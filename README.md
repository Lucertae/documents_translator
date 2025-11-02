# LAC TRANSLATE v2.0 - Professional PDF Translator

**Traduzione professionale di PDF con preservazione layout completo**

## ⚖️ Licenza

Questo software è **proprietario** e protetto da copyright. Il codice sorgente è reso pubblico 
in questo repository per trasparenza e collaborazione, ma **l'uso commerciale richiede una 
licenza a pagamento**.

- **Visualizzazione e studio:** ✅ Permesso
- **Uso personale/educativo:** ✅ Permesso
- **Uso commerciale:** ❌ Richiede licenza a pagamento

Per informazioni su licenze commerciali, contattare il venditore.

Vedi `LICENSE_GITHUB.md` per i termini completi.

**Nota importante:** Questo software utilizza PyMuPDF (AGPL v3). Per uso commerciale senza 
restrizioni AGPL, è disponibile una versione con licenza commerciale PyMuPDF.

---

## 🚀 Avvio Rapido

### Windows
```bash
# Opzione 1: Script dedicato
scripts\windows\AVVIA_GUI.bat

# Opzione 2: Python diretto
python app/pdf_translator_gui.py
```

### macOS / Linux
```bash
# Installazione
./scripts/INSTALL_MACOS.sh    # macOS
./scripts/INSTALL_LINUX.sh    # Linux

# Avvio
python3 app/pdf_translator_gui.py
```

---

## 📋 Funzionalità

### Core Translation
- ✅ **Traduzione PDF** con preservazione layout perfetto
- ✅ **2 Motori traduzione**: Google Translate (online) + Argos Translate (offline)
- ✅ **OCR integrato**: Traduzione PDF scansionati con Tesseract, Dolphin, Chandra
- ✅ **8 Metodi estrazione testo** + metodo ibrido intelligente
- ✅ **Batch processing**: Traduci cartelle intere di PDF

### System Features
- ✅ **Sistema Licenze**: Hardware binding e gestione licenze
- ✅ **Security System**: Integrity checking, secure storage, anti-tampering
- ✅ **Auto-Update**: Verifica aggiornamenti da GitHub Releases
- ✅ **GUI professionale**: Menu, shortcuts, tooltips, tema moderno
- ✅ **Multi-piattaforma**: Windows, macOS, Linux

---

## 📦 Installazione

### Per Utenti Finali (Raccomandato)

**Installazione Semplice - Nessuna Configurazione Tecnica Richiesta:**

1. **Scarica installer** `LAC_Translate_v2.0.0_Setup.exe` dalla [GitHub Release](https://github.com/Lucertae/documents_translator/releases)
2. **Esegui installer** (doppio click)
3. **Segui wizard** di installazione
4. **Avvia** dal desktop o menu Start
5. **Inserisci** chiave seriale all'avvio

✅ **Non serve installare Python** - tutto è incluso nell'installer!

### Requisiti
- Windows 10/11 (64-bit)
- 4GB RAM (8GB consigliato)
- 2GB spazio disco

### Per Sviluppatori (Sviluppo da Sorgenti)

**Opzione 1: Script Automatico**
```bash
scripts\windows\INSTALLA_DIPENDENZE.bat
scripts\windows\INSTALLA_OCR.bat
scripts\windows\AVVIA_GUI.bat
```

**Opzione 2: Manuale**
1. Installa Python 3.8+ da [python.org](https://www.python.org/downloads/)
2. Installa dipendenze: `pip install -r requirements.txt`
3. Avvia: `python app/pdf_translator_gui.py`

### macOS / Linux
```bash
./scripts/INSTALL_MACOS.sh    # macOS
./scripts/INSTALL_LINUX.sh    # Linux
```

---

## 📖 Documentazione

- **Guida Utente**: `docs/user/README_DISTRIBUZIONE.md`
- **Installazione**: `docs/user/INSTALLAZIONE_MULTIPIATTAFORMA.md`
- **Quick Start**: `docs/user/QUICK_START.txt`
- **Funzionalità**: `docs/FEATURES.md`

---

## 🔧 Sviluppo

### Build
```bash
# Windows
python build.py

# Multi-piattaforma
python build_multi_platform.py
```

### CI/CD
- **GitHub Actions**: Build e release automatizzati
- **Auto-Release**: Tag versione → Build → Release automatica
- **Testing**: Test automatici su Windows, Linux, macOS

### Documentazione Sviluppo
- Vedi `docs/internal/` per documentazione tecnica
- Vedi `STRUTTURA_PROGETTO.md` per struttura dettagliata
- Vedi `scripts/development/PRIMO_VERSIONING.md` per prima release

---

## 📄 Licenze

- **Software**: Proprietario (vedi `LICENSE.txt`)
- **Librerie**: Vedi `requirements.txt` per dettagli
- **Privacy**: `docs/legal/PRIVACY_POLICY.md`
- **Termini**: `docs/legal/TERMS_OF_SERVICE.md`

---

## 🛠️ Struttura Progetto

```
LAC_Translate/
├── app/              # Codice sorgente
├── scripts/          # Script Windows/PowerShell
├── docs/             # Documentazione
│   ├── user/        # Per utenti
│   ├── legal/       # Legali
│   └── internal/    # Sviluppo
├── guides/           # Guide utente
├── resources/        # Risorse (icone, ecc.)
└── build.py         # Script build
```

Vedi `STRUTTURA_PROGETTO.md` per dettagli completi.

---

## 📞 Supporto

**Email**: info@lucertae.com

---

**LAC TRANSLATE v2.0** - © 2025 Lucertae Software
