#!/usr/bin/env python3
"""
LAC TRANSLATE - Settings Dialog
Dialog GUI per impostazioni/preferenze utente
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sys
from pathlib import Path

# Import settings manager
sys.path.insert(0, str(Path(__file__).parent))
from settings_manager import get_settings_manager

# Language codes per Argos
ARGOS_LANG_MAP = {
    "Italiano": "it",
    "English": "en",
    "Español": "es",
    "Français": "fr",
    "Deutsch": "de",
    "Português": "pt",
    "Русский": "ru",
}

COLOR_MAP = {
    "Rosso": (0.8, 0, 0),
    "Nero": (0, 0, 0),
    "Blu": (0, 0, 0.8),
    "Verde": (0, 0.5, 0),
    "Viola": (0.5, 0, 0.5),
}

class SettingsDialog:
    """Dialog per impostazioni/preferenze"""
    
    def __init__(self, parent):
        self.parent = parent
        self.settings_manager = get_settings_manager()
        self.result = False
        
        # Crea dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Impostazioni - LAC TRANSLATE")
        self.dialog.geometry("600x500")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Centra dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (500 // 2)
        self.dialog.geometry(f"600x500+{x}+{y}")
        
        # Variables
        self.translator_type = tk.StringVar(value=self.settings_manager.get('translator_type', 'Google'))
        self.source_lang = tk.StringVar(value=self.settings_manager.get('source_lang', 'English'))
        self.target_lang = tk.StringVar(value=self.settings_manager.get('target_lang', 'Italiano'))
        self.text_color = tk.StringVar(value=self.settings_manager.get('text_color', 'Rosso'))
        self.output_dir = tk.StringVar(value=self.settings_manager.get('output_dir', ''))
        self.logs_dir = tk.StringVar(value=self.settings_manager.get('logs_dir', ''))
        
        # Setup UI
        self.setup_ui()
    
    def setup_ui(self):
        """Setup interfaccia dialog"""
        # Notebook per tabs
        notebook = ttk.Notebook(self.dialog, padding="10")
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Tab: Traduzione
        translation_frame = ttk.Frame(notebook, padding="10")
        notebook.add(translation_frame, text="Traduzione")
        self.setup_translation_tab(translation_frame)
        
        # Tab: File e Cartelle
        files_frame = ttk.Frame(notebook, padding="10")
        notebook.add(files_frame, text="File e Cartelle")
        self.setup_files_tab(files_frame)
        
        # Tab: Avanzate
        advanced_frame = ttk.Frame(notebook, padding="10")
        notebook.add(advanced_frame, text="Avanzate")
        self.setup_advanced_tab(advanced_frame)
        
        # Buttons
        button_frame = ttk.Frame(self.dialog, padding="10")
        button_frame.pack(fill=tk.X)
        
        ttk.Button(
            button_frame,
            text="Annulla",
            command=self.cancel,
            width=15
        ).pack(side=tk.RIGHT, padx=(5, 0))
        
        ttk.Button(
            button_frame,
            text="Ripristina Default",
            command=self.reset_defaults,
            width=15
        ).pack(side=tk.RIGHT, padx=(5, 0))
        
        ttk.Button(
            button_frame,
            text="Salva",
            command=self.save,
            width=15
        ).pack(side=tk.RIGHT)
    
    def setup_translation_tab(self, parent):
        """Setup tab traduzione"""
        # Translator type
        translator_frame = ttk.LabelFrame(parent, text="Motore Traduzione", padding="10")
        translator_frame.pack(fill=tk.X, pady=5)
        
        ttk.Radiobutton(
            translator_frame,
            text="Google Translate (online)",
            variable=self.translator_type,
            value="Google"
        ).pack(anchor=tk.W, pady=2)
        
        ttk.Radiobutton(
            translator_frame,
            text="Argos Translate (offline - privacy totale)",
            variable=self.translator_type,
            value="Argos"
        ).pack(anchor=tk.W, pady=2)
        
        # Languages
        lang_frame = ttk.LabelFrame(parent, text="Lingue", padding="10")
        lang_frame.pack(fill=tk.X, pady=5)
        
        row1 = ttk.Frame(lang_frame)
        row1.pack(fill=tk.X, pady=5)
        
        ttk.Label(row1, text="Da:", width=10).pack(side=tk.LEFT)
        source_combo = ttk.Combobox(
            row1,
            textvariable=self.source_lang,
            values=["Auto"] + list(ARGOS_LANG_MAP.keys()),
            state="readonly",
            width=20
        )
        source_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(row1, text="→", font=('', 12)).pack(side=tk.LEFT, padx=10)
        
        ttk.Label(row1, text="A:", width=10).pack(side=tk.LEFT)
        target_combo = ttk.Combobox(
            row1,
            textvariable=self.target_lang,
            values=list(ARGOS_LANG_MAP.keys()),
            state="readonly",
            width=20
        )
        target_combo.pack(side=tk.LEFT, padx=5)
        
        # Color
        color_frame = ttk.LabelFrame(parent, text="Colore Testo Tradotto", padding="10")
        color_frame.pack(fill=tk.X, pady=5)
        
        color_combo = ttk.Combobox(
            color_frame,
            textvariable=self.text_color,
            values=list(COLOR_MAP.keys()),
            state="readonly",
            width=20
        )
        color_combo.pack(anchor=tk.W, pady=5)
    
    def setup_files_tab(self, parent):
        """Setup tab file e cartelle"""
        # Output directory
        output_frame = ttk.LabelFrame(parent, text="Cartella Output", padding="10")
        output_frame.pack(fill=tk.X, pady=5)
        
        output_row = ttk.Frame(output_frame)
        output_row.pack(fill=tk.X)
        
        ttk.Entry(output_row, textvariable=self.output_dir, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(
            output_row,
            text="Sfoglia...",
            command=lambda: self.browse_directory(self.output_dir, "Seleziona cartella output")
        ).pack(side=tk.RIGHT)
        
        # Logs directory
        logs_frame = ttk.LabelFrame(parent, text="Cartella Logs", padding="10")
        logs_frame.pack(fill=tk.X, pady=5)
        
        logs_row = ttk.Frame(logs_frame)
        logs_row.pack(fill=tk.X)
        
        ttk.Entry(logs_row, textvariable=self.logs_dir, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(
            logs_row,
            text="Sfoglia...",
            command=lambda: self.browse_directory(self.logs_dir, "Seleziona cartella logs")
        ).pack(side=tk.RIGHT)
    
    def setup_advanced_tab(self, parent):
        """Setup tab avanzate"""
        info_label = ttk.Label(
            parent,
            text="Impostazioni avanzate - da implementare in futuro",
            font=('Segoe UI', 9)
        )
        info_label.pack(pady=20)
        
        # Placeholder per future impostazioni avanzate
        # - Cache settings
        # - OCR settings avanzati
        # - Performance tuning
        # - Debug mode
    
    def browse_directory(self, var, title):
        """Apri dialog selezione directory"""
        dir_path = filedialog.askdirectory(title=title)
        if dir_path:
            var.set(dir_path)
    
    def save(self):
        """Salva impostazioni"""
        # Salva tutte le impostazioni
        self.settings_manager.set('translator_type', self.translator_type.get())
        self.settings_manager.set('source_lang', self.source_lang.get())
        self.settings_manager.set('target_lang', self.target_lang.get())
        self.settings_manager.set('text_color', self.text_color.get())
        self.settings_manager.set('output_dir', self.output_dir.get())
        self.settings_manager.set('logs_dir', self.logs_dir.get())
        
        self.settings_manager.save_settings()
        
        messagebox.showinfo("Impostazioni", "Impostazioni salvate con successo!")
        self.result = True
        self.dialog.destroy()
    
    def reset_defaults(self):
        """Ripristina impostazioni di default"""
        result = messagebox.askyesno(
            "Conferma",
            "Vuoi ripristinare tutte le impostazioni ai valori di default?"
        )
        
        if result:
            self.settings_manager.reset_to_defaults()
            
            # Reload UI
            self.translator_type.set(self.settings_manager.get('translator_type', 'Google'))
            self.source_lang.set(self.settings_manager.get('source_lang', 'English'))
            self.target_lang.set(self.settings_manager.get('target_lang', 'Italiano'))
            self.text_color.set(self.settings_manager.get('text_color', 'Rosso'))
            self.output_dir.set(self.settings_manager.get('output_dir', ''))
            self.logs_dir.set(self.settings_manager.get('logs_dir', ''))
            
            messagebox.showinfo("Impostazioni", "Impostazioni ripristinate ai valori di default")
    
    def cancel(self):
        """Annulla modifiche"""
        self.result = False
        self.dialog.destroy()

