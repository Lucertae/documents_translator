# LAC TRANSLATE - Multi-Piattaforma

LAC TRANSLATE è disponibile per **Windows, macOS e Linux**.

## 🚀 Build Multi-Piattaforma

### Build Automatico per Piattaforma Corrente

Esegui lo script di build che rileva automaticamente la piattaforma:

```bash
python build_multi_platform.py
```

Lo script creerà:
- **Windows**: `.exe` + installer `.exe` (con InnoSetup)
- **macOS**: `.app` bundle + installer `.dmg`
- **Linux**: eseguibile + installer `.deb` (Debian/Ubuntu)

### Build Specifico per Piattaforma

```bash
# Windows
python build.py

# macOS (su Mac)
python build_multi_platform.py  # Rileva automaticamente macOS

# Linux
python build_multi_platform.py  # Rileva automaticamente Linux
```

## 📦 Distribuzione

### File da Distribuire per Piattaforma

#### Windows
- `LAC_Translate_v2.0_Setup.exe` - Installer principale
- `LAC_Translate.exe` - Eseguibile standalone (alternativa)

#### macOS
- `LAC_Translate_v2.0.0_macOS.dmg` - Installer DMG
- `LAC_Translate.app` - App bundle (alternativa)

#### Linux
- `lac-translate_2.0.0_amd64.deb` - Pacchetto Debian/Ubuntu
- `LAC_Translate` - Eseguibile standalone (alternativa)

### Documentazione Comune
- `README_INSTALLAZIONE.md` - Guida installazione
- `LICENSE.txt` - EULA
- `CHANGELOG.txt` - Modifiche versione
- `QUICK_START.txt` - Guida rapida

## 🔑 Sistema Licenze Multi-Piattaforma

Il sistema licenze funziona su tutte le piattaforme:
- **Hardware ID**: Generato diversamente per ogni OS ma compatibile
- **Formato chiave**: Stesso formato (`LAC-XXXX-XXXX-XXXX`)
- **Attivazione**: Dialog identico su tutte le piattaforme

### Hardware ID Generation
- **Windows**: MAC address + CPU ID + Machine GUID
- **macOS**: MAC address + CPU + IOPlatformUUID
- **Linux**: MAC address + CPU + /etc/machine-id

## 🛠️ Sviluppo Cross-Platform

### Struttura Codice
Il codice è progettato per essere cross-platform:
- Usa `sys.platform` per rilevare OS
- Path handling con `pathlib.Path` (compatibile tutti OS)
- Tesseract path detection automatica per ogni OS

### Dipendenze
Tutte le dipendenze sono cross-platform:
- `PyMuPDF` - Windows, macOS, Linux
- `Pillow` - Windows, macOS, Linux
- `argostranslate` - Windows, macOS, Linux
- `deep-translator` - Windows, macOS, Linux
- `pytesseract` - Windows, macOS, Linux (richiede Tesseract installato)

### Testing
Per testare su ogni piattaforma:
1. **Windows**: Build e test su VM Windows 10/11
2. **macOS**: Build su Mac (richiede Mac fisico o cloud)
3. **Linux**: Build su Ubuntu/Debian (VM o container Docker)

## 📝 Note Importanti

### Python Version
- Python 3.8+ su tutte le piattaforme
- Usa sempre Python 3, non Python 2

### Tkinter
- **Windows**: Incluso con Python
- **macOS**: Potrebbe richiedere installazione separata
- **Linux**: Installa `python3-tk` o `python3-tkinter`

### Tesseract OCR
- **Windows**: Installazione separata richiesta
- **macOS**: `brew install tesseract`
- **Linux**: `apt-get install tesseract-ocr`

### Modelli Argos
- Download automatico al primo avvio
- Stessi modelli su tutte le piattaforme
- ~800MB da scaricare una volta

## 🔄 Aggiornamenti

Gli aggiornamenti sono distribuiti come nuove versioni complete:
- Nuovo installer per ogni piattaforma
- Chiave seriale esistente continua a funzionare
- Migrazione automatica settings (se compatibile)

## 📞 Supporto Multi-Piattaforma

Il supporto è disponibile per tutte le piattaforme:
- **Email**: info@lucertae.com
- Include sempre la piattaforma nell'email di supporto
- Screenshot errori sono utili su tutte le piattaforme

---

**LAC TRANSLATE v2.0** - Multi-Piattaforma  
© 2024 LAC Software

