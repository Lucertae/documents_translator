#!/usr/bin/env python3
"""
LAC TRANSLATE - Launcher
Wrapper per avviare l'applicazione con gestione errori migliorata
"""
import sys
import os
from pathlib import Path

def main():
    """Avvia l'applicazione principale"""
    try:
        # Assicurati che siamo nella directory corretta
        app_dir = Path(__file__).parent
        project_root = app_dir.parent
        os.chdir(project_root)
        
        # Aggiungi app directory al path per import
        if str(app_dir) not in sys.path:
            sys.path.insert(0, str(app_dir))
        
        # Importa e avvia GUI
        from pdf_translator_gui import main as gui_main
        gui_main()
        
    except ImportError as e:
        # Errore import - mostra messaggio
        try:
            import tkinter as tk
            from tkinter import messagebox
            
            root = tk.Tk()
            root.withdraw()  # Nascondi finestra principale
            messagebox.showerror(
                "Errore Importazione",
                f"Errore durante il caricamento dell'applicazione:\n\n{str(e)}\n\n"
                "Verifica che tutte le dipendenze siano installate:\n"
                "pip install -r requirements.txt"
            )
            root.destroy()
        except:
            print(f"Errore importazione: {e}")
        sys.exit(1)
        
    except Exception as e:
        # Altri errori
        try:
            import tkinter as tk
            from tkinter import messagebox
            
            root = tk.Tk()
            root.withdraw()  # Nascondi finestra principale
            messagebox.showerror(
                "Errore Avvio",
                f"Errore durante l'avvio dell'applicazione:\n\n{str(e)}\n\n"
                "Controlla i log in: logs/pdf_translator.log"
            )
            root.destroy()
        except:
            print(f"Errore avvio: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

