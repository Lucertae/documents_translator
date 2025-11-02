#!/usr/bin/env python3
"""
LAC TRANSLATE - PDF Translator GUI Desktop
Traduttori: Google (online) + Argos Translate (offline, privacy totale)
"""
import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
from pathlib import Path
import pymupdf
from deep_translator import GoogleTranslator
import argostranslate.package
import argostranslate.translate
from PIL import Image, ImageTk
import io
import logging
import re
import fitz

# License imports
# Sistema licenze abilitato per produzione
LICENSE_AVAILABLE = True  # Set to True per produzione
try:
    if LICENSE_AVAILABLE:
        from license_manager import get_license_manager
        from license_activation import LicenseActivationDialog
except ImportError:
    LICENSE_AVAILABLE = False
    logging.warning("License system not available")

# Settings imports
try:
    from settings_manager import get_settings_manager
    from settings_dialog import SettingsDialog
    SETTINGS_AVAILABLE = True
except ImportError:
    SETTINGS_AVAILABLE = False
    logging.warning("Settings system not available")

# Batch processing imports
try:
    from batch_dialog import BatchDialog
    BATCH_AVAILABLE = True
except ImportError:
    BATCH_AVAILABLE = False
    logging.warning("Batch processing not available")

# OCR imports - nuovo sistema modulare
try:
    from pdf2image import convert_from_path
    from ocr_manager import get_ocr_manager, OCREngine
    ocr_manager = get_ocr_manager()
    OCR_AVAILABLE = ocr_manager.is_available(OCREngine.TESSERACT) or \
                    ocr_manager.is_available(OCREngine.DOLPHIN) or \
                    ocr_manager.is_available(OCREngine.CHANDRA)
    if OCR_AVAILABLE:
        available_engines = ocr_manager.get_available_engines()
        logging.info(f"OCR disponibile: {', '.join(available_engines)}")
    else:
        logging.warning("Nessun motore OCR disponibile")
except ImportError as e:
    OCR_AVAILABLE = False
    ocr_manager = None
    logging.warning(f"OCR Manager non disponibile: {e}")

# Setup paths
BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "output"
LOGS_DIR = BASE_DIR / "logs"

# Create directories
OUTPUT_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / 'pdf_translator.log'),
        logging.StreamHandler()
    ]
)

# Constants
COLOR_MAP = {
    "Rosso": (0.8, 0, 0),
    "Nero": (0, 0, 0),
    "Blu": (0, 0, 0.8),
    "Verde": (0, 0.5, 0),
    "Viola": (0.5, 0, 0.5),
}

# Argos language codes mapping
ARGOS_LANG_MAP = {
    "Italiano": "it",
    "English": "en",
    "Español": "es",
    "Français": "fr",
    "Deutsch": "de",
    "Português": "pt",
    "Русский": "ru",
}

class ArgosTranslator:
    """Wrapper per Argos Translate"""
    
    def __init__(self, source='auto', target='it'):
        self.source = source if source != 'auto' else 'en'
        self.target = target
        self._check_models()
    
    def _check_models(self):
        """Verifica modelli installati"""
        installed_packages = argostranslate.package.get_installed_packages()
        
        # Trova il translator giusto
        found = False
        for pkg in installed_packages:
            if pkg.from_code == self.source and pkg.to_code == self.target:
                found = True
                logging.info(f"Argos translator loaded: {self.source} -> {self.target}")
                break
        
        if not found:
            logging.warning(f"Argos translator not found for {self.source} -> {self.target}")
            logging.warning("Available packages:")
            for pkg in installed_packages:
                logging.warning(f"  {pkg.from_code} -> {pkg.to_code}")
    
    def translate(self, text):
        """Traduci testo usando API corretta di Argos"""
        if not text or len(text.strip()) < 2:
            return text
        
        try:
            # API corretta: argostranslate.translate.translate(text, from_code, to_code)
            translation = argostranslate.translate.translate(text, self.source, self.target)
            return translation if translation else text
        except Exception as e:
            logging.error(f"Argos translation error: {e}")
            return text


class PDFTranslatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("LAC TRANSLATE - PDF Translator")
        self.root.geometry("1600x900")
        
        # Cache per modello Dolphin (evita ricaricamento)
        self._dolphin_model = None
        
        # Minimal Black & White Theme - Elegant and Professional
        self.colors = {
            'bg': '#ffffff',           # Background principale (bianco puro)
            'bg_dark': '#f8f8f8',      # Background più scuro (grigio molto chiaro)
            'bg_light': '#f5f5f5',     # Background chiaro
            'header': '#000000',       # Header nero
            'accent': '#000000',       # Accent color (nero)
            'accent_hover': '#333333', # Accent hover (grigio scuro)
            'accent_pressed': '#1a1a1a', # Accent pressed
            'text': '#000000',         # Testo principale (nero)
            'text_header': '#ffffff',  # Testo header (bianco)
            'text_dim': '#666666',     # Testo secondario (grigio medio)
            'text_light': '#aaaaaa',   # Testo leggero (grigio chiaro)
            'border': '#e0e0e0',      # Bordi (grigio chiaro)
            'border_hover': '#000000', # Bordo hover (nero)
            'error': '#dc2626',        # Errori (rosso)
            'success': '#16a34a',      # Successo (verde)
            'warning': '#ea580c',      # Warning (arancione)
        }
        
        # Apply dark theme to root
        self.root.configure(bg=self.colors['bg'])
        
        # Configure ttk style
        self.setup_style()
        
        # Variables
        self.pdf_path = None
        self.current_doc = None
        self.current_page = 0
        self.translated_pages = []  # Cache delle pagine tradotte
        
        # Load settings FIRST (before using settings_manager)
        if SETTINGS_AVAILABLE:
            self.settings_manager = get_settings_manager()
            # Load zoom from settings
            self.zoom_level = self.settings_manager.get('zoom_level', 1.25)
            self.translator_type = tk.StringVar(value=self.settings_manager.get('translator_type', 'Google'))
            self.source_lang = tk.StringVar(value=self.settings_manager.get('source_lang', 'English'))
            self.target_lang = tk.StringVar(value=self.settings_manager.get('target_lang', 'Italiano'))
            self.text_color = tk.StringVar(value=self.settings_manager.get('text_color', 'Rosso'))
        else:
            # Defaults (if settings not available)
            self.settings_manager = None
            self.zoom_level = 1.25  # Zoom predefinito 125%
            self.translator_type = tk.StringVar(value="Google")
            self.source_lang = tk.StringVar(value="English")
            self.target_lang = tk.StringVar(value="Italiano")
            self.text_color = tk.StringVar(value="Rosso")
        
        # Setup UI
        self.setup_ui()
        
        # Status
        self.is_translating = False
        self.update_translator_info()
        
        # License check
        if LICENSE_AVAILABLE:
            self.license_manager = get_license_manager()
            self.check_license_on_startup()
        
        # Auto-check updates on startup (optional, non-blocking)
        self.check_updates_on_startup()
        
        logging.info("LAC TRANSLATE started")
    
    def setup_style(self):
        """Setup minimal black & white theme style"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure base colors
        style.configure('.',
            background=self.colors['bg'],
            foreground=self.colors['text'],
            bordercolor=self.colors['border'],
            darkcolor=self.colors['bg_dark'],
            lightcolor=self.colors['bg_light'],
            troughcolor=self.colors['bg_dark'],
            focuscolor=self.colors['accent'],
            selectbackground=self.colors['accent'],
            selectforeground='white',
            fieldbackground=self.colors['bg'],
            font=('-apple-system', 'Segoe UI', 'Roboto', 9)
        )
        
        # Primary Button style (black)
        style.configure('Primary.TButton',
            background=self.colors['accent'],
            foreground='white',
            borderwidth=0,
            focuscolor=self.colors['accent'],
            padding=(12, 8),
            font=('-apple-system', 'Segoe UI', 'Roboto', 9, 'bold'),
            relief='flat',
            cursor='hand2'
        )
        style.map('Primary.TButton',
            background=[('active', self.colors['accent_hover']),
                       ('pressed', self.colors['accent_pressed']),
                       ('disabled', '#cccccc')],
            foreground=[('active', 'white'),
                       ('pressed', 'white'),
                       ('disabled', '#666666')]
        )
        
        # Secondary Button style (white with border)
        style.configure('Secondary.TButton',
            background='white',
            foreground=self.colors['text'],
            borderwidth=1,
            focuscolor=self.colors['accent'],
            padding=(12, 8),
            font=('-apple-system', 'Segoe UI', 'Roboto', 9, 'bold'),
            relief='flat',
            cursor='hand2',
            bordercolor=self.colors['border']
        )
        style.map('Secondary.TButton',
            background=[('active', '#f5f5f5'),
                       ('pressed', '#e8e8e8'),
                       ('disabled', '#f5f5f5')],
            bordercolor=[('active', self.colors['border_hover']),
                        ('pressed', self.colors['border_hover'])],
            foreground=[('disabled', '#cccccc')]
        )
        
        # Default button style (secondary)
        style.configure('TButton',
            background='white',
            foreground=self.colors['text'],
            borderwidth=1,
            focuscolor=self.colors['accent'],
            padding=(10, 6),
            font=('-apple-system', 'Segoe UI', 'Roboto', 9),
            relief='flat',
            cursor='hand2',
            bordercolor=self.colors['border']
        )
        style.map('TButton',
            background=[('active', '#f5f5f5'),
                       ('pressed', '#e8e8e8'),
                       ('disabled', '#f5f5f5')],
            bordercolor=[('active', self.colors['border_hover']),
                        ('pressed', self.colors['border_hover'])],
            foreground=[('disabled', '#cccccc')]
        )
        
        # Label style
        style.configure('TLabel',
            background=self.colors['bg'],
            foreground=self.colors['text'],
            font=('Segoe UI', 9)
        )
        
        # Frame style
        style.configure('TFrame',
            background=self.colors['bg'],
            borderwidth=0
        )
        
        # LabelFrame style
        style.configure('TLabelframe',
            background=self.colors['bg'],
            foreground=self.colors['text'],
            bordercolor=self.colors['border'],
            borderwidth=1,
            relief='flat',
            font=('-apple-system', 'Segoe UI', 'Roboto', 10, 'bold')
        )
        style.configure('TLabelframe.Label',
            background=self.colors['bg'],
            foreground=self.colors['text'],
            font=('-apple-system', 'Segoe UI', 'Roboto', 10, 'bold')
        )
        
        # Combobox style
        style.configure('TCombobox',
            fieldbackground=self.colors['bg_light'],
            background=self.colors['bg_light'],
            foreground=self.colors['text'],
            arrowcolor=self.colors['accent'],
            bordercolor=self.colors['border'],
            lightcolor=self.colors['bg_light'],
            darkcolor=self.colors['bg_light'],
            selectbackground=self.colors['accent'],
            selectforeground=self.colors['bg']
        )
        
        # Radiobutton style
        style.configure('TRadiobutton',
            background=self.colors['bg'],
            foreground=self.colors['text'],
            indicatorcolor=self.colors['accent'],
            font=('Segoe UI', 9)
        )
        style.map('TRadiobutton',
            background=[('active', self.colors['bg'])],
            foreground=[('active', self.colors['accent'])]
        )
        
        # Progressbar style
        style.configure('TProgressbar',
            background=self.colors['accent'],
            troughcolor=self.colors['bg_dark'],
            borderwidth=0,
            thickness=3
        )
        
        # Non creare stile custom per progressbar - usa TProgressbar direttamente
        # Le modifiche di stile verranno applicate a TProgressbar stesso
        
        # Scrollbar style
        style.configure('TScrollbar',
            background=self.colors['bg_light'],
            troughcolor=self.colors['bg_dark'],
            bordercolor=self.colors['bg'],
            arrowcolor=self.colors['text'],
            borderwidth=0
        )
        
        # Scrollbar CENTRALE - Cursore nero su sfondo chiaro
        style.configure('Central.Vertical.TScrollbar',
            background='#000000',           # Cursore NERO (ben visibile)
            troughcolor='#E0E0E0',          # Sfondo CHIARO (per vedere posizione)
            bordercolor='#CCCCCC',
            arrowcolor='#000000',           # Frecce nere
            darkcolor='#000000',
            lightcolor='#000000',
            borderwidth=1,
            arrowsize=14
        )
        style.map('Central.Vertical.TScrollbar',
            background=[('active', '#333333'), ('!active', '#000000')],  # Cursore nero/grigio
            arrowcolor=[('active', '#333333'), ('!active', '#000000')]
        )
    
    def setup_ui(self):
        """Setup interfaccia utente"""
        
        # === MENU BAR ===
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Apri PDF...", command=self.select_pdf, accelerator="Ctrl+O")
        
        # Recent files submenu
        self.recent_files_menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="File Recenti", menu=self.recent_files_menu)
        file_menu.add_separator()
        
        file_menu.add_command(label="Salva PDF tradotto...", command=self.save_pdf, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Esci", command=self.root.quit, accelerator="Alt+F4")
        
        # Update recent files menu
        self.update_recent_files_menu()
        
        # Modifica menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Modifica", menu=edit_menu)
        edit_menu.add_command(label="Impostazioni...", command=self.show_settings_dialog)
        edit_menu.add_separator()
        edit_menu.add_command(label="Batch Processing...", command=self.show_batch_dialog)
        
        # Visualizza menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Visualizza", menu=view_menu)
        view_menu.add_command(label="Zoom In", command=self.zoom_in, accelerator="Ctrl++")
        view_menu.add_command(label="Zoom Out", command=self.zoom_out, accelerator="Ctrl+-")
        view_menu.add_command(label="Adatta alla finestra", command=self.zoom_fit, accelerator="Ctrl+0")
        
        # Aiuto menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Aiuto", menu=help_menu)
        if LICENSE_AVAILABLE:
            help_menu.add_command(label="Informazioni Licenza", command=self.show_license_info)
            help_menu.add_command(label="Attiva Licenza...", command=self.activate_license_dialog)
            help_menu.add_separator()
        help_menu.add_command(label="Verifica Aggiornamenti...", command=self.check_updates)
        help_menu.add_separator()
        help_menu.add_command(label="Informazioni su LAC TRANSLATE", command=self.show_about)
        help_menu.add_command(label="Guida", command=self.show_help)
        
        # Keyboard shortcuts
        self.root.bind('<Control-o>', lambda e: self.select_pdf())
        self.root.bind('<Control-s>', lambda e: self.save_pdf())
        self.root.bind('<Control-plus>', lambda e: self.zoom_in())
        self.root.bind('<Control-equal>', lambda e: self.zoom_in())
        self.root.bind('<Control-minus>', lambda e: self.zoom_out())
        self.root.bind('<Control-0>', lambda e: self.zoom_fit())
        self.root.bind('<F5>', lambda e: self.translate_current_page())
        self.root.bind('<F6>', lambda e: self.translate_all_pages())
        
        # === HEADER (Black Minimal Design) ===
        header_frame = tk.Frame(self.root, bg=self.colors['header'], height=60)
        header_frame.pack(side=tk.TOP, fill=tk.X)
        header_frame.pack_propagate(False)
        
        header_content = tk.Frame(header_frame, bg=self.colors['header'])
        header_content.pack(fill=tk.BOTH, expand=True, padx=20)
        
        # Logo/Titolo
        title_label = tk.Label(
            header_content,
            text="LAC TRANSLATE",
            bg=self.colors['header'],
            fg=self.colors['text_header'],
            font=('-apple-system', 'Segoe UI', 'Roboto', 20, 'bold'),
            anchor='w'
        )
        title_label.pack(side=tk.LEFT)
        
        # Sottotitolo
        subtitle_label = tk.Label(
            header_content,
            text="Traduttore PDF Professionale",
            bg=self.colors['header'],
            fg=self.colors['text_light'],
            font=('-apple-system', 'Segoe UI', 'Roboto', 12),
            anchor='e'
        )
        subtitle_label.pack(side=tk.RIGHT)
        
        # === TOP TOOLBAR (White Minimal Design) ===
        toolbar = tk.Frame(self.root, bg='white', height=70)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        toolbar.pack_propagate(False)
        
        toolbar_content = tk.Frame(toolbar, bg='white')
        toolbar_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # File selection
        open_btn = ttk.Button(toolbar_content, text="Apri PDF", command=self.select_pdf, 
                              style='Primary.TButton', width=12)
        open_btn.pack(side=tk.LEFT, padx=(0, 2))
        self.create_tooltip(open_btn, "Apri un file PDF da tradurre\nShortcut: Ctrl+O")
        
        self.file_label = tk.Label(toolbar_content, text="Nessun file caricato", 
                                   bg='white', fg=self.colors['text_dim'], 
                                   font=('-apple-system', 'Segoe UI', 'Roboto', 9), width=35)
        self.file_label.pack(side=tk.LEFT, padx=10)
        
        self.create_separator(toolbar_content).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # Page navigation
        prev_btn = ttk.Button(toolbar_content, text="◀ Precedente", command=self.prev_page, 
                             style='Secondary.TButton', width=12)
        prev_btn.pack(side=tk.LEFT, padx=2)
        
        self.page_label = tk.Label(toolbar_content, text="Pagina: 0/0", 
                                   bg='white', fg=self.colors['text'],
                                   font=('-apple-system', 'Segoe UI', 'Roboto', 9), width=15)
        self.page_label.pack(side=tk.LEFT, padx=5)
        
        next_btn = ttk.Button(toolbar_content, text="Successivo ▶", command=self.next_page, 
                             style='Secondary.TButton', width=12)
        next_btn.pack(side=tk.LEFT, padx=2)
        
        self.create_separator(toolbar_content).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # Zoom controls
        zoom_out_btn = ttk.Button(toolbar_content, text="🔍−", command=self.zoom_out, 
                                 style='Secondary.TButton', width=5)
        zoom_out_btn.pack(side=tk.LEFT, padx=2)
        
        self.zoom_label = tk.Label(toolbar_content, text="125%", 
                                   bg='white', fg=self.colors['text'],
                                   font=('-apple-system', 'Segoe UI', 'Roboto', 9), width=8)
        self.zoom_label.pack(side=tk.LEFT, padx=5)
        
        zoom_in_btn = ttk.Button(toolbar_content, text="🔍+", command=self.zoom_in, 
                                style='Secondary.TButton', width=5)
        zoom_in_btn.pack(side=tk.LEFT, padx=2)
        
        fit_btn = ttk.Button(toolbar_content, text="Adatta", command=self.zoom_fit, 
                            style='Secondary.TButton', width=8)
        fit_btn.pack(side=tk.LEFT, padx=2)
        
        self.create_separator(toolbar_content).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # Translation buttons
        translate_page_btn = ttk.Button(toolbar_content, text="Traduci Pagina", 
                                        command=self.translate_current_page, 
                                        style='Secondary.TButton', width=15)
        translate_page_btn.pack(side=tk.LEFT, padx=2)
        self.create_tooltip(translate_page_btn, "Traduci la pagina corrente\nShortcut: F5")
        
        translate_all_btn = ttk.Button(toolbar_content, text="Traduci Tutto", 
                                      command=self.translate_all_pages, 
                                      style='Secondary.TButton', width=15)
        translate_all_btn.pack(side=tk.LEFT, padx=2)
        self.create_tooltip(translate_all_btn, "Traduci tutte le pagine del PDF\nShortcut: F6")
        
        self.create_separator(toolbar_content).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # Save button
        save_btn = ttk.Button(toolbar_content, text="Salva PDF", command=self.save_pdf, 
                             style='Primary.TButton', width=12)
        save_btn.pack(side=tk.LEFT, padx=2)
        self.create_tooltip(save_btn, "Salva il PDF tradotto\nShortcut: Ctrl+S")
        
        tk.Frame(toolbar_content, bg='white', width=1).pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # === SETTINGS PANEL (Minimal Design) ===
        settings_frame = tk.Frame(self.root, bg=self.colors['bg_dark'], height=80)
        settings_frame.pack(side=tk.TOP, fill=tk.X)
        settings_frame.pack_propagate(False)
        
        settings_content = tk.Frame(settings_frame, bg=self.colors['bg_dark'])
        settings_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Row 1: Translator type
        row1 = tk.Frame(settings_content, bg=self.colors['bg_dark'])
        row1.pack(fill=tk.X, pady=(0, 5))
        
        tk.Label(row1, text="Traduttore:", bg=self.colors['bg_dark'], 
                fg=self.colors['text'], font=('-apple-system', 'Segoe UI', 'Roboto', 9, 'bold')).pack(side=tk.LEFT, padx=5)
        
        ttk.Radiobutton(row1, text="Google Translate (online)", 
                       variable=self.translator_type, value="Google",
                       command=self.update_translator_info).pack(side=tk.LEFT, padx=10)
        
        ttk.Radiobutton(row1, text="Argos Translate (offline - privacy totale)", 
                       variable=self.translator_type, value="Argos",
                       command=self.update_translator_info).pack(side=tk.LEFT, padx=10)
        
        self.translator_info = tk.Label(row1, text="", bg=self.colors['bg_dark'], 
                                       fg=self.colors['text_dim'],
                                       font=('-apple-system', 'Segoe UI', 'Roboto', 9))
        self.translator_info.pack(side=tk.LEFT, padx=20)
        
        self.create_separator(row1).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # Row 2: Languages and Color
        row2 = tk.Frame(settings_content, bg=self.colors['bg_dark'])
        row2.pack(fill=tk.X)
        
        tk.Label(row2, text="Da:", bg=self.colors['bg_dark'], 
                fg=self.colors['text'], font=('-apple-system', 'Segoe UI', 'Roboto', 9, 'bold')).pack(side=tk.LEFT, padx=5)
        
        source_combo = ttk.Combobox(row2, textvariable=self.source_lang, 
                                    values=["Auto"] + list(ARGOS_LANG_MAP.keys()),
                                    state="readonly", width=12)
        source_combo.pack(side=tk.LEFT, padx=5)
        
        tk.Label(row2, text="→", bg=self.colors['bg_dark'], 
                fg=self.colors['text'], font=('-apple-system', 'Segoe UI', 'Roboto', 16, 'bold')).pack(side=tk.LEFT, padx=5)
        
        tk.Label(row2, text="A:", bg=self.colors['bg_dark'], 
                fg=self.colors['text'], font=('-apple-system', 'Segoe UI', 'Roboto', 9, 'bold')).pack(side=tk.LEFT, padx=5)
        
        target_combo = ttk.Combobox(row2, textvariable=self.target_lang, 
                                    values=list(ARGOS_LANG_MAP.keys()),
                                    state="readonly", width=12)
        target_combo.pack(side=tk.LEFT, padx=5)
        
        self.create_separator(row2).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        tk.Label(row2, text="Colore:", bg=self.colors['bg_dark'], 
                fg=self.colors['text'], font=('-apple-system', 'Segoe UI', 'Roboto', 9, 'bold')).pack(side=tk.LEFT, padx=5)
        
        color_combo = ttk.Combobox(row2, textvariable=self.text_color, 
                                   values=list(COLOR_MAP.keys()),
                                   state="readonly", width=10)
        color_combo.pack(side=tk.LEFT, padx=5)
        
        # === MAIN CONTENT - Side by side view con scrollbar centrale ===
        content_frame = tk.Frame(self.root, bg=self.colors['bg'])
        content_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Original PDF (left)
        left_frame = tk.Frame(content_frame, bg=self.colors['bg'])
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 2))
        
        # Title for original
        original_title = tk.Label(left_frame, text="Originale", 
                                  bg=self.colors['bg'], fg=self.colors['text'],
                                  font=('-apple-system', 'Segoe UI', 'Roboto', 16, 'bold'),
                                  anchor='w', padx=5, pady=5)
        original_title.pack(side=tk.TOP, fill=tk.X)
        
        # Canvas SENZA scrollbar verticale (solo orizzontale)
        self.original_canvas = tk.Canvas(
            left_frame, 
            bg=self.colors['bg'], 
            highlightthickness=0,
            bd=0
        )
        left_hscroll = ttk.Scrollbar(left_frame, orient="horizontal", command=self.original_canvas.xview)
        self.original_canvas.configure(xscrollcommand=left_hscroll.set)
        
        # Layout: solo scrollbar orizzontale
        left_hscroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.original_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # SCROLLBAR VERTICALE CENTRALE - Cursore nero su sfondo chiaro
        central_vscroll_frame = tk.Frame(content_frame, bg='#E0E0E0', width=18, relief=tk.SUNKEN, bd=1)
        central_vscroll_frame.pack(side=tk.LEFT, fill=tk.Y, padx=4)
        central_vscroll_frame.pack_propagate(False)
        
        central_vscroll = ttk.Scrollbar(central_vscroll_frame, orient="vertical", command=self.sync_scroll, style='Central.Vertical.TScrollbar')
        central_vscroll.pack(fill=tk.BOTH, expand=True)
        self.central_vscroll = central_vscroll
        
        # Configura canvas per usare scrollbar centrale
        self.original_canvas.configure(yscrollcommand=self.update_central_scrollbar)
        
        # Mouse wheel scrolling sincronizzato
        self.original_canvas.bind('<MouseWheel>', lambda e: self.sync_mousewheel(e))
        
        # Translated PDF (right)
        right_frame = tk.Frame(content_frame, bg=self.colors['bg'])
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(2, 0))
        
        # Title for translated
        translated_title = tk.Label(right_frame, text="Tradotto", 
                                    bg=self.colors['bg'], fg=self.colors['text'],
                                    font=('-apple-system', 'Segoe UI', 'Roboto', 16, 'bold'),
                                    anchor='w', padx=5, pady=5)
        translated_title.pack(side=tk.TOP, fill=tk.X)
        
        # Canvas SENZA scrollbar verticale (solo orizzontale)
        self.translated_canvas = tk.Canvas(
            right_frame, 
            bg=self.colors['bg'], 
            highlightthickness=0,
            bd=0
        )
        right_hscroll = ttk.Scrollbar(right_frame, orient="horizontal", command=self.translated_canvas.xview)
        self.translated_canvas.configure(xscrollcommand=right_hscroll.set)
        
        # Layout: solo scrollbar orizzontale
        right_hscroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.translated_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configura anche questo canvas per scrollbar centrale
        self.translated_canvas.configure(yscrollcommand=lambda *args: None)  # Ignora, usa quella centrale
        
        # Mouse wheel scrolling sincronizzato
        self.translated_canvas.bind('<MouseWheel>', lambda e: self.sync_mousewheel(e))
        
        # === STATUS BAR (Minimal Design) ===
        status_frame = tk.Frame(self.root, bg=self.colors['bg_dark'], height=30)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        status_frame.pack_propagate(False)
        
        status_content = tk.Frame(status_frame, bg=self.colors['bg_dark'])
        status_content.pack(fill=tk.BOTH, expand=True, padx=20)
        
        self.status_bar = tk.Label(
            status_content, 
            text="Pronto - LAC TRANSLATE", 
            anchor='w',
            bg=self.colors['bg_dark'],
            fg=self.colors['text_dim'],
            font=('-apple-system', 'Segoe UI', 'Roboto', 9),
            padx=0
        )
        self.status_bar.pack(side=tk.LEFT)
        
        # Progress bar (hidden by default) - usa stile standard TProgressbar
        self.progress = ttk.Progressbar(status_content, mode='indeterminate', 
                                       length=200)
        self.progress.pack(side=tk.RIGHT, padx=10)
        self.progress.pack_forget()  # Hidden initially
    
    def update_translator_info(self):
        """Aggiorna info traduttore"""
        if self.translator_type.get() == "Google":
            self.translator_info.config(
                text="[Online - richiede connessione internet]",
                foreground=self.colors['warning']
            )
        else:
            self.translator_info.config(
                text="[Offline - tutto sul tuo PC, privacy totale]",
                foreground=self.colors['success']
            )
    
    def select_pdf(self):
        """Seleziona file PDF"""
        filename = filedialog.askopenfilename(
            title="Seleziona file PDF",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if filename:
            self.pdf_path = filename
            self.file_label.config(text=os.path.basename(filename))
            
            # Add to recent files
            if SETTINGS_AVAILABLE:
                self.settings_manager.add_recent_file(filename)
                self.update_recent_files_menu()
            
            self.load_pdf()
    
    def load_pdf(self):
        """Carica PDF"""
        try:
            self.current_doc = pymupdf.open(self.pdf_path)
            self.current_page = 0
            self.translated_pages = [None] * self.current_doc.page_count
            
            # Check if PDF is scanned
            first_page = self.current_doc[0]
            sample_text = self.extract_text_improved(first_page)
            
            if sample_text.startswith("[PDF scansionato"):
                self.update_status(f"⚠ PDF scansionato rilevato: {self.current_doc.page_count} pagine - traduzione limitata")
                messagebox.showinfo(
                    "PDF Scansionato Rilevato", 
                    "Questo PDF sembra essere scansionato.\n\n"
                    "La traduzione sarà limitata e potrebbe non funzionare perfettamente.\n"
                    "Per risultati migliori, prova con un PDF con testo selezionabile.\n\n"
                    "Suggerimento: Installa Tesseract OCR per migliori risultati con PDF scansionati."
                )
            else:
                # Controlla se il testo è sufficiente per una buona traduzione
                text_length = len(sample_text.strip())
                if text_length > 100:
                    self.update_status(f"✓ PDF caricato: {self.current_doc.page_count} pagine - {text_length} caratteri estratti")
                else:
                    self.update_status(f"⚠ PDF caricato: {self.current_doc.page_count} pagine - testo limitato ({text_length} caratteri)")
            
            self.display_current_page()
            logging.info(f"Loaded PDF: {self.pdf_path} ({self.current_doc.page_count} pages)")
        except FileNotFoundError:
            error_msg = f"File non trovato:\n{self.pdf_path}\n\nIl file potrebbe essere stato spostato o eliminato."
            messagebox.showerror("Errore - File Non Trovato", error_msg)
            logging.error(f"PDF file not found: {self.pdf_path}")
            # Reset
            self.pdf_path = None
            self.current_doc = None
            self.file_label.config(text="Nessun file caricato")
        except pymupdf.FileDataError as e:
            error_msg = (
                f"Errore nel file PDF:\n{str(e)}\n\n"
                "Il file potrebbe essere corrotto o non essere un PDF valido.\n"
                "Prova ad aprire il file con un altro visualizzatore PDF per verificare."
            )
            messagebox.showerror("Errore - PDF Corrotto", error_msg)
            logging.error(f"Invalid PDF file: {str(e)}")
        except PermissionError:
            error_msg = (
                f"Impossibile aprire il file:\n{self.pdf_path}\n\n"
                "Il file potrebbe essere aperto in un'altra applicazione.\n"
                "Chiudi tutte le applicazioni che stanno usando questo file e riprova."
            )
            messagebox.showerror("Errore - Permessi", error_msg)
            logging.error(f"Permission denied: {self.pdf_path}")
        except Exception as e:
            error_msg = (
                f"Errore imprevisto durante il caricamento:\n{str(e)}\n\n"
                "Se il problema persiste:\n"
                "1. Verifica che il file sia un PDF valido\n"
                "2. Controlla che ci sia spazio disco disponibile\n"
                "3. Contatta il supporto tecnico con il messaggio di errore"
            )
            messagebox.showerror("Errore - Caricamento PDF", error_msg)
            logging.error(f"Failed to load PDF: {str(e)}", exc_info=True)
    
    def display_current_page(self):
        """Mostra pagina corrente con zoom configurabile"""
        if not self.current_doc:
            return
        
        page_num = self.current_page
        self.page_label.config(text=f"Pag: {page_num + 1}/{self.current_doc.page_count}")
        self.zoom_label.config(text=f"{int(self.zoom_level * 100)}%")
        
        # Display original
        page = self.current_doc[page_num]
        
        # Usa lo zoom level configurabile
        scale = self.zoom_level
        
        # Render with zoom scale
        pix = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale))
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        photo = ImageTk.PhotoImage(img)
        
        # Clear canvas
        self.original_canvas.delete("all")
        
        # Get canvas size
        self.original_canvas.update_idletasks()
        canvas_width = self.original_canvas.winfo_width()
        
        # Center image
        x_center = max(canvas_width // 2, pix.width // 2)
        y_center = 0  # Top aligned
        
        # Create image centered horizontally
        self.original_canvas.create_image(x_center, y_center, anchor=tk.N, image=photo)
        self.original_canvas.image = photo
        
        # Configure scroll region - sempre permetti scroll
        scroll_width = max(pix.width + 40, canvas_width)
        scroll_height = pix.height + 40
        self.original_canvas.config(scrollregion=(0, 0, scroll_width, scroll_height))
        
        # Scroll to top
        self.original_canvas.yview_moveto(0)
        
        # Display translated if exists
        if self.translated_pages[page_num]:
            self.display_translated_page(self.translated_pages[page_num])
        else:
            self.translated_canvas.delete("all")
            # Add placeholder text
            canvas_width = self.translated_canvas.winfo_width()
            canvas_height = self.translated_canvas.winfo_height()
            self.translated_canvas.create_text(
                canvas_width // 2, 
                canvas_height // 2,
                text="Nessuna traduzione\nClicca 'Traduci Pagina' per iniziare",
                fill=self.colors['text_dim'],
                font=('Segoe UI', 12),
                justify=tk.CENTER
            )
    
    def display_translated_page(self, translated_doc):
        """Mostra pagina tradotta con zoom configurabile"""
        try:
            page = translated_doc[0]
            
            # Usa lo stesso zoom level della pagina originale
            scale = self.zoom_level
            
            # Render with zoom scale
            pix = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale))
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            photo = ImageTk.PhotoImage(img)
            
            # Clear canvas
            self.translated_canvas.delete("all")
            
            # Get canvas size
            self.translated_canvas.update_idletasks()
            canvas_width = self.translated_canvas.winfo_width()
            
            # Center image
            x_center = max(canvas_width // 2, pix.width // 2)
            y_center = 0  # Top aligned
            
            # Create image centered horizontally
            self.translated_canvas.create_image(x_center, y_center, anchor=tk.N, image=photo)
            self.translated_canvas.image = photo
            
            # Configure scroll region - sempre permetti scroll
            scroll_width = max(pix.width + 40, canvas_width)
            scroll_height = pix.height + 40
            self.translated_canvas.config(scrollregion=(0, 0, scroll_width, scroll_height))
            
            # Scroll to top
            self.translated_canvas.yview_moveto(0)
            
        except Exception as e:
            logging.error(f"Error displaying translated page: {e}")
    
    def prev_page(self):
        """Pagina precedente"""
        if self.current_doc and self.current_page > 0:
            self.current_page -= 1
            self.display_current_page()
    
    def next_page(self):
        """Pagina successiva"""
        if self.current_doc and self.current_page < self.current_doc.page_count - 1:
            self.current_page += 1
            self.display_current_page()
    
    def zoom_in(self):
        """Aumenta zoom"""
        if self.zoom_level < 5.0:  # Max 500%
            self.zoom_level += 0.25
            if SETTINGS_AVAILABLE:
                self.settings_manager.set('zoom_level', self.zoom_level)
            self.display_current_page()
            logging.info(f"Zoom aumentato a {int(self.zoom_level * 100)}%")
    
    def zoom_out(self):
        """Diminuisci zoom"""
        if self.zoom_level > 0.5:  # Min 50%
            self.zoom_level -= 0.25
            if SETTINGS_AVAILABLE:
                self.settings_manager.set('zoom_level', self.zoom_level)
            self.display_current_page()
            logging.info(f"Zoom diminuito a {int(self.zoom_level * 100)}%")
    
    def zoom_fit(self):
        """Adatta zoom alla finestra"""
        if not self.current_doc:
            return
        
        page = self.current_doc[self.current_page]
        page_rect = page.rect
        
        # Get canvas size
        self.original_canvas.update_idletasks()
        canvas_width = self.original_canvas.winfo_width()
        canvas_height = self.original_canvas.winfo_height()
        
        # Calculate scale to fit
        scale_x = (canvas_width - 40) / page_rect.width
        scale_y = (canvas_height - 40) / page_rect.height
        self.zoom_level = min(scale_x, scale_y, 3.0)  # Max 300% per fit
        
        if SETTINGS_AVAILABLE:
            self.settings_manager.set('zoom_level', self.zoom_level)
        
        self.display_current_page()
        logging.info(f"Zoom adattato a {int(self.zoom_level * 100)}%")
    
    def sync_scroll(self, *args):
        """Sincronizza scroll verticale tra entrambi i canvas"""
        # Muovi entrambi i canvas insieme
        self.original_canvas.yview(*args)
        self.translated_canvas.yview(*args)
    
    def update_central_scrollbar(self, first, last):
        """Aggiorna la scrollbar centrale quando i canvas cambiano"""
        # Aggiorna la scrollbar centrale
        self.central_vscroll.set(first, last)
        # Sincronizza anche il canvas tradotto
        self.translated_canvas.yview_moveto(float(first))
    
    def sync_mousewheel(self, event):
        """Sincronizza scroll con rotellina mouse su entrambi i canvas"""
        # Calcola scroll
        scroll_amount = int(-1 * (event.delta / 120))
        # Applica a entrambi i canvas
        self.original_canvas.yview_scroll(scroll_amount, "units")
        self.translated_canvas.yview_scroll(scroll_amount, "units")
    
    def get_translator(self):
        """Ottieni traduttore"""
        source = "auto" if self.source_lang.get() == "Auto" else ARGOS_LANG_MAP.get(self.source_lang.get(), 'en')
        target = ARGOS_LANG_MAP.get(self.target_lang.get(), 'it')
        
        if self.translator_type.get() == "Google":
            return GoogleTranslator(source=source, target=target)
        else:
            return ArgosTranslator(source=source, target=target)
    
    def extract_text_improved(self, page):
        """Estrai testo con metodi migliorati per PDF di alta qualità"""
        # Metodo 1: Estrazione normale
        text = page.get_text("text")
        if text and len(text.strip()) > 20:  # Ridotto da 50 a 20
            return text
        
        # Metodo 2: Estrazione con flags diversi
        text = page.get_text("text", flags=pymupdf.TEXT_PRESERVE_WHITESPACE)
        if text and len(text.strip()) > 20:
            return text
        
        # Metodo 3: Estrazione con flags più aggressivi
        text = page.get_text("text", flags=pymupdf.TEXT_DEHYPHENATE | pymupdf.TEXT_PRESERVE_WHITESPACE)
        if text and len(text.strip()) > 20:
            return text
        
        # Metodo 4: Estrazione da blocchi con filtri migliorati
        blocks = page.get_text("blocks", flags=pymupdf.TEXT_DEHYPHENATE)
        full_text = ""
        for block in blocks:
            if len(block) > 4:
                text_part = block[4]
                if text_part and text_part.strip() and len(text_part.strip()) > 2:
                    full_text += text_part + " "
        
        if full_text and len(full_text.strip()) > 20:
            return full_text.strip()
        
        # Metodo 5: Estrazione con dizionario dettagliato
        text_dict = page.get_text("dict")
        full_text = ""
        for block in text_dict["blocks"]:
            if "lines" in block:
                for line in block["lines"]:
                    if "spans" in line:
                        for span in line["spans"]:
                            if "text" in span and span["text"].strip():
                                full_text += span["text"] + " "
        
        if full_text and len(full_text.strip()) > 20:
            return full_text.strip()
        
        # Metodo 6: Estrazione con parole singole
        words = page.get_text("words")
        if words and len(words) > 10:
            word_text = " ".join([word[4] for word in words if word[4].strip()])
            if len(word_text.strip()) > 20:
                return word_text.strip()
        
        # Metodo 7: Estrazione con HTML
        html_text = page.get_text("html")
        if html_text and len(html_text.strip()) > 50:
            # Estrai solo il testo dall'HTML
            clean_text = re.sub(r'<[^>]+>', ' ', html_text)
            clean_text = re.sub(r'\s+', ' ', clean_text).strip()
            if len(clean_text) > 20:
                return clean_text
        
        # Metodo 8: OCR con sistema modulare - PRIORITÀ per tabelle/scannerizzati
        # Per tabelle e documenti scannerizzati: usa prima Dolphin/Chandra (migliori per layout complessi)
        if OCR_AVAILABLE and ocr_manager:
            try:
                logging.info("Attempting OCR extraction with available engines (priorità Dolphin/Chandra per tabelle)...")
                # Render page as image con alta risoluzione per migliore accuratezza
                pix = page.get_pixmap(matrix=pymupdf.Matrix(3.0, 3.0))  # 3x resolution per tabelle/documenti scannerizzati
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                
                # Strategia intelligente: prova prima Dolphin/Chandra per tabelle e layout complessi
                # Dolphin e Chandra sono migliori per documenti scannerizzati e tabelle
                engines_to_try = []
                
                # Se disponibili, prova prima Dolphin e Chandra (migliori per tabelle)
                if ocr_manager.is_available(OCREngine.DOLPHIN):
                    engines_to_try.append(OCREngine.DOLPHIN)
                if ocr_manager.is_available(OCREngine.CHANDRA):
                    engines_to_try.append(OCREngine.CHANDRA)
                # Poi Tesseract come fallback
                if ocr_manager.is_available(OCREngine.TESSERACT):
                    engines_to_try.append(OCREngine.TESSERACT)
                
                # Prova ogni motore in ordine
                for engine in engines_to_try:
                    try:
                        ocr_text = ocr_manager.extract_text(img, engine=engine, lang='eng')
                        if ocr_text and len(ocr_text.strip()) > 20:
                            logging.info(f"OCR successful con {engine.value}: extracted {len(ocr_text)} characters")
                            return ocr_text.strip()
                    except Exception as e:
                        logging.debug(f"OCR {engine.value} failed, provo prossimo: {e}")
                        continue
                
                # Se nessuno funziona, prova AUTO come ultimo tentativo
                ocr_text = ocr_manager.extract_text(img, engine=OCREngine.AUTO, lang='eng')
                if ocr_text and len(ocr_text.strip()) > 20:
                    logging.info(f"OCR successful (AUTO): extracted {len(ocr_text)} characters")
                    return ocr_text.strip()
            except Exception as e:
                logging.warning(f"OCR failed: {str(e)}")
        
        # Se tutto fallisce
        logging.warning("No text found with any extraction method")
        return "[PDF scansionato - testo non estraibile automaticamente]"
    
    def translate_page(self, page_num):
        """Traduci una pagina con supporto ibrido ROBUSTO per PDF normali e scansionati"""
        WHITE = pymupdf.pdfcolor["white"]
        rgb_color = COLOR_MAP.get(self.text_color.get(), COLOR_MAP["Rosso"])
        translator = self.get_translator()

        new_doc = pymupdf.open()
        new_doc.insert_pdf(self.current_doc, from_page=page_num, to_page=page_num)
        page = new_doc[0]

        # Analizza blocchi per approccio ibrido SEMPLICE E ROBUSTO
        blocks = page.get_text("blocks", flags=pymupdf.TEXT_DEHYPHENATE)
        translated_count = 0
        ocr_blocks = 0
        normal_blocks = 0

        logging.info(f"Analyzing {len(blocks)} blocks for hybrid translation")

        # Analizza e traduci ogni blocco con metodo ottimale
        for i, block in enumerate(blocks):
            bbox = block[:4]
            text = block[4]

            if not text or len(text.strip()) < 3:
                continue

            # PRIMA: Controlla se è una tabella (anche con testo normale)
            is_table = self.detect_table(text)
            
            if is_table:
                # TABELLA RILEVATA - usa OCR avanzato (Dolphin/Chandra) per struttura migliore
                try:
                    logging.info(f"Block {i+1}: Tabella rilevata, estrazione con OCR avanzato (Dolphin/Chandra)...")
                    
                    # PROVA PRIMA: Estrazione struttura con Dolphin/Chandra
                    table_structure = self.extract_table_with_advanced_ocr(page, bbox)
                    
                    # FALLBACK: Se OCR avanzato fallisce, prova parsing da testo estratto
                    if not table_structure or table_structure.get('num_rows', 0) < 2:
                        logging.info(f"Block {i+1}: OCR avanzato non ha estratto struttura valida, provo parsing testo...")
                        table_structure = self.parse_table_structure(text)
                    
                    if table_structure and table_structure['num_rows'] >= 2:
                        # Traduci tabella mantenendo struttura
                        translated_table = self.translate_table(table_structure, translator)
                        
                        if translated_table and translated_table.get('rows'):
                            # Pulisci area tabella
                            page.draw_rect(bbox, color=None, fill=WHITE)
                            
                            # PROVA PRIMA: Inserimento diretto (preserva meglio struttura)
                            success = self.insert_table_direct(page, bbox, translated_table, rgb_color)
                            
                            if not success:
                                # FALLBACK: HTML se inserimento diretto fallisce
                                logging.warning(f"Block {i+1}: Inserimento diretto fallito, uso HTML fallback")
                                table_html = self.format_table_html(translated_table, rgb_color)
                                page.insert_htmlbox(
                                    bbox,
                                    table_html,
                                    css=f"""* {{
                                        font-family: 'Arial', sans-serif;
                                        font-size: 8pt;
                                        color: rgb({int(rgb_color[0]*255)}, {int(rgb_color[1]*255)}, {int(rgb_color[2]*255)});
                                    }}
                                    """
                                )
                            
                            translated_count += 1
                            logging.info(f"Block {i+1}: Tabella tradotta e formattata ({table_structure['num_rows']} righe x {table_structure['num_cols']} colonne)")
                        else:
                            logging.warning(f"Block {i+1}: Traduzione tabella fallita, fallback a metodo normale")
                            is_table = False  # Fallback a metodo normale
                    else:
                        logging.warning(f"Block {i+1}: Struttura tabella non valida, fallback a metodo normale")
                        is_table = False  # Fallback a metodo normale
                except Exception as e:
                    logging.warning(f"Errore traduzione tabella block {i+1}: {str(e)}, fallback a metodo normale")
                    is_table = False  # Fallback a metodo normale
            
            # Gestione normale (testo o fallback da tabella)
            if not is_table:
                # Analizza la qualità del testo
                text_quality = self.analyze_text_quality(text)

                if text_quality['is_good']:
                    # Blocco normale - traduci direttamente preservando layout
                    try:
                        translated = translator.translate(text.strip())
                        if translated and translated.strip():
                            page.draw_rect(bbox, color=None, fill=WHITE)
                            page.insert_htmlbox(
                                bbox,
                                translated,
                                css=f"""* {{
                                    font-family: 'Arial', sans-serif;
                                    font-size: 10pt;
                                    color: rgb({int(rgb_color[0]*255)}, {int(rgb_color[1]*255)}, {int(rgb_color[2]*255)});
                                    line-height: 1.4;
                                    text-align: left;
                                }}"""
                            )
                            translated_count += 1
                            normal_blocks += 1
                            logging.debug(f"Block {i+1}: Normal translation ({len(text)} chars)")
                    except Exception as e:
                        logging.warning(f"Normal translation failed for block {i+1}: {str(e)}")
                else:
                    # Blocco di scarsa qualità - usa OCR avanzato (Dolphin/Chandra preferiti)
                    try:
                        logging.debug(f"Block {i+1}: Poor quality text, trying OCR avanzato (Dolphin/Chandra)")
                        ocr_text = self.extract_text_from_bbox(page, bbox, prefer_advanced=True)

                        if ocr_text and len(ocr_text.strip()) > 10:
                            # Controlla se anche l'OCR ha trovato una tabella
                            if self.detect_table(ocr_text):
                                # È una tabella anche nell'OCR - usa OCR avanzato per struttura migliore
                                logging.info(f"Block {i+1}: Tabella rilevata nell'OCR, estrazione struttura con Dolphin/Chandra...")
                                table_structure = self.extract_table_with_advanced_ocr(page, bbox)
                                
                                # Fallback a parsing normale se OCR avanzato fallisce
                                if not table_structure or table_structure.get('num_rows', 0) < 2:
                                    table_structure = self.parse_table_structure(ocr_text)
                                
                                if table_structure and table_structure['num_rows'] >= 2:
                                    translated_table = self.translate_table(table_structure, translator)
                                    if translated_table and translated_table.get('rows'):
                                        # Pulisci area
                                        page.draw_rect(bbox, color=None, fill=WHITE)
                                        
                                        # PROVA PRIMA: Inserimento diretto
                                        success = self.insert_table_direct(page, bbox, translated_table, rgb_color)
                                        
                                        if not success:
                                            # FALLBACK: HTML
                                            logging.warning(f"Block {i+1}: Inserimento diretto OCR fallito, uso HTML")
                                            table_html = self.format_table_html(translated_table, rgb_color)
                                            page.insert_htmlbox(
                                                bbox,
                                                table_html,
                                                css=f"""* {{ font-size: 8pt; }}"""
                                            )
                                        
                                        translated_count += 1
                                        ocr_blocks += 1
                                        logging.info(f"Block {i+1}: Tabella OCR tradotta ({table_structure['num_rows']} righe)")
                                        continue
                            
                            # Normale testo OCR - traduci normalmente
                            translated_ocr = translator.translate(ocr_text.strip())
                            if translated_ocr and translated_ocr.strip():
                                page.draw_rect(bbox, color=None, fill=WHITE)
                                formatted_ocr = self.format_ocr_text([translated_ocr])
                                page.insert_htmlbox(
                                    bbox,
                                    formatted_ocr,
                                    css=f"""* {{
                                        font-family: 'Arial', sans-serif;
                                        font-size: 10pt;
                                        color: rgb({int(rgb_color[0]*255)}, {int(rgb_color[1]*255)}, {int(rgb_color[2]*255)});
                                        line-height: 1.3;
                                        text-align: left;
                                    }}"""
                                )
                                translated_count += 1
                                ocr_blocks += 1
                                logging.debug(f"Block {i+1}: OCR translation ({len(ocr_text)} chars)")
                    except Exception as e:
                        logging.warning(f"OCR failed for block {i+1}: {str(e)}")

        # Se nessun blocco tradotto, prova OCR full-page come fallback
        if translated_count == 0:
            logging.info("No blocks translated, trying full-page OCR fallback")
            try:
                full_text = self.extract_text_improved(page)

                if full_text and not full_text.startswith("[PDF scansionato"):
                    logging.info(f"Full-page OCR extracted {len(full_text)} characters")
                    text_chunks = self.split_text_for_translation(full_text, max_length=800)
                    translated_chunks = []

                    for i, chunk in enumerate(text_chunks):
                        if chunk.strip():
                            try:
                                translated_chunk = translator.translate(chunk.strip())
                                if translated_chunk and translated_chunk.strip():
                                    translated_chunks.append(translated_chunk)
                                    logging.info(f"Translated chunk {i+1}/{len(text_chunks)}")
                            except Exception as e:
                                logging.warning(f"Translation failed for chunk {i+1}: {str(e)}")
                                translated_chunks.append(chunk)

                    if translated_chunks:
                        translated_text = self.format_ocr_text(translated_chunks)
                        page_rect = page.rect
                        margin = 30
                        text_rect = pymupdf.Rect(margin, margin, page_rect.width - margin, page_rect.height - margin)

                        page.draw_rect(page_rect, color=None, fill=WHITE)
                        page.insert_htmlbox(
                            text_rect,
                            translated_text,
                            css=f"""* {{
                                font-family: 'Arial', sans-serif;
                                font-size: 10pt;
                                color: rgb({int(rgb_color[0]*255)}, {int(rgb_color[1]*255)}, {int(rgb_color[2]*255)});
                                line-height: 1.4;
                                text-align: left;
                                margin: 0;
                                padding: 0;
                            }}
                            p {{
                                margin: 8px 0;
                                text-indent: 0;
                            }}
                            .section {{
                                font-weight: bold;
                                font-size: 12pt;
                                margin: 15px 0 8px 0;
                            }}
                            .subsection {{
                                font-weight: bold;
                                font-size: 11pt;
                                margin: 12px 0 6px 0;
                            }}
                            .list-item {{
                                margin: 4px 0 4px 20px;
                                text-indent: -10px;
                            }}"""
                        )
                        translated_count = len(text_chunks)
                        ocr_blocks = len(text_chunks)
                        logging.info(f"Successfully translated full-page OCR text ({len(text_chunks)} chunks)")
            except Exception as e:
                logging.error(f"Failed to translate with full-page OCR: {str(e)}")

        logging.info(f"Page {page_num + 1}: {normal_blocks} normal blocks, {ocr_blocks} OCR blocks, {translated_count} total translated")
        return new_doc
    
    def analyze_text_quality(self, text):
        """Analizza la qualità del testo estratto per decidere se usare OCR"""
        if not text or len(text.strip()) < 5:
            return {'is_good': False, 'reason': 'too_short'}
        
        text = text.strip()
        
        # Check for common OCR artifacts
        ocr_artifacts = ['�', '�', '\x00', '\x01', '\x02']
        
        # Count OCR artifacts
        artifact_count = sum(text.count(artifact) for artifact in ocr_artifacts)
        artifact_ratio = artifact_count / len(text) if len(text) > 0 else 0
        
        # Check for excessive special characters
        special_chars = sum(1 for c in text if not c.isalnum() and not c.isspace() and c not in '.,!?;:()[]{}"\'')
        special_ratio = special_chars / len(text) if len(text) > 0 else 0
        
        # Check for repeated characters (common in OCR errors)
        repeated_chars = sum(1 for i in range(len(text)-2) if text[i] == text[i+1] == text[i+2])
        repeated_ratio = repeated_chars / len(text) if len(text) > 0 else 0
        
        # Check for mixed case issues (common in OCR)
        words = text.split()
        if words:
            case_issues = sum(1 for word in words if len(word) > 1 and word.islower() and any(c.isupper() for c in word[1:]))
            case_ratio = case_issues / len(words)
        else:
            case_ratio = 0
        
        # Scoring system
        score = 100
        score -= artifact_ratio * 200  # Heavy penalty for artifacts
        if special_ratio > 0.3:
            score -= (special_ratio - 0.3) * 100
        if repeated_ratio > 0.05:
            score -= repeated_ratio * 200
        if case_ratio > 0.2:
            score -= case_ratio * 50
        if len(words) < 2:
            score -= 30
        
        # Check for reasonable character distribution
        alpha_ratio = sum(1 for c in text if c.isalpha()) / len(text) if len(text) > 0 else 0
        if alpha_ratio < 0.5:
            score -= 20
        
        is_good = score >= 60
        
        return {
            'is_good': is_good,
            'score': score,
            'artifact_ratio': artifact_ratio,
            'special_ratio': special_ratio,
            'repeated_ratio': repeated_ratio,
            'case_ratio': case_ratio,
            'alpha_ratio': alpha_ratio,
            'reason': 'good' if is_good else 'poor_quality'
        }
    
    def extract_table_with_dolphin_api(self, img):
        """
        Estrae tabella usando API Python diretta di Dolphin (più veloce e affidabile)
        """
        try:
            dolphin_path = Path(__file__).parent.parent / "Dolphin"
            hf_model_path = Path(__file__).parent.parent / "hf_model"
            
            if not dolphin_path.exists():
                return None
            
            # Importa Dolphin direttamente
            sys.path.insert(0, str(dolphin_path))
            try:
                from demo_page import DOLPHIN
                from utils.utils import prepare_image
                
                # Carica modello (usa cache se già caricato)
                if not hasattr(self, '_dolphin_model') or self._dolphin_model is None:
                    model_path = str(hf_model_path) if hf_model_path.exists() else "ByteDance/Dolphin-1.5"
                    logging.info(f"Caricamento modello Dolphin da {model_path}...")
                    self._dolphin_model = DOLPHIN(model_path)
                    logging.info("Modello Dolphin caricato")
                
                model = self._dolphin_model
                
                # Usa prompt specifico per tabelle
                table_text = model.chat("Parse the table in the image. Extract all rows and columns with their content.", img)
                
                if table_text and len(table_text.strip()) > 10:
                    logging.info("Dolphin API ha estratto testo tabella")
                    return table_text
                
            except ImportError as e:
                logging.debug(f"Dolphin API non disponibile: {e}")
            finally:
                # Rimuovi path
                try:
                    if str(dolphin_path) in sys.path:
                        sys.path.remove(str(dolphin_path))
                except:
                    pass
            
        except Exception as e:
            logging.debug(f"Errore Dolphin API: {e}")
        
        return None
    
    def extract_table_with_advanced_ocr(self, page, bbox):
        """
        Estrae tabella usando Dolphin/Chandra OCR mantenendo struttura
        Ritorna struttura tabellare (righe/colonne) invece di solo testo
        """
        if not OCR_AVAILABLE or not ocr_manager:
            return None
        
        try:
            # Convert bbox to integers
            x0, y0, x1, y1 = [int(coord) for coord in bbox]
            
            # Create a clip rectangle for this specific area
            clip_rect = pymupdf.Rect(x0, y0, x1, y1)
            
            # Render con alta risoluzione per tabelle (4x per migliore qualità)
            resolution = 4.0
            pix = page.get_pixmap(matrix=pymupdf.Matrix(resolution, resolution), clip=clip_rect)
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            
            # PROVA PRIMA: API Python diretta Dolphin (più veloce)
            dolphin_direct = self.extract_table_with_dolphin_api(img)
            if dolphin_direct:
                # Prova parsing come tabella
                if '|' in dolphin_direct:
                    lines = dolphin_direct.split('\n')
                    table_lines = []
                    for line in lines:
                        line = line.strip()
                        if line and '|' in line:
                            cells = [c.strip() for c in line.split('|')]
                            while cells and not cells[0]:
                                cells.pop(0)
                            while cells and not cells[-1]:
                                cells.pop()
                            if len(cells) >= 2:
                                table_lines.append(cells)
                    
                    if len(table_lines) >= 2:
                        max_cols = max(len(row) for row in table_lines) if table_lines else 0
                        normalized = []
                        for row in table_lines:
                            while len(row) < max_cols:
                                row.append('')
                            normalized.append(row[:max_cols])
                        
                        logging.info(f"Dolphin API ha estratto tabella: {len(normalized)} righe x {max_cols} colonne")
                        return {
                            'rows': normalized,
                            'num_rows': len(normalized),
                            'num_cols': max_cols
                        }
                
                # Parsing intelligente
                table_structure = self.parse_table_structure(dolphin_direct)
                if table_structure and table_structure['num_rows'] >= 2:
                    logging.info(f"Dolphin API tabella strutturata: {table_structure['num_rows']} righe")
                    return table_structure
            
            # PROVA SECONDA: Dolphin via subprocess (fallback)
            if ocr_manager.is_available(OCREngine.DOLPHIN):
                try:
                    logging.info(f"Tentativo estrazione tabella con Dolphin OCR (specializzato tabelle)...")
                    dolphin_text = ocr_manager.extract_text(img, engine=OCREngine.DOLPHIN, lang='eng')
                    if dolphin_text and len(dolphin_text.strip()) > 10:
                        # Dolphin può restituire tabelle in diversi formati:
                        # 1. Markdown pipe tables (| col1 | col2 |)
                        # 2. HTML tables
                        # 3. Testo strutturato
                        
                        # PRIORITÀ 1: Tabella markdown con pipe (formato più comune)
                        if '|' in dolphin_text:
                            lines = dolphin_text.split('\n')
                            table_lines = []
                            for line in lines:
                                line = line.strip()
                                if line and '|' in line:
                                    # Linea tabella markdown - rimuovi bordi iniziali/finali
                                    cells = [c.strip() for c in line.split('|')]
                                    # Rimuovi celle vuote ai bordi
                                    while cells and not cells[0]:
                                        cells.pop(0)
                                    while cells and not cells[-1]:
                                        cells.pop()
                                    if len(cells) >= 2:
                                        table_lines.append(cells)
                            
                            if len(table_lines) >= 2:
                                # Normalizza colonne
                                max_cols = max(len(row) for row in table_lines) if table_lines else 0
                                normalized = []
                                for row in table_lines:
                                    while len(row) < max_cols:
                                        row.append('')
                                    normalized.append(row[:max_cols])
                                
                                logging.info(f"Dolphin ha estratto tabella markdown: {len(normalized)} righe x {max_cols} colonne")
                                return {
                                    'rows': normalized,
                                    'num_rows': len(normalized),
                                    'num_cols': max_cols
                                }
                        
                        # PRIORITÀ 2: Parsing intelligente del testo
                        table_structure = self.parse_table_structure(dolphin_text)
                        if table_structure and table_structure['num_rows'] >= 2:
                            logging.info(f"Dolphin ha estratto tabella strutturata: {table_structure['num_rows']} righe x {table_structure['num_cols']} colonne")
                            return table_structure
                        
                        logging.debug("Dolphin ha estratto testo ma non tabella strutturata")
                except Exception as e:
                    logging.debug(f"Dolphin OCR failed: {e}")
                    import traceback
                    logging.debug(traceback.format_exc())
            
            # PROVA CHANDRA (specifico per tabelle)
            if ocr_manager.is_available(OCREngine.CHANDRA):
                try:
                    logging.info(f"Tentativo estrazione tabella con Chandra OCR...")
                    chandra_text = ocr_manager.extract_text(img, engine=OCREngine.CHANDRA, lang='eng')
                    if chandra_text and len(chandra_text.strip()) > 10:
                        table_structure = self.parse_table_structure(chandra_text)
                        if table_structure and table_structure['num_rows'] >= 2:
                            logging.info(f"Chandra ha estratto tabella: {table_structure['num_rows']} righe x {table_structure['num_cols']} colonne")
                            return table_structure
                except Exception as e:
                    logging.debug(f"Chandra OCR failed: {e}")
            
            # FALLBACK: usa Tesseract con parsing intelligente
            if ocr_manager.is_available(OCREngine.TESSERACT):
                try:
                    logging.info(f"Fallback a Tesseract OCR per tabella...")
                    # Configura Tesseract per tabelle (PSM mode 6 = uniform block of text)
                    tesseract_text = ocr_manager.extract_text(img, engine=OCREngine.TESSERACT, lang='eng')
                    if tesseract_text and len(tesseract_text.strip()) > 10:
                        table_structure = self.parse_table_structure(tesseract_text)
                        if table_structure and table_structure['num_rows'] >= 2:
                            logging.info(f"Tesseract ha estratto tabella: {table_structure['num_rows']} righe")
                            return table_structure
                except Exception as e:
                    logging.debug(f"Tesseract OCR failed: {e}")
            
            return None
                
        except Exception as e:
            logging.warning(f"Errore estrazione tabella avanzata: {str(e)}")
            return None
    
    def extract_text_from_bbox(self, page, bbox, prefer_advanced=False):
        """
        Estrae testo da un'area specifica usando OCR - METODO ROBUSTO con sistema modulare
        prefer_advanced: Se True, prova prima Dolphin/Chandra (migliori per tabelle/scannerizzati)
        """
        if not OCR_AVAILABLE or not ocr_manager:
            return None
        
        try:
            # Convert bbox to integers
            x0, y0, x1, y1 = [int(coord) for coord in bbox]
            
            # Create a clip rectangle for this specific area
            clip_rect = pymupdf.Rect(x0, y0, x1, y1)
            
            # Render the specific area as image with higher resolution (3x per tabelle/scannerizzati)
            resolution = 3.0 if prefer_advanced else 2.0
            pix = page.get_pixmap(matrix=pymupdf.Matrix(resolution, resolution), clip=clip_rect)
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            
            # Strategia OCR intelligente per tabelle e documenti scannerizzati
            engines_to_try = []
            
            if prefer_advanced:
                # Per tabelle/scannerizzati: priorità Dolphin e Chandra
                if ocr_manager.is_available(OCREngine.DOLPHIN):
                    engines_to_try.append(OCREngine.DOLPHIN)
                if ocr_manager.is_available(OCREngine.CHANDRA):
                    engines_to_try.append(OCREngine.CHANDRA)
            
            # Sempre include Tesseract come fallback
            if ocr_manager.is_available(OCREngine.TESSERACT):
                engines_to_try.append(OCREngine.TESSERACT)
            
            # Prova ogni motore in ordine
            for engine in engines_to_try:
                try:
                    ocr_text = ocr_manager.extract_text(img, engine=engine, lang='eng')
                    if ocr_text and len(ocr_text.strip()) > 5:
                        logging.debug(f"OCR extracted {len(ocr_text)} characters from bbox {bbox} usando {engine.value}")
                        return ocr_text.strip()
                except Exception as e:
                    logging.debug(f"OCR {engine.value} failed per bbox {bbox}: {e}")
                    continue
            
            # Se nessuno funziona, prova AUTO come ultimo tentativo
            ocr_text = ocr_manager.extract_text(img, engine=OCREngine.AUTO, lang='eng')
            if ocr_text and len(ocr_text.strip()) > 5:
                logging.debug(f"OCR extracted {len(ocr_text)} characters from bbox {bbox} (AUTO)")
                return ocr_text.strip()
            else:
                logging.debug(f"OCR failed for bbox {bbox}")
                return None
                
        except Exception as e:
            logging.warning(f"OCR extraction failed for bbox {bbox}: {str(e)}")
            return None
    
    def split_text_for_translation(self, text, max_length=1000):
        """Dividi il testo in chunk per la traduzione"""
        if len(text) <= max_length:
            return [text]
        
        # Dividi per paragrafi prima
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            if len(current_chunk + paragraph) <= max_length:
                current_chunk += paragraph + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = paragraph + "\n\n"
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def detect_table(self, text):
        """Rileva se un testo è una tabella analizzando pattern caratteristici"""
        if not text or len(text.strip()) < 20:
            return False
        
        lines = text.strip().split('\n')
        if len(lines) < 3:  # Minimo 3 righe per una tabella
            return False
        
        # Conta caratteristiche tabelle:
        # - Spazi multipli consecutivi (separatori colonne)
        # - Pattern numerici con separatori (prezzi, date, codici)
        # - Allineamento verticale (spazi all'inizio delle righe simili)
        # - Parole chiave tabellari (Table, Product, Code, Price, etc.)
        table_indicators = 0
        
        # Pattern 1: Spazi multipli consecutivi (separatori colonne)
        multi_space_count = sum(1 for line in lines if re.search(r' {2,}', line))
        if multi_space_count >= len(lines) * 0.5:  # Almeno 50% delle righe
            table_indicators += 2
        
        # Pattern 2: Numeri formattati (prezzi, date, codici)
        number_pattern = re.compile(r'\$\d+[\d,\.]+|€\d+[\d,\.]+|\d+[\d,\.]+\s*USD|\d+[\d,\.]+\s*EUR|\d{4}-\d{2}-\d{2}')
        number_count = sum(1 for line in lines if number_pattern.search(line))
        if number_count >= 2:
            table_indicators += 2
        
        # Pattern 3: Parole chiave tabelle
        table_keywords = ['table', 'tabella', 'product', 'prodotto', 'code', 'codice', 'price', 'prezzo', 
                         'description', 'descrizione', 'qty', 'quantity', 'quantità', 'total', 'totale',
                         'header', 'intestazione', 'row', 'riga', 'column', 'colonna']
        keyword_count = sum(1 for line in lines for keyword in table_keywords if keyword.lower() in line.lower())
        if keyword_count >= 2:
            table_indicators += 1
        
        # Pattern 4: Righe con pattern ripetitivo (allineamento colonne)
        # Cerca righe che iniziano con pattern simili (codici prodotto, numeri, etc.)
        pattern_start = re.compile(r'^[A-Z0-9-]+\s+')
        pattern_start_count = sum(1 for line in lines if pattern_start.match(line.strip()))
        if pattern_start_count >= 3:
            table_indicators += 2
        
        # Pattern 5: Righe con almeno 3 elementi separati da spazi multipli
        tab_separated = sum(1 for line in lines if len(re.split(r' {2,}|\t+', line.strip())) >= 3)
        if tab_separated >= len(lines) * 0.4:
            table_indicators += 2
        
        # Considera tabella se almeno 4 indicatori
        return table_indicators >= 4
    
    def parse_table_structure(self, text):
        """Estrae struttura tabella (righe e colonne) dal testo"""
        lines = [line.strip() for line in text.strip().split('\n') if line.strip()]
        
        if not lines:
            return None
        
        # Prova diversi separatori
        rows = []
        max_cols = 0
        
        for line in lines:
            # Prova separatori: spazi multipli, tab, pipe, o virgole
            if re.search(r' {3,}', line):
                # Spazi multipli come separatore
                cols = re.split(r' {3,}', line)
            elif '\t' in line:
                # Tab come separatore
                cols = line.split('\t')
            elif '|' in line:
                # Pipe come separatore
                cols = [c.strip() for c in line.split('|') if c.strip()]
            elif re.search(r'\s{2,}', line):
                # Spazi multipli (almeno 2)
                cols = re.split(r' {2,}', line)
            else:
                # Prova a dividere per spazi se ci sono pattern numerici/alfanumerici
                parts = line.split()
                if len(parts) >= 3:
                    # Cerca pattern: codice prodotto + descrizione + prezzo
                    # Se trovi numero/valuta alla fine, separa
                    cols = []
                    current_col = []
                    for i, part in enumerate(parts):
                        if re.match(r'^[\$€]\d+|^\d+[\d,\.]+$', part) and i > 1:
                            # Inizia nuova colonna con numero/prezzo
                            if current_col:
                                cols.append(' '.join(current_col))
                            current_col = [part]
                        else:
                            current_col.append(part)
                    if current_col:
                        cols.append(' '.join(current_col))
                else:
                    cols = parts
            
            # Pulisci colonne
            cols = [c.strip() for c in cols if c.strip()]
            if cols:
                rows.append(cols)
                max_cols = max(max_cols, len(cols))
        
        # Normalizza: assicura che tutte le righe abbiano lo stesso numero di colonne
        normalized_rows = []
        for row in rows:
            # Padding con celle vuote se necessario
            while len(row) < max_cols:
                row.append('')
            normalized_rows.append(row[:max_cols])  # Tronca se troppo colonne
        
        if normalized_rows and max_cols >= 2:
            return {
                'rows': normalized_rows,
                'num_rows': len(normalized_rows),
                'num_cols': max_cols
            }
        
        return None
    
    def translate_table(self, table_data, translator):
        """Traduce tabella mantenendo struttura: ogni cella viene tradotta separatamente"""
        if not table_data or not table_data.get('rows'):
            return None
        
        translated_rows = []
        rows = table_data['rows']
        
        for row_idx, row in enumerate(rows):
            translated_row = []
            for col_idx, cell in enumerate(row):
                cell_text = cell.strip()
                if not cell_text:
                    translated_row.append('')
                    continue
                
                # Non tradurre se è solo numeri/simboli (prezzi, codici, date)
                if re.match(r'^[\$€]\d+[\d,\.]*$|^\d+[\d,\.]+\s*$|^\d{4}-\d{2}-\d{2}$|^[A-Z0-9-]+$', cell_text):
                    # Mantieni numeri/prezzi/codici invariati
                    translated_row.append(cell_text)
                else:
                    # Traduci contenuto testuale
                    try:
                        translated_cell = translator.translate(cell_text)
                        translated_row.append(translated_cell if translated_cell else cell_text)
                    except Exception as e:
                        logging.debug(f"Errore traduzione cella [{row_idx}][{col_idx}]: {e}")
                        translated_row.append(cell_text)
            
            translated_rows.append(translated_row)
        
        return {
            'rows': translated_rows,
            'num_rows': len(translated_rows),
            'num_cols': table_data['num_cols']
        }
    
    def insert_table_direct(self, page, bbox, table_data, rgb_color):
        """
        Inserisce tabella disegnando direttamente celle per cella nel PDF
        Questo preserva la struttura meglio di HTML - ogni cella viene posizionata esattamente
        """
        if not table_data or not table_data.get('rows'):
            return False
        
        try:
            rows = table_data['rows']
            num_cols = table_data['num_cols']
            
            # Calcola dimensioni bbox
            x0, y0, x1, y1 = [float(coord) for coord in bbox]
            table_width = x1 - x0
            table_height = y1 - y0
            
            # Calcola dimensioni celle
            padding = 2.0  # Padding interno celle
            col_width = (table_width - padding) / num_cols if num_cols > 0 else table_width
            row_height = min((table_height - padding) / len(rows), 12.0)  # Max 12pt per riga, più compatto
            
            # Colore testo
            text_color = (rgb_color[0], rgb_color[1], rgb_color[2])
            
            # Font size
            font_size = 8  # Font piccolo per tabelle
            
            # PRIMA: Disegna bordi struttura (per visualizzazione migliore)
            # Bordo esterno
            page.draw_rect((x0, y0, x1, y1), color=(0.5, 0.5, 0.5), width=0.8)
            
            # Disegna ogni cella con testo
            for row_idx, row in enumerate(rows):
                y_cell_top = y0 + padding + (row_idx * row_height)
                y_cell_bottom = y_cell_top + row_height
                y_text_pos = y_cell_top + 8  # Posizione testo (8pt dal top cella)
                
                # Disegna bordo superiore riga (più spesso per header)
                line_width = 1.0 if row_idx == 0 else 0.5
                page.draw_line((x0, y_cell_top), (x1, y_cell_top), color=(0.5, 0.5, 0.5), width=line_width)
                
                for col_idx, cell in enumerate(row):
                    x_cell_left = x0 + padding + (col_idx * col_width)
                    x_cell_right = x_cell_left + col_width
                    x_text_pos = x_cell_left + 2  # 2pt padding left per testo
                    
                    cell_text = str(cell).strip() if cell else ""
                    
                    # Gestisci testo lungo: tronca o wrappa
                    # Calcola max caratteri che entrano nella cella
                    max_chars = int((col_width - 4) / 3.5)  # ~3.5pt per carattere a font 8
                    if len(cell_text) > max_chars:
                        # Tronca con ellipsis se troppo lungo
                        cell_text = cell_text[:max_chars-3] + "..."
                    
                    # Inserisci testo nella cella
                    if cell_text:
                        try:
                            # Usa insert_text per inserire testo in posizione esatta
                            page.insert_text(
                                (x_text_pos, y_text_pos),
                                cell_text,
                                fontsize=font_size,
                                color=text_color,
                                fontname="helv"
                            )
                        except Exception as e:
                            logging.debug(f"Errore inserimento testo cella [{row_idx}][{col_idx}]: {e}")
                    
                    # Disegna bordo verticale tra colonne (se non ultima colonna)
                    if col_idx < num_cols - 1:
                        page.draw_line(
                            (x_cell_right, y_cell_top),
                            (x_cell_right, y_cell_bottom),
                            color=(0.7, 0.7, 0.7), width=0.3
                        )
            
            return True
            
        except Exception as e:
            logging.error(f"Errore inserimento tabella diretta: {e}")
            import traceback
            logging.error(traceback.format_exc())
            return False
    
    def format_table_html(self, table_data, rgb_color):
        """Crea HTML tabella formattata per inserimento in PDF (fallback)"""
        if not table_data or not table_data.get('rows'):
            return ""
        
        rows = table_data['rows']
        html_rows = []
        
        for row_idx, row in enumerate(rows):
            html_cells = []
            is_header = row_idx == 0  # Prima riga = header
            
            for cell in row:
                # Escapa caratteri HTML
                cell_html = str(cell).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                # Usa <th> per header, <td> per altre righe
                tag = 'th' if is_header else 'td'
                html_cells.append(f'<{tag}>{cell_html}</{tag}>')
            
            html_rows.append(f'<tr>{"".join(html_cells)}</tr>')
        
        # CSS per tabella formattata
        css_color = f"rgb({int(rgb_color[0]*255)}, {int(rgb_color[1]*255)}, {int(rgb_color[2]*255)})"
        
        html = f"""
        <table style="border-collapse: collapse; width: 100%; font-size: 9pt; color: {css_color};">
        <style>
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ 
                border: 1px solid #ddd; 
                padding: 4px 6px; 
                text-align: left; 
                vertical-align: top;
            }}
            th {{ background-color: #f5f5f5; font-weight: bold; }}
            tr:nth-child(even) {{ background-color: #fafafa; }}
        </style>
        {''.join(html_rows)}
        </table>
        """
        
        return html
    
    def format_ocr_text(self, translated_chunks):
        """Formatta il testo OCR tradotto per mantenere la struttura con HTML intelligente"""
        full_text = "\n\n".join(translated_chunks)
        
        # PRIMA: Controlla se è una tabella
        if self.detect_table(full_text):
            logging.info("Tabella rilevata nel testo OCR")
            table_structure = self.parse_table_structure(full_text)
            if table_structure:
                # È una tabella strutturata - formatta come tabella HTML
                # NOTA: La traduzione dovrebbe essere già fatta, quindi usiamo full_text tradotto
                # Se non lo è, potrebbe essere necessario tradurre qui
                rgb_color = COLOR_MAP.get(self.text_color.get(), COLOR_MAP["Rosso"])
                return self.format_table_html(table_structure, rgb_color)
        
        # Cerca di identificare sezioni e sottosezioni
        lines = full_text.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                formatted_lines.append('<p>&nbsp;</p>')
                continue
            
            # Identifica sezioni principali (numeri seguiti da punto con maiuscola)
            if re.match(r'^\d+\.\s+[A-Z]', line):
                formatted_lines.append(f'<div class="section">{line}</div>')
            # Identifica sottosezioni (numeri con decimali)
            elif re.match(r'^\d+\.\d+', line):
                formatted_lines.append(f'<div class="subsection">{line}</div>')
            # Identifica elementi di lista (lettere o numeri con parentesi)
            elif re.match(r'^[a-zA-Z]\)\s+', line) or re.match(r'^\d+\)\s+', line):
                formatted_lines.append(f'<div class="list-item">{line}</div>')
            # Identifica bullet points
            elif re.match(r'^[•\-\*]\s+', line):
                formatted_lines.append(f'<div class="list-item">{line}</div>')
            # Identifica titoli (tutto maiuscolo)
            elif line.isupper() and len(line.split()) > 1:
                formatted_lines.append(f'<div class="section">{line}</div>')
            # Paragrafi normali
            else:
                formatted_lines.append(f'<p>{line}</p>')
        
        return '\n'.join(formatted_lines)
    
    def translate_current_page(self):
        """Traduci pagina corrente"""
        if not self.current_doc:
            messagebox.showwarning("Attenzione", "Carica prima un PDF")
            return
        
        if self.is_translating:
            messagebox.showinfo("Info", "Traduzione già in corso...")
            return
        
        def translate_thread():
            self.is_translating = True
            try:
                self.update_status(f"⏳ Traduzione pagina {self.current_page + 1}...")
                self.progress.pack(side=tk.RIGHT, padx=10)
                self.progress.start(10)
                
                translated_doc = self.translate_page(self.current_page)
                self.translated_pages[self.current_page] = translated_doc
                
                self.display_translated_page(translated_doc)
                
                self.progress.stop()
                self.progress.pack_forget()
                self.update_status(f"✓ Pagina {self.current_page + 1} tradotta")
                
            except Exception as e:
                self.progress.stop()
                self.progress.pack_forget()
                error_msg = (
                    f"Errore durante la traduzione:\n{str(e)}\n\n"
                    "Possibili cause:\n"
                    "• Connessione internet instabile (se usi Google Translate)\n"
                    "• PDF troppo complesso\n"
                    "• Memoria insufficiente\n\n"
                    "Suggerimenti:\n"
                    "• Prova a tradurre una pagina alla volta\n"
                    "• Verifica la connessione internet\n"
                    "• Chiudi altre applicazioni pesanti"
                )
                messagebox.showerror("Errore - Traduzione Fallita", error_msg)
                logging.error(f"Translation failed: {str(e)}", exc_info=True)
                self.update_status("✗ Traduzione fallita")
            finally:
                self.is_translating = False
        
        threading.Thread(target=translate_thread, daemon=True).start()
    
    def translate_all_pages(self):
        """Traduci tutte le pagine"""
        if not self.current_doc:
            messagebox.showwarning("Attenzione", "Carica prima un PDF")
            return
        
        if self.is_translating:
            messagebox.showinfo("Info", "Traduzione già in corso...")
            return
        
        result = messagebox.askyesno(
            "Conferma", 
            f"Vuoi tradurre tutte le {self.current_doc.page_count} pagine?\n"
            f"Potrebbe richiedere diversi minuti."
        )
        
        if not result:
            return
        
        def translate_all_thread():
            self.is_translating = True
            try:
                self.progress.pack(side=tk.RIGHT, padx=10)
                self.progress.start(10)
                
                total_pages = self.current_doc.page_count
                for page_num in range(total_pages):
                    if self.translated_pages[page_num]:
                        self.update_status(f"⏭ Pagina {page_num + 1}/{total_pages} già tradotta")
                        continue
                    
                    self.update_status(f"⏳ Traduzione pagina {page_num + 1}/{total_pages}...")
                    translated_doc = self.translate_page(page_num)
                    self.translated_pages[page_num] = translated_doc
                
                self.progress.stop()
                self.progress.pack_forget()
                self.update_status(f"✓ Tradotte tutte le {total_pages} pagine!")
                messagebox.showinfo("Completato", f"✓ Tradotte tutte le {total_pages} pagine!")
                
            except Exception as e:
                self.progress.stop()
                self.progress.pack_forget()
                error_msg = (
                    f"Errore durante la traduzione di tutte le pagine:\n{str(e)}\n\n"
                    "Possibili cause:\n"
                    "• Connessione internet instabile (se usi Google Translate)\n"
                    "• PDF troppo grande o complesso\n"
                    "• Memoria insufficiente\n"
                    "• Timeout durante traduzione\n\n"
                    "Suggerimenti:\n"
                    "• Prova a tradurre poche pagine alla volta\n"
                    "• Verifica la connessione internet\n"
                    "• Chiudi altre applicazioni pesanti\n"
                    "• Usa Argos Translate (offline) se problemi con Google"
                )
                messagebox.showerror("Errore - Traduzione Fallita", error_msg)
                logging.error(f"Translation failed: {str(e)}", exc_info=True)
                self.update_status("✗ Traduzione fallita")
            finally:
                self.is_translating = False
        
        threading.Thread(target=translate_all_thread, daemon=True).start()
    
    def save_pdf(self):
        """Salva PDF tradotto"""
        if not any(self.translated_pages):
            messagebox.showwarning("Attenzione", "Traduci prima almeno una pagina")
            return
        
        # Proponi salvataggio nella cartella output
        default_filename = f"translated_{os.path.basename(self.pdf_path)}"
        default_path = str(OUTPUT_DIR / default_filename)
        
        output_path = filedialog.asksaveasfilename(
            title="Salva PDF tradotto",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialdir=str(OUTPUT_DIR),
            initialfile=default_filename
        )
        
        if output_path:
            try:
                self.update_status("⏳ Salvataggio PDF...")
                output_doc = pymupdf.open()
                
                for page_num, translated_doc in enumerate(self.translated_pages):
                    if translated_doc:
                        output_doc.insert_pdf(translated_doc)
                    else:
                        # Usa pagina originale se non tradotta
                        output_doc.insert_pdf(self.current_doc, from_page=page_num, to_page=page_num)
                
                output_doc.save(
                    output_path,
                    garbage=4,
                    deflate=True,
                    clean=True
                )
                
                self.update_status(f"✓ Salvato: {os.path.basename(output_path)}")
                logging.info(f"Saved translated PDF: {output_path}")
                messagebox.showinfo("Successo", f"✓ PDF salvato:\n{output_path}")
            except Exception as e:
                messagebox.showerror("Errore", f"Impossibile salvare PDF: {str(e)}")
                logging.error(f"Failed to save PDF: {str(e)}")
    
    def update_status(self, message, status_type='info'):
        """Aggiorna barra stato con colori dinamici"""
        color_map = {
            'success': self.colors['success'],
            'error': self.colors['error'],
            'warning': self.colors['warning'],
            'info': self.colors['text'],
            'progress': self.colors['accent']
        }
        
        # Detect status type from message
        if message.startswith('✓') or 'completat' in message.lower() or 'salvat' in message.lower():
            status_type = 'success'
        elif message.startswith('✗') or 'error' in message.lower() or 'fallita' in message.lower():
            status_type = 'error'
        elif message.startswith('⏳') or 'traduzione' in message.lower() or 'salvataggio' in message.lower():
            status_type = 'progress'
        elif message.startswith('⚠') or 'attenzione' in message.lower():
            status_type = 'warning'
        
        self.status_bar.config(text=message, fg=color_map.get(status_type, self.colors['text']))
        self.root.update_idletasks()
    
    def update_recent_files_menu(self):
        """Aggiorna menu file recenti"""
        if not SETTINGS_AVAILABLE:
            return
        
        # Pulisci menu
        self.recent_files_menu.delete(0, tk.END)
        
        recent_files = self.settings_manager.get_recent_files()
        
        if not recent_files:
            self.recent_files_menu.add_command(label="(Nessun file recente)", state="disabled")
        else:
            for i, file_path in enumerate(recent_files[:10]):  # Max 10 file recenti
                # Prendi solo nome file per display
                file_name = os.path.basename(file_path)
                # Tronca se troppo lungo
                if len(file_name) > 50:
                    file_name = file_name[:47] + "..."
                
                # Aggiungi numero per accesso rapido
                label = f"&{i+1} {file_name}"
                self.recent_files_menu.add_command(
                    label=label,
                    command=lambda path=file_path: self.open_recent_file(path)
                )
            
            self.recent_files_menu.add_separator()
            self.recent_files_menu.add_command(
                label="Pulisci Elenco",
                command=self.clear_recent_files
            )
    
    def open_recent_file(self, file_path):
        """Apri file dai recenti"""
        if os.path.exists(file_path):
            self.pdf_path = file_path
            self.file_label.config(text=os.path.basename(file_path))
            self.load_pdf()
            # Aggiorna recent files (lo sposta in cima)
            if SETTINGS_AVAILABLE:
                self.settings_manager.add_recent_file(file_path)
                self.update_recent_files_menu()
        else:
            messagebox.showwarning(
                "File Non Trovato",
                f"Il file non esiste più:\n{file_path}\n\n"
                "Sarà rimosso dall'elenco dei file recenti."
            )
            # Rimuovi da recent files
            if SETTINGS_AVAILABLE:
                recent = self.settings_manager.get_recent_files()
                if file_path in recent:
                    recent.remove(file_path)
                    self.settings_manager.set('recent_files', recent)
                    self.update_recent_files_menu()
    
    def clear_recent_files(self):
        """Pulisci elenco file recenti"""
        result = messagebox.askyesno(
            "Conferma",
            "Vuoi rimuovere tutti i file dall'elenco recenti?"
        )
        if result and SETTINGS_AVAILABLE:
            self.settings_manager.set('recent_files', [])
            self.update_recent_files_menu()
    
    def check_license_on_startup(self):
        """Controlla licenza all'avvio"""
        if not LICENSE_AVAILABLE:
            return True
        
        # Mostra EULA se non accettato
        if not self.check_eula_acceptance():
            self.root.quit()
            return False
        
        if not self.license_manager.check_license():
            # Nessuna licenza valida, mostra dialog attivazione
            dialog = LicenseActivationDialog(self.root)
            self.root.wait_window(dialog.dialog)
            
            # Verifica di nuovo dopo dialog
            if not self.license_manager.check_license():
                messagebox.showwarning(
                    "Licenza Richiesta",
                    "LAC TRANSLATE richiede una licenza valida per funzionare.\n\n"
                    "Il software sarà chiuso. Contatta il supporto per ottenere una licenza."
                )
                self.root.quit()
                return False
        
        return True
    
    def check_eula_acceptance(self):
        """Verifica accettazione EULA"""
        eula_file = BASE_DIR / "license" / "eula_accepted.txt"
        
        if eula_file.exists():
            return True
        
        # Mostra dialog EULA
        license_text = self.load_eula_text()
        
        if license_text:
            result = messagebox.askyesno(
                "Accettazione Licenza Software",
                f"{license_text}\n\n"
                "Accetti i termini della licenza?",
                icon='question'
            )
            
            if result:
                # Salva accettazione
                eula_file.parent.mkdir(parents=True, exist_ok=True)
                with open(eula_file, 'w') as f:
                    f.write(f"EULA accepted on {__import__('datetime').datetime.now().isoformat()}\n")
                return True
            else:
                messagebox.showinfo(
                    "Licenza Richiesta",
                    "È necessario accettare i termini della licenza per utilizzare LAC TRANSLATE.\n\n"
                    "Il software sarà chiuso."
                )
                return False
        
        return True
    
    def load_eula_text(self):
        """Carica testo EULA"""
        license_file = BASE_DIR / "LICENSE.txt"
        if license_file.exists():
            try:
                with open(license_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                # Prendi solo le prime righe per il dialog
                lines = content.split('\n')[:15]
                return '\n'.join(lines) + "\n\n... (leggi il file completo in LICENSE.txt)"
            except:
                pass
        return "End User License Agreement (EULA)\n\nLeggere attentamente prima di utilizzare il software.\n\nAccettando, acconsenti ai termini della licenza."
    
    def show_license_info(self):
        """Mostra informazioni licenza"""
        if not LICENSE_AVAILABLE:
            messagebox.showinfo("Licenza", "Sistema licenze non disponibile")
            return
        
        license_info = self.license_manager.get_license_info()
        
        if license_info['activated']:
            message = (
                f"Licenza Attivata\n\n"
                f"Tipo: {license_info['license_type']}\n"
                f"Chiave: {license_info['serial_key'][:8]}...\n"
                f"ID Hardware: {license_info['hw_id']}\n\n"
                f"Licenza Full - Accesso completo a tutte le funzionalità"
            )
            messagebox.showinfo("Informazioni Licenza", message)
        else:
            messagebox.showwarning(
                "Licenza Non Attivata",
                "Nessuna licenza attiva.\n\nClicca su 'Attiva Licenza' nel menu per attivare il software."
            )
    
    def activate_license_dialog(self):
        """Apre dialog attivazione licenza"""
        if not LICENSE_AVAILABLE:
            messagebox.showinfo("Licenza", "Sistema licenze non disponibile")
            return
        
        dialog = LicenseActivationDialog(self.root)
        self.root.wait_window(dialog.dialog)
        
        # Verifica risultato
        if dialog.result:
            self.update_status("✓ Licenza attivata con successo", 'success')
            messagebox.showinfo("Successo", "Licenza attivata con successo!")
    
    def show_settings_dialog(self):
        """Mostra dialog impostazioni"""
        if not SETTINGS_AVAILABLE:
            messagebox.showinfo("Impostazioni", "Sistema impostazioni non disponibile")
            return
        
        dialog = SettingsDialog(self.root)
        self.root.wait_window(dialog.dialog)
        
        # Reload settings if saved
        if dialog.result:
            # Update UI variables
            self.translator_type.set(self.settings_manager.get('translator_type', 'Google'))
            self.source_lang.set(self.settings_manager.get('source_lang', 'English'))
            self.target_lang.set(self.settings_manager.get('target_lang', 'Italiano'))
            self.text_color.set(self.settings_manager.get('text_color', 'Rosso'))
            
            # Update UI
            self.update_translator_info()
            
            # Update output dir if changed
            new_output_dir = self.settings_manager.get('output_dir')
            if new_output_dir:
                global OUTPUT_DIR
                OUTPUT_DIR = Path(new_output_dir)
                OUTPUT_DIR.mkdir(exist_ok=True)
            
            self.update_status("✓ Impostazioni salvate", 'success')
    
    def show_about(self):
        """Mostra dialog About"""
        try:
            from version import get_version_full, get_build_info
            build_info = get_build_info()
            version_text = f"v{build_info['version_full']}"
            build_date = build_info.get('build_date', 'N/A')
        except:
            version_text = "v2.0.0"
            build_date = "N/A"
        
        about_text = (
            f"LAC TRANSLATE {version_text}\n\n"
            "Traduttore PDF Professionale\n\n"
            "Sviluppato per studi legali e professionisti\n"
            "Traduzione PDF con preservazione layout\n"
            "Supporto OCR per documenti scansionati\n\n"
            "Traduttori:\n"
            "- Google Translate (online)\n"
            "- Argos Translate (offline, privacy totale)\n\n"
            f"Build: {build_date}\n\n"
            "© 2024 LAC Software\n\n"
            "Supporto: info@lucertae.com"
        )
        messagebox.showinfo("Informazioni su LAC TRANSLATE", about_text)
    
    def create_separator(self, parent):
        """Crea un separatore verticale minimal"""
        separator = tk.Frame(parent, bg=self.colors['border'], width=1)
        return separator
    
    def create_tooltip(self, widget, text):
        """Crea tooltip per widget"""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            label = tk.Label(
                tooltip,
                text=text,
                background="#ffffe0",
                foreground="black",
                relief="solid",
                borderwidth=1,
                font=('Segoe UI', 9),
                justify=tk.LEFT,
                padx=5,
                pady=3
            )
            label.pack()
            widget.tooltip = tooltip
        
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
        
        widget.bind('<Enter>', on_enter)
        widget.bind('<Leave>', on_leave)
    
    def show_help(self):
        """Mostra guida"""
        help_text = (
            "LAC TRANSLATE - Guida Rapida\n\n"
            "1. Apri un file PDF (Ctrl+O)\n"
            "2. Seleziona lingua sorgente e destinazione\n"
            "3. Scegli il traduttore (Google o Argos)\n"
            "4. Clicca 'Traduci Pagina' o 'Traduci Tutto'\n"
            "5. Salva il PDF tradotto (Ctrl+S)\n\n"
            "Shortcuts:\n"
            "- Ctrl+O: Apri file\n"
            "- Ctrl+S: Salva\n"
            "- F5: Traduci pagina corrente\n"
            "- F6: Traduci tutte le pagine\n"
            "- Ctrl++: Zoom in\n"
            "- Ctrl+-: Zoom out\n"
            "- Ctrl+0: Zoom adatta alla finestra\n\n"
            "Per maggiori informazioni, consulta il manuale utente."
        )
        messagebox.showinfo("Guida", help_text)
    
    def check_updates(self):
        """Controlla aggiornamenti disponibili"""
        try:
            from update_checker import UpdateChecker
            from update_downloader import UpdateDownloader
            import webbrowser
            
            self.update_status("Controllo aggiornamenti...", 'info')
            
            # Controlla in thread separato per non bloccare UI
            def check_thread():
                try:
                    checker = UpdateChecker()
                    update_info = checker.check_for_updates()
                    
                    # Esegui nella thread principale
                    self.root.after(0, lambda: self.handle_update_result(update_info, checker))
                except Exception as e:
                    logging.error(f"Error checking updates: {e}")
                    self.root.after(0, lambda: messagebox.showerror(
                        "Errore", 
                        f"Errore durante il controllo aggiornamenti:\n{str(e)}"
                    ))
            
            # Avvia thread
            threading.Thread(target=check_thread, daemon=True).start()
            
        except ImportError as e:
            logging.error(f"Update checker not available: {e}")
            messagebox.showerror("Errore", "Sistema aggiornamenti non disponibile")
        except Exception as e:
            logging.error(f"Error in check_updates: {e}")
            messagebox.showerror("Errore", f"Errore imprevisto: {str(e)}")
    
    def handle_update_result(self, update_info, checker):
        """Gestisce risultato controllo aggiornamenti"""
        try:
            from update_downloader import UpdateDownloader
            import webbrowser
            
            if not update_info:
                messagebox.showinfo(
                    "Aggiornamenti", 
                    "Impossibile verificare aggiornamenti.\n\nControlla la connessione internet."
                )
                self.update_status("", 'info')
                return
            
            if update_info.get('available'):
                # Aggiornamento disponibile
                current = update_info['current_version']
                latest = update_info['latest_version']
                release_info = update_info['release_info']
                
                msg = (
                    f"Nuova versione disponibile!\n\n"
                    f"Versione corrente: {current}\n"
                    f"Nuova versione: {latest}\n\n"
                    f"Vuoi scaricare l'aggiornamento?"
                )
                
                if messagebox.askyesno("Aggiornamento Disponibile", msg):
                    # Opzione 1: Apri pagina GitHub Release
                    release_url = release_info.get('html_url')
                    if release_url:
                        response = messagebox.askyesno(
                            "Scarica Aggiornamento",
                            "Vuoi aprire la pagina di download su GitHub?\n\n"
                            "Da lì potrai scaricare l'installer più recente."
                        )
                        if response:
                            webbrowser.open(release_url)
                    
                    # Opzione 2: Download automatico (se disponibile)
                    downloader = UpdateDownloader()
                    download_url = checker.get_download_url()
                    
                    if download_url:
                        response2 = messagebox.askyesno(
                            "Download Automatico",
                            f"Vuoi scaricare automaticamente l'installer?\n\n"
                            f"File: {download_url.split('/')[-1]}\n"
                            f"Salvato in: downloads/"
                        )
                        if response2:
                            self.download_update_file(download_url, downloader)
            else:
                # Già aggiornato
                messagebox.showinfo(
                    "Aggiornamenti", 
                    f"Sei già alla versione più recente!\n\nVersione: {update_info.get('current_version', 'N/A')}"
                )
            
            self.update_status("", 'info')
            
        except Exception as e:
            logging.error(f"Error handling update result: {e}")
            messagebox.showerror("Errore", f"Errore durante gestione aggiornamento: {str(e)}")
    
    def download_update_file(self, download_url, downloader):
        """Scarica file aggiornamento con progress"""
        try:
            import tkinter.ttk as ttk
            
            # Crea dialog progress
            progress_window = tk.Toplevel(self.root)
            progress_window.title("Download Aggiornamento")
            progress_window.geometry("400x120")
            progress_window.transient(self.root)
            progress_window.grab_set()
            
            # Centra dialog
            progress_window.update_idletasks()
            x = (progress_window.winfo_screenwidth() // 2) - (400 // 2)
            y = (progress_window.winfo_screenheight() // 2) - (120 // 2)
            progress_window.geometry(f"400x120+{x}+{y}")
            
            # Label
            label = tk.Label(
                progress_window,
                text="Download in corso...",
                font=('Segoe UI', 10)
            )
            label.pack(pady=10)
            
            # Progress bar
            progress_bar = ttk.Progressbar(
                progress_window,
                mode='indeterminate',
                length=300
            )
            progress_bar.pack(pady=10)
            progress_bar.start()
            
            # Status label
            status_label = tk.Label(
                progress_window,
                text="Connessione...",
                font=('Segoe UI', 9),
                fg='gray'
            )
            status_label.pack()
            
            def update_progress(downloaded, total):
                if total > 0:
                    percent = (downloaded * 100) // total
                    status_label.config(text=f"Scaricato: {downloaded // 1024} KB / {total // 1024} KB ({percent}%)")
                else:
                    status_label.config(text="Connessione...")
            
            def download_thread():
                try:
                    filename = download_url.split('/')[-1]
                    status_label.config(text=f"Scaricando: {filename}...")
                    
                    file_path = downloader.download_update(
                        download_url,
                        filename=filename,
                        progress_callback=update_progress
                    )
                    
                    # Chiudi dialog e mostra risultato
                    progress_window.after(0, lambda: self.handle_download_complete(file_path, downloader, progress_window))
                    
                except Exception as e:
                    logging.error(f"Error downloading: {e}")
                    progress_window.after(0, lambda: self.handle_download_error(str(e), progress_window))
            
            # Avvia download in thread
            threading.Thread(target=download_thread, daemon=True).start()
            
        except Exception as e:
            logging.error(f"Error creating download dialog: {e}")
            messagebox.showerror("Errore", f"Errore durante download: {str(e)}")
    
    def handle_download_complete(self, file_path, downloader, progress_window):
        """Gestisce completamento download"""
        progress_window.destroy()
        
        if file_path and downloader.verify_download(file_path):
            msg = (
                f"Download completato!\n\n"
                f"File: {file_path.name}\n"
                f"Posizione: {file_path.parent}\n\n"
                f"Vuoi aprire la cartella downloads?"
            )
            
            if messagebox.askyesno("Download Completato", msg):
                downloader.open_download_folder()
                
            messagebox.showinfo(
                "Installazione",
                "Per installare l'aggiornamento:\n\n"
                "1. Chiudi LAC TRANSLATE\n"
                "2. Esegui l'installer scaricato\n"
                "3. Riavvia l'applicazione"
            )
        else:
            messagebox.showerror("Errore", "Download fallito o file corrotto.")
    
    def handle_download_error(self, error_msg, progress_window):
        """Gestisce errore download"""
        progress_window.destroy()
        messagebox.showerror("Errore Download", f"Errore durante download:\n\n{error_msg}")
    
    def check_updates_on_startup(self):
        """Controlla aggiornamenti all'avvio (background, non invasivo)"""
        try:
            import json
            from datetime import datetime, timedelta
            
            # Carica configurazione
            config_file = BASE_DIR / "config" / "update_config.json"
            check_on_startup = True
            check_interval_days = 7
            
            if config_file.exists():
                try:
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                    check_on_startup = config.get('check_on_startup', True)
                    check_interval_days = config.get('check_interval_days', 7)
                    last_check_str = config.get('last_check')
                    
                    # Controlla se è passato abbastanza tempo dall'ultimo check
                    if last_check_str:
                        try:
                            last_check = datetime.fromisoformat(last_check_str)
                            days_since = (datetime.now() - last_check).days
                            if days_since < check_interval_days:
                                logging.info(f"Skipping update check (last checked {days_since} days ago)")
                                return
                        except:
                            pass
                except:
                    pass
            
            if not check_on_startup:
                return
            
            # Controlla in background (non bloccare avvio)
            def background_check():
                try:
                    from update_checker import UpdateChecker
                    
                    checker = UpdateChecker()
                    update_info = checker.check_for_updates()
                    
                    # Salva timestamp ultimo check
                    if config_file.exists():
                        try:
                            with open(config_file, 'r') as f:
                                config = json.load(f)
                        except:
                            config = {}
                    else:
                        config = {}
                    
                    config['last_check'] = datetime.now().isoformat()
                    
                    config_file.parent.mkdir(parents=True, exist_ok=True)
                    with open(config_file, 'w') as f:
                        json.dump(config, f, indent=2)
                    
                    # Notifica solo se aggiornamento disponibile
                    if update_info and update_info.get('available'):
                        latest = update_info['latest_version']
                        current = update_info['current_version']
                        release_url = update_info['release_info'].get('html_url', '')
                        
                        # Notifica non invasiva (dopo 5 secondi dall'avvio)
                        def show_notification():
                            response = messagebox.askyesno(
                                "Aggiornamento Disponibile",
                                f"Nuova versione disponibile!\n\n"
                                f"Versione corrente: {current}\n"
                                f"Nuova versione: {latest}\n\n"
                                f"Vuoi verificare gli aggiornamenti ora?"
                            )
                            if response:
                                self.check_updates()
                        
                        self.root.after(5000, show_notification)  # Dopo 5 secondi
                        
                except Exception as e:
                    logging.debug(f"Background update check failed (non-critical): {e}")
            
            # Avvia check in thread separato
            threading.Thread(target=background_check, daemon=True).start()
            
        except Exception as e:
            logging.debug(f"Error in startup update check (non-critical): {e}")
    
    def setup_drag_drop(self):
        """Setup drag and drop per file PDF"""
        try:
            # Try tkinterdnd2 (cross-platform drag & drop)
            try:
                from tkinterdnd2 import DND_FILES, TkinterDnD
                # Root deve essere già TkinterDnD.Tk() - questo è solo fallback
                # Se non è già DnD, non possiamo convertirlo qui
                # La funzionalità sarà disponibile se root è creato come TkinterDnD.Tk()
                try:
                    self.root.drop_target_register(DND_FILES)
                    self.root.dnd_bind('<<Drop>>', self.on_drop)
                    logging.info("Drag & drop enabled (tkinterdnd2)")
                except AttributeError:
                    # Root non è TkinterDnD - bind a canvas invece
                    if hasattr(self, 'original_canvas'):
                        self.original_canvas.drop_target_register(DND_FILES)
                        self.original_canvas.dnd_bind('<<Drop>>', self.on_drop)
                        logging.info("Drag & drop enabled on canvas (tkinterdnd2)")
            except ImportError:
                logging.info("Drag & drop not available (install tkinterdnd2: pip install tkinterdnd2)")
        except Exception as e:
            logging.warning(f"Could not setup drag & drop: {e}")
    
    def on_drop(self, event):
        """Handle file drop"""
        try:
            # Parse dropped files
            files = self.root.tk.splitlist(event.data)
            
            for file_path in files:
                if file_path.lower().endswith('.pdf'):
                    self.pdf_path = file_path
                    self.file_label.config(text=os.path.basename(file_path))
                    
                    # Add to recent files
                    if SETTINGS_AVAILABLE:
                        self.settings_manager.add_recent_file(file_path)
                        self.update_recent_files_menu()
                    
                    self.load_pdf()
                    break
                else:
                    messagebox.showinfo("Info", f"File non supportato: {os.path.basename(file_path)}\n\nSolo file PDF sono supportati.")
        except Exception as e:
            logging.error(f"Error handling drop: {e}")
            messagebox.showerror("Errore", f"Errore durante l'apertura del file: {str(e)}")
    
    def on_canvas_click(self, event):
        """Placeholder per canvas click (se drag & drop non disponibile)"""
        pass
    
    def show_batch_dialog(self):
        """Mostra dialog batch processing"""
        if not BATCH_AVAILABLE:
            messagebox.showinfo("Batch Processing", "Funzionalità batch processing non disponibile")
            return
        
        def translate_pdf_wrapper(input_path, output_path):
            """Wrapper per traduzione PDF singolo"""
            try:
                # Carica PDF
                doc = pymupdf.open(input_path)
                output_doc = pymupdf.open()
                
                # Traduci tutte le pagine
                translator = self.get_translator()
                rgb_color = COLOR_MAP.get(self.text_color.get(), COLOR_MAP["Rosso"])
                WHITE = pymupdf.pdfcolor["white"]
                
                for page_num in range(doc.page_count):
                    page = doc[page_num]
                    new_page = output_doc.new_page(width=page.rect.width, height=page.rect.height)
                    
                    # Estrai e traduci
                    text = self.extract_text_improved(page)
                    if text and not text.startswith("[PDF scansionato"):
                        translated = translator.translate(text)
                        
                        # Inserisci traduzione
                        new_page.draw_rect(new_page.rect, color=None, fill=WHITE)
                        new_page.insert_htmlbox(
                            new_page.rect,
                            translated,
                            css=f"""* {{
                                font-family: 'Arial', sans-serif;
                                font-size: 10pt;
                                color: rgb({int(rgb_color[0]*255)}, {int(rgb_color[1]*255)}, {int(rgb_color[2]*255)});
                                line-height: 1.4;
                            }}"""
                        )
                
                # Salva
                output_doc.save(output_path)
                doc.close()
                output_doc.close()
                
                return True
            except Exception as e:
                logging.error(f"Batch translation error: {e}")
                return False
        
        dialog = BatchDialog(self.root, translate_pdf_wrapper)
        self.root.wait_window(dialog.dialog)


def main():
    """Main entry point con splash screen"""
    # Mostra splash screen
    try:
        from splash_screen import show_splash
        
        def start_main_app():
            """Avvia app principale dopo splash"""
            root = tk.Tk()
            
            # Check argos models
            installed_packages = argostranslate.package.get_installed_packages()
            if not installed_packages:
                result = messagebox.askyesno(
                    "Modelli Argos mancanti",
                    "Nessun modello Argos Translate installato.\n\n"
                    "Vuoi scaricarli ora?\n"
                    "(richiede connessione internet, ~500MB)"
                )
                if result:
                    messagebox.showinfo("Info", "Esegui: INSTALLA_DIPENDENZE.bat\nOppure: python setup_argos_models.py")
            
            app = PDFTranslatorGUI(root)
            root.mainloop()
        
        # Mostra splash e carica app
        # Il splash gestisce il suo mainloop e transizione alla GUI principale
        show_splash(start_main_app)
    except ImportError:
        # Fallback se splash non disponibile
        root = tk.Tk()
        
        # Check argos models
        installed_packages = argostranslate.package.get_installed_packages()
        if not installed_packages:
            result = messagebox.askyesno(
                "Modelli Argos mancanti",
                "Nessun modello Argos Translate installato.\n\n"
                "Vuoi scaricarli ora?\n"
                "(richiede connessione internet, ~500MB)"
            )
            if result:
                messagebox.showinfo("Info", "Esegui: INSTALLA_DIPENDENZE.bat\nOppure: python setup_argos_models.py")
        
        app = PDFTranslatorGUI(root)
        root.mainloop()


if __name__ == "__main__":
    main()
