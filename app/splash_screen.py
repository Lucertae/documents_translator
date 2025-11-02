#!/usr/bin/env python3
"""
LAC TRANSLATE - Splash Screen
Loading page all'avvio dell'applicazione
"""
import tkinter as tk
from tkinter import ttk
from pathlib import Path
import threading
import time

class SplashScreen:
    """Splash screen con progress bar e logo"""
    
    def __init__(self):
        self.splash = tk.Tk()
        self.splash.title("LAC TRANSLATE")
        self.splash.geometry("500x350")
        self.splash.resizable(False, False)
        
        # Centro la finestra
        self.splash.update_idletasks()
        x = (self.splash.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.splash.winfo_screenheight() // 2) - (350 // 2)
        self.splash.geometry(f"500x350+{x}+{y}")
        
        # Assicura che la finestra appaia sempre in primo piano
        self.splash.attributes('-topmost', True)
        
        # Rimuovi bordi della finestra (opzionale, per look moderno)
        # self.splash.overrideredirect(True)
        
        # Colori moderni
        bg_color = '#ffffff'
        accent_color = '#2563eb'
        text_color = '#1f2937'
        text_dim = '#6b7280'
        
        self.splash.configure(bg=bg_color)
        
        # Logo/Title area
        title_frame = tk.Frame(self.splash, bg=bg_color)
        title_frame.pack(fill=tk.X, pady=(40, 20))
        
        # Titolo principale
        title_label = tk.Label(
            title_frame,
            text="LAC TRANSLATE",
            font=('Segoe UI', 28, 'bold'),
            fg=accent_color,
            bg=bg_color
        )
        title_label.pack()
        
        # Sottotitolo
        subtitle_label = tk.Label(
            title_frame,
            text="Professional PDF Translator",
            font=('Segoe UI', 12),
            fg=text_dim,
            bg=bg_color
        )
        subtitle_label.pack(pady=(5, 0))
        
        # Status label
        self.status_label = tk.Label(
            self.splash,
            text="Inizializzazione...",
            font=('Segoe UI', 10),
            fg=text_color,
            bg=bg_color
        )
        self.status_label.pack(pady=(20, 10))
        
        # Progress bar
        progress_frame = tk.Frame(self.splash, bg=bg_color)
        progress_frame.pack(fill=tk.X, padx=60, pady=10)
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TProgressbar",
            thickness=20,
            troughcolor='#e5e7eb',
            background=accent_color,
            borderwidth=0,
            lightcolor=accent_color,
            darkcolor=accent_color
        )
        
        self.progress = ttk.Progressbar(
            progress_frame,
            mode='indeterminate',
            style="TProgressbar",
            length=380
        )
        self.progress.pack(fill=tk.X)
        self.progress.start(10)
        
        # Rimuovi versione - non necessaria
        
        # Forza visualizzazione immediata
        self.splash.update_idletasks()
        self.splash.update()
    
    def update_status(self, text: str):
        """Aggiorna testo status"""
        self.status_label.config(text=text)
        self.splash.update()
    
    def destroy(self):
        """Chiude splash screen"""
        self.progress.stop()
        self.splash.destroy()
    
    def show(self):
        """Mostra splash screen - forza visualizzazione immediata"""
        self.splash.deiconify()
        self.splash.lift()
        self.splash.attributes('-topmost', True)
        self.splash.update_idletasks()
        self.splash.update()
        self.splash.focus_force()
    
    def hide(self):
        """Nasconde splash screen"""
        self.splash.withdraw()

def show_splash(callback=None):
    """
    Mostra splash screen e carica app in background
    BEST PRACTICE: Carica in thread, poi apri GUI nel main thread con after()
    
    Args:
        callback: Funzione da chiamare dopo il caricamento (dovrebbe aprire GUI principale)
    """
    splash = SplashScreen()
    
    # Forza visualizzazione IMMEDIATA dello splash
    splash.show()
    splash.splash.update_idletasks()
    splash.splash.update()
    
    # Traccia tempo di inizio per garantire minimo tempo di visualizzazione
    import time as time_module
    start_time = time_module.time()
    min_display_time = 1.5  # Minimo 1.5 secondi di visualizzazione
    
    # Flag per tracciare quando caricamento è completo
    loading_done = threading.Event()
    loading_success = [False]
    error_message = [None]
    
    def load_app():
        """Carica app in background (NON apre GUI qui - non thread-safe)"""
        try:
            # Simula caricamento iniziale - tempi più realistici
            splash.update_status("Caricamento moduli...")
            time.sleep(0.5)
            
            splash.update_status("Inizializzazione OCR...")
            time.sleep(0.5)
            
            splash.update_status("Preparazione interfaccia...")
            time.sleep(0.4)
            
            splash.update_status("Quasi pronto...")
            time.sleep(0.3)
            
            # Caricamento completato con successo
            loading_success[0] = True
            
            # Assicurati che sia passato il tempo minimo prima di segnalare completamento
            elapsed = time_module.time() - start_time
            if elapsed < min_display_time:
                time.sleep(min_display_time - elapsed)
            
            loading_done.set()
            
        except Exception as e:
            # Errore durante caricamento
            error_message[0] = str(e)
            loading_success[0] = False
            
            # Assicurati che sia passato il tempo minimo
            elapsed = time_module.time() - start_time
            if elapsed < min_display_time:
                time.sleep(min_display_time - elapsed)
            
            loading_done.set()
    
    def check_loading_status():
        """Controlla periodicamente se caricamento è completo"""
        if loading_done.is_set():
            # Caricamento completo - chiudi splash e apri GUI
            if loading_success[0]:
                # Caricamento OK - chiudi splash e apri GUI principale
                if callback:
                    try:
                        # Ferma progress bar
                        splash.progress.stop()
                        splash.update_status("Avvio applicazione...")
                        splash.splash.update()
                        time.sleep(0.1)  # Piccola pausa per mostrare messaggio finale
                        
                        # Nascondi splash
                        splash.hide()
                        
                        # Esci dal mainloop dello splash PRIMA di aprire GUI
                        splash.splash.quit()
                        splash.splash.destroy()
                        
                        # Ora apri GUI principale (crea nuovo Tk() con suo mainloop)
                        callback()
                    except Exception as e:
                        # Errore apertura GUI
                        try:
                            splash.destroy()
                        except:
                            pass
                        import tkinter.messagebox as mb
                        mb.showerror("Errore", f"Errore apertura applicazione:\n{str(e)}")
                else:
                    splash.destroy()
            else:
                # Errore durante caricamento
                splash.destroy()
                import tkinter.messagebox as mb
                if error_message[0]:
                    mb.showerror("Errore", f"Errore caricamento:\n{error_message[0]}")
                else:
                    mb.showerror("Errore", "Errore sconosciuto durante caricamento")
        else:
            # Controlla ancora dopo 100ms
            splash.splash.after(100, check_loading_status)
    
    # PRIMA forza visualizzazione completa, POI avvia caricamento
    splash.splash.update_idletasks()
    splash.splash.update()
    
    # Avvia caricamento in thread separato
    load_thread = threading.Thread(target=load_app, daemon=True)
    
    # Piccolo delay per assicurare che splash sia completamente visibile prima di iniziare
    splash.splash.after(100, lambda: load_thread.start())
    
    # Avvia controllo periodico stato caricamento (dopo aver mostrato splash)
    splash.splash.after(150, check_loading_status)
    
    # Avvia mainloop dello splash (rimane attivo finché splash non viene distrutto)
    splash.splash.mainloop()
    
    return splash

