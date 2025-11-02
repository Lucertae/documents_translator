# LAC TRANSLATE - Installazione Multi-Piattaforma

LAC TRANSLATE supporta **Windows, macOS e Linux**.

## 🪟 Windows

### Installazione Automatica (Raccomandato)

1. Scarica `LAC_Translate_v2.0_Setup.exe`
2. Esegui l'installer
3. Segui il wizard di installazione
4. Avvia dal desktop o menu Start
5. Inserisci la chiave seriale all'avvio

### Installazione Manuale

1. Estrai `LAC_Translate.exe` dalla distribuzione ZIP
2. Copia in una directory (es. `C:\Program Files\LAC TRANSLATE`)
3. Installa dipendenze: `INSTALLA_DIPENDENZE.bat`
4. Per OCR: `INSTALLA_OCR.bat`

## 🍎 macOS

### Installazione con App Bundle (.dmg)

1. Scarica `LAC_Translate_v2.0.0_macOS.dmg`
2. Apri il file .dmg
3. Trascina `LAC_Translate.app` nella cartella Applications
4. Esegui l'applicazione (potrebbe richiedere autorizzazione in Preferenze di Sistema)
5. Inserisci la chiave seriale all'avvio

### Installazione Manuale

1. Installa Python 3.8+ da [python.org](https://www.python.org/downloads/)
2. Apri Terminal
3. Naviga nella directory del progetto
4. Esegui: `chmod +x INSTALL_MACOS.sh && ./INSTALL_MACOS.sh`
5. Avvia: `python3 app/pdf_translator_gui.py`

**Note macOS:**
- Potrebbe richiedere autorizzazione per aprire app da sviluppatori non identificati
- Vai in Preferenze di Sistema → Sicurezza → Autorizza

## 🐧 Linux

### Installazione con Pacchetto .deb (Debian/Ubuntu)

1. Scarica `lac-translate_2.0.0_amd64.deb`
2. Installa:
   ```bash
   sudo dpkg -i lac-translate_2.0.0_amd64.deb
   ```
3. Se ci sono dipendenze mancanti:
   ```bash
   sudo apt-get install -f
   ```
4. Avvia: `lac-translate` dalla terminale o dal menu applicazioni

### Installazione Manuale

1. Installa Python 3.8+ e pip:
   ```bash
   sudo apt-get install python3 python3-pip python3-tk
   ```
   (Per Fedora/RHEL: `sudo dnf install python3 python3-pip python3-tkinter`)

2. Installa Tesseract OCR (opzionale ma consigliato):
   ```bash
   sudo apt-get install tesseract-ocr
   ```

3. Naviga nella directory del progetto

4. Esegui script installazione:
   ```bash
   chmod +x INSTALL_LINUX.sh
   ./INSTALL_LINUX.sh
   ```

5. Avvia:
   ```bash
   python3 app/pdf_translator_gui.py
   ```

**Note Linux:**
- Per distribuzioni basate su RPM (Fedora, RHEL), usa `yum` o `dnf` invece di `apt-get`
- Assicurati di avere tkinter installato per la GUI
- Alcune distribuzioni potrebbero richiedere pacchetti aggiuntivi

## 🔑 Attivazione Licenza

### Tutte le Piattaforme

1. All'avvio, si aprirà il dialog di attivazione licenza
2. Inserisci la chiave seriale nel formato: `LAC-XXXX-XXXX-XXXX`
3. Clicca "Attiva Licenza"
4. La licenza è legata all'hardware del computer

**Note:**
- La licenza funziona solo sul computer su cui viene attivata
- Per trasferire la licenza, contatta il supporto con l'ID Hardware

## 📋 Requisiti Sistema

### Comuni a Tutte le Piattaforme
- **Python**: 3.8+ (solo per installazione manuale)
- **RAM**: 4GB minimo, 8GB consigliato
- **Spazio Disco**: 2GB liberi
- **Connessione Internet**: Per download modelli Argos (primo avvio)

### Windows Specifici
- Windows 10 (64-bit) o Windows 11
- Nessun requisito aggiuntivo se usi installer

### macOS Specifici
- macOS 10.14 (Mojave) o superiore
- Apple Silicon (M1/M2) o Intel x64 supportati

### Linux Specifici
- Distribuzione moderna (Ubuntu 18.04+, Fedora 30+, Debian 10+, ecc.)
- Desktop environment con supporto GUI (GNOME, KDE, XFCE, ecc.)
- Python tkinter installato

## 🔧 Risoluzione Problemi

### Windows
- **"Python non trovato"**: Installa Python 3.8+ e aggiungi al PATH
- **Errore antivirus**: Aggiungi eccezione (falso positivo comune)
- **Tesseract non trovato**: Esegui `INSTALLA_OCR.bat`

### macOS
- **"App non verificata"**: Vai in Preferenze di Sistema → Sicurezza → Autorizza
- **Errore Python**: Usa Python 3 da python.org, non quello di sistema
- **Tkinter non funziona**: Installa Python con tkinter incluso

### Linux
- **"tkinter non trovato"**: Installa `python3-tk` o `python3-tkinter`
- **Tesseract non trovato**: Installa pacchetto `tesseract-ocr`
- **Errori dipendenze**: Usa pip con `--user` o virtual environment

## 📞 Supporto

Per assistenza installazione:
- **Email**: info@lucertae.com
- **Include**: Sistema operativo, versione, messaggio errore completo

