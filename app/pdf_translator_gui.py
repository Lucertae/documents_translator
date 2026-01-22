#!/usr/bin/env python3
"""
LAC TRANSLATE - PDF Translator GUI Desktop
Traduzione offline con Argos Translate (privacy totale)
"""
import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
from pathlib import Path
import pymupdf
import argostranslate.package
import argostranslate.translate
from PIL import Image, ImageTk
import io
import logging
import re
import fitz

# OCR imports
try:
    import pytesseract
    from pdf2image import convert_from_path
    
    # Configure Tesseract path for Windows
    if sys.platform == 'win32':
        # Try common installation paths
        tesseract_paths = [
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            r'C:\Tesseract-OCR\tesseract.exe',
        ]
        for path in tesseract_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                break
    
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    logging.warning("OCR not available - install pytesseract and pdf2image for scanned PDF support")

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
    "Originale": None,  # Use original text color
    "Nero": (0, 0, 0),
    "Rosso": (0.8, 0, 0),
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
    "Nederlands": "nl",
}

# Tesseract language codes mapping for OCR
TESSERACT_LANG_MAP = {
    "Italiano": "ita",
    "English": "eng",
    "Español": "spa",
    "Français": "fra",
    "Deutsch": "deu",
    "Português": "por",
    "Nederlands": "nld",
    "Auto": "eng",  # Default per auto-detect
}

