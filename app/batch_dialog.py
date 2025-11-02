#!/usr/bin/env python3
"""
LAC TRANSLATE - Batch Processing Dialog
Dialog GUI per processamento batch cartelle PDF
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sys
from pathlib import Path
import threading

# Import batch processor
sys.path.insert(0, str(Path(__file__).parent))
from batch_processor import BatchProcessor

class BatchDialog:
    """Dialog per processamento batch"""
    
    def __init__(self, parent, translate_pdf_func):
        """
        Inizializza dialog batch
        
        Args:
            parent: Parent window
            translate_pdf_func: Funzione per tradurre un singolo PDF (input_path, output_path) -> bool
        """
        self.parent = parent
        self.translate_pdf_func = translate_pdf_func
        self.processing = False
        
        # Crea dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Batch Processing - LAC TRANSLATE")
        self.dialog.geometry("600x400")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Centra dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (400 // 2)
        self.dialog.geometry(f"600x400+{x}+{y}")
        
        # Setup UI
        self.setup_ui()
    
    def setup_ui(self):
        """Setup interfaccia dialog"""
        # Header
        header_frame = ttk.Frame(self.dialog, padding="20")
        header_frame.pack(fill=tk.X)
        
        title_label = ttk.Label(
            header_frame,
            text="Batch Processing",
            font=('Segoe UI', 16, 'bold')
        )
        title_label.pack()
        
        subtitle_label = ttk.Label(
            header_frame,
            text="Traduci tutti i PDF in una cartella",
            font=('Segoe UI', 9)
        )
        subtitle_label.pack(pady=(5, 0))
        
        # Separator
        ttk.Separator(self.dialog, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=20, pady=10)
        
        # Content
        content_frame = ttk.Frame(self.dialog, padding="20")
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Input directory
        input_frame = ttk.LabelFrame(content_frame, text="Cartella Input", padding="10")
        input_frame.pack(fill=tk.X, pady=5)
        
        self.input_dir = tk.StringVar()
        input_row = ttk.Frame(input_frame)
        input_row.pack(fill=tk.X)
        
        ttk.Entry(input_row, textvariable=self.input_dir, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(
            input_row,
            text="Sfoglia...",
            command=lambda: self.browse_directory(self.input_dir, "Seleziona cartella con PDF")
        ).pack(side=tk.RIGHT)
        
        # Output directory
        output_frame = ttk.LabelFrame(content_frame, text="Cartella Output", padding="10")
        output_frame.pack(fill=tk.X, pady=5)
        
        self.output_dir = tk.StringVar()
        output_row = ttk.Frame(output_frame)
        output_row.pack(fill=tk.X)
        
        ttk.Entry(output_row, textvariable=self.output_dir, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(
            output_row,
            text="Sfoglia...",
            command=lambda: self.browse_directory(self.output_dir, "Seleziona cartella output")
        ).pack(side=tk.RIGHT)
        
        # Progress
        progress_frame = ttk.LabelFrame(content_frame, text="Progresso", padding="10")
        progress_frame.pack(fill=tk.X, pady=5)
        
        self.progress_var = tk.StringVar(value="Pronto")
        ttk.Label(progress_frame, textvariable=self.progress_var, font=('Segoe UI', 9)).pack(anchor=tk.W)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=(5, 0))
        
        # Log
        log_frame = ttk.LabelFrame(content_frame, text="Log", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_text = tk.Text(log_frame, height=8, wrap=tk.WORD, font=('Consolas', 9))
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Buttons
        button_frame = ttk.Frame(self.dialog, padding="20")
        button_frame.pack(fill=tk.X)
        
        ttk.Button(
            button_frame,
            text="Annulla",
            command=self.cancel,
            width=15
        ).pack(side=tk.RIGHT, padx=(5, 0))
        
        self.start_button = ttk.Button(
            button_frame,
            text="Inizia Batch Processing",
            command=self.start_processing,
            width=20
        )
        self.start_button.pack(side=tk.RIGHT)
    
    def browse_directory(self, var, title):
        """Apri dialog selezione directory"""
        dir_path = filedialog.askdirectory(title=title)
        if dir_path:
            var.set(dir_path)
    
    def log(self, message):
        """Aggiungi messaggio al log"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.dialog.update_idletasks()
    
    def start_processing(self):
        """Avvia processamento batch"""
        if self.processing:
            return
        
        input_path = self.input_dir.get()
        output_path = self.output_dir.get()
        
        if not input_path or not os.path.isdir(input_path):
            messagebox.showerror("Errore", "Seleziona una cartella input valida")
            return
        
        if not output_path:
            messagebox.showerror("Errore", "Seleziona una cartella output")
            return
        
        # Crea processor
        def translator_wrapper(input_file, output_file):
            """Wrapper per funzione traduzione"""
            try:
                return self.translate_pdf_func(input_file, output_file)
            except Exception as e:
                self.log(f"Errore traduzione {Path(input_file).name}: {str(e)}")
                return False
        
        processor = BatchProcessor(input_path, output_path, translator_wrapper)
        
        # Trova file PDF
        pdf_files = processor.find_pdf_files()
        if not pdf_files:
            messagebox.showinfo("Info", "Nessun file PDF trovato nella cartella input")
            return
        
        # Conferma
        result = messagebox.askyesno(
            "Conferma",
            f"Trovati {len(pdf_files)} file PDF.\n\n"
            f"Vuoi procedere con la traduzione batch?"
        )
        
        if not result:
            return
        
        # Avvia processamento in thread separato
        self.processing = True
        self.start_button.config(state='disabled', text="Processing...")
        self.log_text.delete(1.0, tk.END)
        
        def process_thread():
            try:
                def progress_cb(processed, total, current_file):
                    self.progress_bar['maximum'] = total
                    self.progress_bar['value'] = processed
                    self.progress_var.set(f"Processing {processed}/{total}: {current_file}")
                    self.log(f"[{processed}/{total}] {current_file}")
                    self.dialog.update_idletasks()
                
                def error_cb(file, error):
                    self.log(f"✗ ERRORE: {file.name} - {error}")
                
                # Processa
                results = processor.process_batch(progress_cb, error_cb)
                
                # Mostra risultati
                self.dialog.after(0, lambda: self.show_results(results))
                
            except Exception as e:
                self.dialog.after(0, lambda: messagebox.showerror("Errore", f"Errore batch processing: {str(e)}"))
            finally:
                self.processing = False
                self.dialog.after(0, lambda: self.start_button.config(state='normal', text="Inizia Batch Processing"))
        
        threading.Thread(target=process_thread, daemon=True).start()
    
    def show_results(self, results):
        """Mostra risultati processamento"""
        self.progress_bar['value'] = results['processed']
        
        message = (
            f"Batch Processing Completato!\n\n"
            f"Totale file: {results['total']}\n"
            f"Tradotti: {results['processed']}\n"
            f"Falliti: {results['failed']}\n"
            f"Tasso successo: {(results['processed']/results['total']*100):.1f}%"
        )
        
        messagebox.showinfo("Completato", message)
        self.log(f"\n✓ Completato: {results['processed']}/{results['total']} tradotti")
    
    def cancel(self):
        """Annulla"""
        if self.processing:
            if not messagebox.askyesno("Conferma", "Il processamento è in corso. Vuoi interrompere?"):
                return
        self.dialog.destroy()

