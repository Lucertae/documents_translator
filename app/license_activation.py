#!/usr/bin/env python3
"""
LAC TRANSLATE - License Activation Dialog
Dialog GUI per attivazione licenza
"""
import tkinter as tk
from tkinter import ttk, messagebox
import re
import sys
from pathlib import Path

# Import license manager
sys.path.insert(0, str(Path(__file__).parent))
from license_manager import get_license_manager

class LicenseActivationDialog:
    """Dialog per attivazione licenza"""
    
    def __init__(self, parent):
        self.parent = parent
        self.license_manager = get_license_manager()
        self.result = False
        
        # Crea dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Attivazione Licenza - LAC TRANSLATE")
        self.dialog.geometry("550x350")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Centra dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (550 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (350 // 2)
        self.dialog.geometry(f"550x350+{x}+{y}")
        
        # Setup UI
        self.setup_ui()
        
        # Focus su campo seriale
        self.serial_entry.focus()
    
    def setup_ui(self):
        """Setup interfaccia dialog"""
        # Header
        header_frame = ttk.Frame(self.dialog, padding="20")
        header_frame.pack(fill=tk.X)
        
        title_label = ttk.Label(
            header_frame,
            text="Attivazione Licenza",
            font=('Segoe UI', 16, 'bold')
        )
        title_label.pack()
        
        subtitle_label = ttk.Label(
            header_frame,
            text="Inserisci la tua chiave seriale per attivare LAC TRANSLATE",
            font=('Segoe UI', 9)
        )
        subtitle_label.pack(pady=(5, 0))
        
        # Separator
        ttk.Separator(self.dialog, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=20, pady=10)
        
        # Content
        content_frame = ttk.Frame(self.dialog, padding="20")
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Serial key input
        serial_frame = ttk.Frame(content_frame)
        serial_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(
            serial_frame,
            text="Chiave Seriale:",
            font=('Segoe UI', 9, 'bold')
        ).pack(anchor=tk.W)
        
        self.serial_entry = ttk.Entry(
            serial_frame,
            font=('Segoe UI', 11),
            width=40
        )
        self.serial_entry.pack(fill=tk.X, pady=(5, 0))
        self.serial_entry.bind('<KeyRelease>', self.on_serial_changed)
        self.serial_entry.bind('<Return>', lambda e: self.activate())
        
        # Format hint
        hint_label = ttk.Label(
            serial_frame,
            text="Formato: LAC-XXXX-XXXX-XXXX",
            font=('Segoe UI', 8),
            foreground='gray'
        )
        hint_label.pack(anchor=tk.W, pady=(2, 0))
        
        # Hardware ID info
        hw_frame = ttk.LabelFrame(content_frame, text="Informazioni Sistema", padding="10")
        hw_frame.pack(fill=tk.X, pady=10)
        
        hw_id = self.license_manager.hw_id
        hw_label = ttk.Label(
            hw_frame,
            text=f"ID Hardware: {hw_id}",
            font=('Courier New', 9)
        )
        hw_label.pack(anchor=tk.W)
        
        info_label = ttk.Label(
            hw_frame,
            text="La licenza è legata al tuo computer. Per trasferirla, contatta il supporto.",
            font=('Segoe UI', 8),
            foreground='gray',
            wraplength=480
        )
        info_label.pack(anchor=tk.W, pady=(5, 0))
        
        # Status
        self.status_label = ttk.Label(
            content_frame,
            text="",
            font=('Segoe UI', 9),
            foreground='green'
        )
        self.status_label.pack(pady=10)
        
        # Buttons
        button_frame = ttk.Frame(self.dialog, padding="20")
        button_frame.pack(fill=tk.X)
        
        ttk.Button(
            button_frame,
            text="Annulla",
            command=self.cancel,
            width=15
        ).pack(side=tk.RIGHT, padx=(5, 0))
        
        self.activate_button = ttk.Button(
            button_frame,
            text="Attiva Licenza",
            command=self.activate,
            width=15
        )
        self.activate_button.pack(side=tk.RIGHT)
        
        # Support info
        support_frame = ttk.Frame(self.dialog)
        support_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        support_label = ttk.Label(
            support_frame,
            text="Problemi con l'attivazione? Contatta il supporto.",
            font=('Segoe UI', 8),
            foreground='blue',
            cursor='hand2'
        )
        support_label.pack()
        support_label.bind('<Button-1>', lambda e: self.show_support())
    
    def on_serial_changed(self, event=None):
        """Callback quando cambia il seriale"""
        text = self.serial_entry.get().upper()
        # Rimuovi caratteri non validi
        text = re.sub(r'[^A-Z0-9-]', '', text)
        
        # Auto-formatta: LAC-XXXX-XXXX-XXXX
        if len(text) > 0 and not text.startswith('LAC-'):
            if text.startswith('LAC'):
                text = 'LAC-' + text[3:]
            elif not text.startswith('LAC'):
                text = 'LAC-' + text
        
        # Inserisci trattini automaticamente
        parts = text.replace('-', '')
        if len(parts) > 3:
            formatted = 'LAC-' + parts[3:7] if len(parts) > 7 else 'LAC-' + parts[3:]
            if len(parts) > 7:
                formatted += '-' + parts[7:11] if len(parts) > 11 else '-' + parts[7:]
                if len(parts) > 11:
                    formatted += '-' + parts[11:15]
            
            # Limita a formato completo
            if len(parts) > 15:
                formatted = 'LAC-' + parts[3:7] + '-' + parts[7:11] + '-' + parts[11:15]
            
            text = formatted
        
        # Aggiorna se diverso
        if text != self.serial_entry.get():
            cursor_pos = self.serial_entry.index(tk.INSERT)
            self.serial_entry.delete(0, tk.END)
            self.serial_entry.insert(0, text)
            # Ripristina cursore
            try:
                self.serial_entry.icursor(min(cursor_pos, len(text)))
            except:
                pass
        
        # Valida formato
        serial = self.serial_entry.get()
        is_valid = self.license_manager.validate_serial_key(serial)
        
        if serial and len(serial) > 4:
            if is_valid:
                self.status_label.config(
                    text="✓ Formato valido",
                    foreground='green'
                )
                self.activate_button.config(state='normal')
            else:
                self.status_label.config(
                    text="⚠ Formato non valido",
                    foreground='orange'
                )
                self.activate_button.config(state='disabled')
        else:
            self.status_label.config(text="")
            self.activate_button.config(state='disabled')
    
    def activate(self):
        """Attiva licenza"""
        serial_key = self.serial_entry.get().strip().upper()
        
        if not serial_key:
            messagebox.showwarning("Attenzione", "Inserisci una chiave seriale")
            return
        
        if not self.license_manager.validate_serial_key(serial_key):
            messagebox.showerror("Errore", "Formato chiave seriale non valido.\n\nUsa il formato: LAC-XXXX-XXXX-XXXX")
            return
        
        # Disabilita pulsante durante attivazione
        self.activate_button.config(state='disabled', text="Attivazione...")
        self.status_label.config(text="Attivazione in corso...", foreground='blue')
        self.dialog.update()
        
        # Attiva licenza
        success, message = self.license_manager.activate_license(serial_key)
        
        if success:
            self.status_label.config(text="✓ Licenza attivata con successo!", foreground='green')
            messagebox.showinfo("Successo", message)
            self.result = True
            self.dialog.after(500, self.dialog.destroy)
        else:
            self.status_label.config(text="✗ Errore durante l'attivazione", foreground='red')
            messagebox.showerror("Errore", message)
            self.activate_button.config(state='normal', text="Attiva Licenza")
    
    def cancel(self):
        """Annulla attivazione"""
        self.result = False
        self.dialog.destroy()
    
    def show_support(self):
        """Mostra informazioni supporto"""
        messagebox.showinfo(
            "Supporto",
            "Per assistenza con l'attivazione:\n\n"
            "Email: info@lucertae.com\n"
            "Includi il tuo ID Hardware nell'email:\n"
            f"{self.license_manager.hw_id}"
        )