def get_tesseract_lang(source_lang_name):
    """Ottieni codice lingua Tesseract dalla lingua UI selezionata"""
    return TESSERACT_LANG_MAP.get(source_lang_name, "eng")


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
        
        # Black & White theme colors
        self.colors = {
            'bg': '#ffffff',           # Background principale (bianco)
            'bg_dark': '#f0f0f0',      # Background più scuro (grigio chiaro)
            'bg_light': '#f8f8f8',     # Background chiaro (grigio molto chiaro)
            'accent': '#000000',       # Accent color (nero)
            'accent_hover': '#333333', # Accent hover (grigio scuro)
            'text': '#000000',         # Testo principale (nero)
            'text_dim': '#666666',     # Testo secondario (grigio)
            'border': '#cccccc',       # Bordi (grigio chiaro)
            'error': '#cc0000',        # Errori (rosso scuro)
            'success': '#006600',      # Successo (verde scuro)
            'warning': '#cc6600',      # Warning (arancione scuro)
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
        
        # Settings variables
        self.translator_type = tk.StringVar(value="Argos")
        self.source_lang = tk.StringVar(value="English")
        self.target_lang = tk.StringVar(value="Italiano")
        self.text_color = tk.StringVar(value="Originale")
        
        # Setup UI
        self.setup_ui()
        
        # Status
        self.is_translating = False
        self.update_translator_info()
        
        logging.info("LAC TRANSLATE started")
    
    def setup_style(self):
        """Setup dark theme style"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        style.configure('.',
            background=self.colors['bg'],
            foreground=self.colors['text'],
            bordercolor=self.colors['border'],
            darkcolor=self.colors['bg_dark'],
            lightcolor=self.colors['bg_light'],
            troughcolor=self.colors['bg_dark'],
            focuscolor=self.colors['accent'],
            selectbackground=self.colors['accent'],
            selectforeground=self.colors['bg'],
            fieldbackground=self.colors['bg_light'],
            font=('Segoe UI', 9)
        )
        
        # Button style
        style.configure('TButton',
            background=self.colors['accent'],
            foreground=self.colors['bg'],
            borderwidth=0,
            focuscolor='none',
            padding=(10, 5),
            font=('Segoe UI', 9, 'bold')
        )
        style.map('TButton',
            background=[('active', self.colors['accent_hover']),
                       ('pressed', self.colors['accent'])],
            foreground=[('active', self.colors['bg'])]
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
            foreground=self.colors['accent'],
            bordercolor=self.colors['border'],
            borderwidth=1,
            relief='flat',
            font=('Segoe UI', 10, 'bold')
        )
        style.configure('TLabelframe.Label',
            background=self.colors['bg'],
            foreground=self.colors['accent'],
            font=('Segoe UI', 10, 'bold')
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
        
        # Scrollbar style
        style.configure('TScrollbar',
            background=self.colors['bg_light'],
            troughcolor=self.colors['bg_dark'],
            bordercolor=self.colors['bg'],
            arrowcolor=self.colors['text'],
            borderwidth=0
        )
    
    def setup_ui(self):
        """Setup interfaccia utente"""
        
        # === TOP TOOLBAR ===
        toolbar = ttk.Frame(self.root, padding="5")
        toolbar.pack(side=tk.TOP, fill=tk.X)
        
        # File selection
        ttk.Button(toolbar, text="Apri PDF", command=self.select_pdf, width=12).pack(side=tk.LEFT, padx=2)
        self.file_label = ttk.Label(toolbar, text="Nessun file caricato", width=35)
        self.file_label.pack(side=tk.LEFT, padx=5)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Page navigation
        ttk.Button(toolbar, text="◀ Prec", command=self.prev_page, width=8).pack(side=tk.LEFT, padx=2)
        self.page_label = ttk.Label(toolbar, text="Pagina: 0/0", width=15)
        self.page_label.pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Succ ▶", command=self.next_page, width=8).pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Translation buttons
        ttk.Button(toolbar, text="Traduci Pagina", command=self.translate_current_page, width=15).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Traduci Tutto", command=self.translate_all_pages, width=15).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Salva PDF", command=self.save_pdf, width=12).pack(side=tk.LEFT, padx=2)
        
        # === SETTINGS PANEL ===
        settings_frame = ttk.LabelFrame(self.root, text="⚙ Impostazioni", padding="10")
        settings_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        
        # Row 1: Translator info
        row1 = ttk.Frame(settings_frame)
        row1.pack(fill=tk.X, pady=2)
        
        ttk.Label(row1, text="Traduttore:", font=('', 9, 'bold')).pack(side=tk.LEFT, padx=5)
        ttk.Label(row1, text="Argos Translate (offline - privacy totale)",
                 foreground=self.colors['success']).pack(side=tk.LEFT, padx=10)
        
        self.translator_info = ttk.Label(row1, text="[Offline - tutto sul tuo PC, privacy totale]",
                                        foreground=self.colors['success'])
        self.translator_info.pack(side=tk.LEFT, padx=20)
        
        # Row 2: Languages
        row2 = ttk.Frame(settings_frame)
        row2.pack(fill=tk.X, pady=2)
        
        ttk.Label(row2, text="Da:").pack(side=tk.LEFT, padx=5)
        source_combo = ttk.Combobox(row2, textvariable=self.source_lang, 
                                    values=["Auto"] + list(ARGOS_LANG_MAP.keys()),
                                    state="readonly", width=12)
        source_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(row2, text="→", font=('', 12)).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(row2, text="A:").pack(side=tk.LEFT, padx=5)
        target_combo = ttk.Combobox(row2, textvariable=self.target_lang, 
                                    values=list(ARGOS_LANG_MAP.keys()),
                                    state="readonly", width=12)
        target_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(row2, text="Colore:").pack(side=tk.LEFT, padx=20)
        color_combo = ttk.Combobox(row2, textvariable=self.text_color, 
                                   values=list(COLOR_MAP.keys()),
                                   state="readonly", width=10)
        color_combo.pack(side=tk.LEFT, padx=5)
        
        # === MAIN CONTENT - Side by side view ===
        content_frame = ttk.Frame(self.root)
        content_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Original PDF (left)
        left_frame = ttk.LabelFrame(content_frame, text="📄 Originale", padding="5")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Canvas con scrollbar verticale e orizzontale
        self.original_canvas = tk.Canvas(
            left_frame, 
            bg=self.colors['bg'], 
            highlightthickness=0,
            bd=0
        )
        left_vscroll = ttk.Scrollbar(left_frame, orient="vertical", command=self.original_canvas.yview)
        left_hscroll = ttk.Scrollbar(left_frame, orient="horizontal", command=self.original_canvas.xview)
        self.original_canvas.configure(
            yscrollcommand=left_vscroll.set,
            xscrollcommand=left_hscroll.set
        )
        
        # Grid layout per scrollbar
        left_hscroll.pack(side=tk.BOTTOM, fill=tk.X)
        left_vscroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.original_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Mouse wheel scrolling
        self.original_canvas.bind('<MouseWheel>', lambda e: self.original_canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        
        # Translated PDF (right)
        right_frame = ttk.LabelFrame(content_frame, text="🌍 Tradotto", padding="5")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        self.translated_canvas = tk.Canvas(
            right_frame, 
            bg=self.colors['bg'], 
            highlightthickness=0,
            bd=0
        )
        right_vscroll = ttk.Scrollbar(right_frame, orient="vertical", command=self.translated_canvas.yview)
        right_hscroll = ttk.Scrollbar(right_frame, orient="horizontal", command=self.translated_canvas.xview)
        self.translated_canvas.configure(
            yscrollcommand=right_vscroll.set,
            xscrollcommand=right_hscroll.set
        )
        
        # Grid layout per scrollbar
        right_hscroll.pack(side=tk.BOTTOM, fill=tk.X)
        right_vscroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.translated_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Mouse wheel scrolling
        self.translated_canvas.bind('<MouseWheel>', lambda e: self.translated_canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        
        # === STATUS BAR ===
        status_frame = tk.Frame(self.root, bg=self.colors['bg_light'], height=30)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.progress = ttk.Progressbar(status_frame, mode='indeterminate')
        
        self.status_bar = tk.Label(
            status_frame, 
            text="[OK] Pronto - LAC TRANSLATE", 
            bg=self.colors['bg_light'],
            fg=self.colors['success'],
            anchor=tk.W,
            font=('Segoe UI', 9),
            padx=10,
            pady=5
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def select_pdf(self):
        """Seleziona file PDF"""
        filename = filedialog.askopenfilename(
            title="Seleziona file PDF",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if filename:
            self.pdf_path = filename
            self.file_label.config(text=os.path.basename(filename))
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
                    "Per risultati migliori, prova con un PDF con testo selezionabile."
                )
            else:
                # Controlla se il testo è sufficiente per una buona traduzione
                text_length = len(sample_text.strip())
                if text_length > 100:
                    self.update_status(f"[OK] PDF caricato: {self.current_doc.page_count} pagine - {text_length} caratteri estratti")
                else:
                    self.update_status(f"⚠ PDF caricato: {self.current_doc.page_count} pagine - testo limitato ({text_length} caratteri)")
            
            self.display_current_page()
            logging.info(f"Loaded PDF: {self.pdf_path} ({self.current_doc.page_count} pages)")
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile caricare PDF: {str(e)}")
            logging.error(f"Failed to load PDF: {str(e)}")
    
    def display_current_page(self):
        """Mostra pagina corrente ridimensionata per adattarsi"""
        if not self.current_doc:
            return
        
        page_num = self.current_page
        self.page_label.config(text=f"Pag: {page_num + 1}/{self.current_doc.page_count}")
        
        # Display original
        page = self.current_doc[page_num]
        
        # Get canvas size first
        self.original_canvas.update_idletasks()
        canvas_width = self.original_canvas.winfo_width()
        canvas_height = self.original_canvas.winfo_height()
        
        # Calculate scale to fit horizontally
        page_rect = page.rect
        page_width = page_rect.width
        page_height = page_rect.height
        
        # Scale to fit canvas width with some margin
        scale_x = (canvas_width - 40) / page_width  # 40px margin
        scale_y = (canvas_height - 40) / page_height  # 40px margin
        scale = min(scale_x, scale_y, 2.0)  # Max 2x scale, fit to canvas
        
        # Render with calculated scale
        pix = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale))
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        photo = ImageTk.PhotoImage(img)
        
        # Clear canvas
        self.original_canvas.delete("all")
        
        # Center image
        x_center = canvas_width // 2
        y_center = 0  # Top aligned
        
        # Create image centered horizontally
        self.original_canvas.create_image(x_center, y_center, anchor=tk.N, image=photo)
        self.original_canvas.image = photo
        
        # Configure scroll region
        scroll_width = max(pix.width, canvas_width)
        scroll_height = pix.height + 20
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
        """Mostra pagina tradotta ridimensionata per adattarsi"""
        try:
            page = translated_doc[0]
            
            # Get canvas size first
            self.translated_canvas.update_idletasks()
            canvas_width = self.translated_canvas.winfo_width()
            canvas_height = self.translated_canvas.winfo_height()
            
            # Calculate scale to fit horizontally
            page_rect = page.rect
            page_width = page_rect.width
            page_height = page_rect.height
            
            # Scale to fit canvas width with some margin
            scale_x = (canvas_width - 40) / page_width  # 40px margin
            scale_y = (canvas_height - 40) / page_height  # 40px margin
            scale = min(scale_x, scale_y, 2.0)  # Max 2x scale, fit to canvas
            
            # Render with calculated scale
            pix = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale))
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            photo = ImageTk.PhotoImage(img)
            
            # Clear canvas
            self.translated_canvas.delete("all")
            
            # Center image
            x_center = canvas_width // 2
            y_center = 0  # Top aligned
            
            # Create image centered horizontally
            self.translated_canvas.create_image(x_center, y_center, anchor=tk.N, image=photo)
            self.translated_canvas.image = photo
            
            # Configure scroll region
            scroll_width = max(pix.width, canvas_width)
            scroll_height = pix.height + 20
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
    
    def get_translator(self):
        """Ottieni traduttore Argos"""
        source = "auto" if self.source_lang.get() == "Auto" else ARGOS_LANG_MAP.get(self.source_lang.get(), 'en')
        target = ARGOS_LANG_MAP.get(self.target_lang.get(), 'it')
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
        
        # Metodo 8: OCR con Tesseract se disponibile (multi-lingua)
        if OCR_AVAILABLE:
            try:
                # Determina lingua OCR dalla lingua sorgente selezionata
                ocr_lang = get_tesseract_lang(self.source_lang.get())
                logging.info(f"Attempting OCR extraction with Tesseract (lang: {ocr_lang})...")
                
                # Render page as image
                pix = page.get_pixmap(matrix=pymupdf.Matrix(2.0, 2.0))  # 2x resolution for better OCR
                # Perform OCR with language detection
                ocr_lang = get_tesseract_lang(self.source_lang.get())
                ocr_text = pytesseract.image_to_string(img, lang=ocr_lang)
                
                # Perform OCR with detected language
                ocr_text = pytesseract.image_to_string(img, lang=ocr_lang)
                if ocr_text and len(ocr_text.strip()) > 20:
                    logging.info(f"OCR successful: extracted {len(ocr_text)} characters (lang: {ocr_lang})")
                    return ocr_text.strip()
            except Exception as e:
                logging.warning(f"OCR failed: {str(e)}")
        
        # Se tutto fallisce
        logging.warning("No text found with any extraction method")
        return "[PDF scansionato - testo non estraibile automaticamente]"
    
    def translate_page(self, page_num):
        WHITE = pymupdf.pdfcolor["white"]
        color_setting = COLOR_MAP.get(self.text_color.get(), None)
        use_original_color = color_setting is None  # "Originale" maps to None
        default_color = (0, 0, 0)  # Black fallback
        translator = self.get_translator()

        new_doc = pymupdf.open()
        new_doc.insert_pdf(self.current_doc, from_page=page_num, to_page=page_num)
        page = new_doc[0]

        text_dict = page.get_text("dict")
        translated_count = 0

        # Process each block as a unit for better translation context
        for block in text_dict.get("blocks", []):
            if "lines" not in block:
                continue
            
            # Phase 1: Collect all text from block with structure info
            block_text = ""
            block_structure = []
            
            for line in block["lines"]:
                if "spans" not in line:
                    continue
                    
                line_info = {
                    'spans': [],
                    'text': ""
                }
                
                for span in line["spans"]:
                    if not span.get("text") or len(span["text"].strip()) < 1:
                        continue
                    
                    # Extract original color from span
                    color_int = span.get("color", 0)
                    r = ((color_int >> 16) & 0xFF) / 255.0
                    g = ((color_int >> 8) & 0xFF) / 255.0
                    b = (color_int & 0xFF) / 255.0
                    original_color = (r, g, b)
                    
                    span_info = {
                        'bbox': span["bbox"],
                        'text': span["text"],
                        'size': span.get("size", 11),
                        'font': span.get("font", ""),
                        'original_length': len(span["text"]),
                        'original_color': original_color
                    }
                    line_info['spans'].append(span_info)
                    line_info['text'] += span["text"]
                    block_text += span["text"]
                
                if line_info['spans']:
                    block_structure.append(line_info)
                    block_text += " "  # Space between lines
            
            if not block_text.strip():
                continue
            
            # Phase 2: Translate entire block for full context
            try:
                translated_block = translator.translate(block_text.strip())
                if not translated_block or not translated_block.strip():
                    continue
                
                # Phase 3: Distribute translation across original layout
                translated_words = translated_block.split()
                word_idx = 0
                
                for line_info in block_structure:
                    for span_info in line_info['spans']:
                        bbox = span_info['bbox']
                        original_text = span_info['text']
                        
                        # Clear original text
                        page.draw_rect(bbox, color=None, fill=WHITE)
                        
                        # Calculate how many words fit in this span
                        bbox_width = bbox[2] - bbox[0]
                        
                        if word_idx >= len(translated_words):
                            break
                        
                        # Collect words for this span
                        span_words = []
                        original_word_count = len(original_text.split())
                        
                        # Take proportional number of words (at least 1)
                        words_to_take = max(1, original_word_count)
                        
                        for _ in range(words_to_take):
                            if word_idx < len(translated_words):
                                span_words.append(translated_words[word_idx])
                                word_idx += 1
                            else:
                                break
                        
                        if not span_words:
                            continue
                        
                        span_translated = " ".join(span_words)
                        
                        # Calculate if text fits, adjust font size if needed
                        font_size = span_info['size']
                        estimated_width = len(span_translated) * (font_size * 0.6)
                        
                        if estimated_width > bbox_width and bbox_width > 10:
                            # Reduce font size to fit
                            font_size = max(6, (bbox_width / len(span_translated)) * 1.5)
                        
                        # Determine color: original or selected
                        if use_original_color:
                            rgb_color = span_info.get('original_color', default_color)
                        else:
                            rgb_color = color_setting if color_setting else default_color
                        
                        # Insert translated text
                        try:
                            is_bold = 'Bold' in span_info['font']
                            is_italic = 'Italic' in span_info['font']
                            
                            page.insert_htmlbox(
                                bbox,
                                span_translated,
                                css=f"""* {{
                                    font-family: sans-serif;
                                    font-size: {font_size}pt;
                                    color: rgb({int(rgb_color[0]*255)}, {int(rgb_color[1]*255)}, {int(rgb_color[2]*255)});
                                    font-weight: {'bold' if is_bold else 'normal'};
                                    font-style: {'italic' if is_italic else 'normal'};
                                    line-height: 1.2;
                                }}"""
                            )
                            translated_count += 1
                        except Exception as e:
                            logging.warning(f"Failed to insert text in bbox: {str(e)}")
                
            except Exception as e:
                logging.warning(f"Translation failed for block: {str(e)}")
                continue

        # If not extracted text, use OCR fallback
        if translated_count == 0 and OCR_AVAILABLE:
            try:
                pix = page.get_pixmap(matrix=pymupdf.Matrix(2.0, 2.0))
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                hocr = pytesseract.image_to_pdf_or_hocr(img, extension='hocr')
                html = hocr.decode("utf-8")

                # Extracting only visible text from hOCR
                clean_text = re.sub(r'<[^>]+>', ' ', html)
                clean_text = re.sub(r'\s+', ' ', clean_text).strip()

                if len(clean_text) > 20:
                    translated_text = translator.translate(clean_text)
                    # For OCR fallback, use black as default (no original color available)
                    ocr_color = color_setting if color_setting else default_color
                    page.draw_rect(page.rect, color=None, fill=WHITE)
                    page.insert_htmlbox(
                        page.rect,
                        translated_text,
                        css=f"""* {{
                            font-family: sans-serif;
                            font-size: 10pt;
                            color: rgb({int(ocr_color[0]*255)}, {int(ocr_color[1]*255)}, {int(ocr_color[2]*255)});
                        }}"""
                    )
                    translated_count += 1
            except Exception as e:
                logging.error(f"OCR layout translation failed: {str(e)}")

        logging.info(f"Page {page_num + 1}: translated {translated_count} spans")
        return new_doc
    
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
    
    def format_ocr_text(self, translated_chunks):
        """Formatta il testo OCR tradotto per mantenere la struttura"""
        full_text = "\n\n".join(translated_chunks)
        
        # Cerca di identificare sezioni e sottosezioni
        lines = full_text.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                formatted_lines.append('<p>&nbsp;</p>')
                continue
            
            # Identifica sezioni principali (numeri seguiti da punto)
            if re.match(r'^\d+\.\s+[A-Z]', line):
                formatted_lines.append(f'<div class="section">{line}</div>')
            # Identifica sottosezioni (numeri con decimali)
            elif re.match(r'^\d+\.\d+', line):
                formatted_lines.append(f'<div class="subsection">{line}</div>')
            # Identifica elementi di lista (lettere o numeri con parentesi)
            elif re.match(r'^[a-zA-Z]\)\s+', line) or re.match(r'^\d+\)\s+', line):
                formatted_lines.append(f'<div class="list-item">{line}</div>')
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
                self.progress.pack(side=tk.BOTTOM, fill=tk.X, before=self.status_bar)
                self.progress.start(10)
                
                translated_doc = self.translate_page(self.current_page)
                self.translated_pages[self.current_page] = translated_doc
                
                self.display_translated_page(translated_doc)
                
                self.progress.stop()
                self.progress.pack_forget()
                self.update_status(f"[OK] Pagina {self.current_page + 1} tradotta")
                
            except Exception as e:
                self.progress.stop()
                self.progress.pack_forget()
                messagebox.showerror("Errore", f"Traduzione fallita: {str(e)}")
                logging.error(f"Translation failed: {str(e)}")
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
                self.progress.pack(side=tk.BOTTOM, fill=tk.X, before=self.status_bar)
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
                self.update_status(f"[OK] Tradotte tutte le {total_pages} pagine!")
                messagebox.showinfo("Completato", f"[OK] Tradotte tutte le {total_pages} pagine!")
                
            except Exception as e:
                self.progress.stop()
                self.progress.pack_forget()
                messagebox.showerror("Errore", f"Traduzione fallita: {str(e)}")
                logging.error(f"Translation failed: {str(e)}")
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
                
                self.update_status(f"[OK] Salvato: {os.path.basename(output_path)}")
                logging.info(f"Saved translated PDF: {output_path}")
                messagebox.showinfo("Successo", f"[OK] PDF salvato:\n{output_path}")
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
        if message.startswith('[OK]') or 'completat' in message.lower() or 'salvat' in message.lower():
            status_type = 'success'
        elif message.startswith('✗') or 'error' in message.lower() or 'fallita' in message.lower():
            status_type = 'error'
        elif message.startswith('⏳') or 'traduzione' in message.lower() or 'salvataggio' in message.lower():
            status_type = 'progress'
        elif message.startswith('⚠') or 'attenzione' in message.lower():
            status_type = 'warning'
        
        self.status_bar.config(text=message, fg=color_map.get(status_type, self.colors['text']))
        self.root.update_idletasks()


def main():
    """Main entry point"""
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
