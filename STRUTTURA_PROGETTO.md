# 📁 Struttura Progetto LAC TRANSLATE v2.0

Struttura professionale e organizzata del progetto.

## 📂 Struttura Directory

```
LAC_Translate/
│
├── app/                          # ✅ Codice sorgente applicazione
│   ├── __pycache__/              # Cache Python (generato)
│   ├── deep_translator/          # Libreria traduzione
│   ├── pdf_translator_gui.py     # GUI principale
│   ├── license_manager.py        # Sistema licenze
│   ├── license_activation.py     # Dialog attivazione
│   ├── settings_manager.py       # Gestione settings
│   ├── settings_dialog.py         # Dialog settings
│   ├── batch_processor.py        # Processamento batch
│   ├── batch_dialog.py           # Dialog batch
│   ├── generate_license.py       # Generazione chiavi
│   ├── version.py                # Versioning
│   └── setup_argos_models.py     # Setup modelli Argos
│
├── scripts/                      # ✅ Script e utility
│   ├── windows/                  # Script Windows (.bat, .ps1)
│   │   ├── AVVIA_GUI.bat         # Avvia applicazione
│   │   ├── INSTALLA_DIPENDENZE.bat
│   │   ├── INSTALLA_OCR.bat
│   │   ├── VERIFICA_INSTALLAZIONE.bat
│   │   └── *.ps1                 # Script PowerShell
│   │
│   ├── development/              # Script sviluppo
│   │   ├── QUICK_TEST.bat
│   │   └── REORGANIZZA_PROGETTO.bat
│   │
│   ├── INSTALL_MACOS.sh          # Installer macOS
│   └── INSTALL_LINUX.sh          # Installer Linux
│
├── docs/                         # ✅ Documentazione
│   ├── user/                     # Documentazione utente finale
│   │   ├── README_DISTRIBUZIONE.md
│   │   ├── INSTALLAZIONE_MULTIPIATTAFORMA.md
│   │   └── QUICK_START.txt
│   │
│   ├── legal/                    # Documenti legali
│   │   ├── LICENSE.txt           # EULA
│   │   ├── PRIVACY_POLICY.md
│   │   └── TERMS_OF_SERVICE.md
│   │
│   ├── internal/                 # Documentazione sviluppo (interna)
│   │   ├── DOCUMENTAZIONE_SICUREZZA_E_LICENZE.md
│   │   ├── STATO_BUILD_E_GIU.md
│   │   ├── TESTING_CHECKLIST.md
│   │   ├── BUILD_README.md
│   │   └── ...
│   │
│   └── FEATURES.md               # Lista funzionalità (utente)
│
├── guides/                       # ✅ Guide utente
│   ├── QUICK_START_GUI.md
│   ├── GUIDA_OCR.md
│   └── QUICK_COMPARISON.md
│
├── changelog/                    # ✅ Changelog versioni
│   ├── CHANGELOG.md              # Changelog principale (unico)
│   ├── METODO_SEARCHABLE_IBRIDO.md
│   ├── MIGLIORAMENTI_LAYOUT.md
│   └── ZOOM_AGGIUNTO.md
│
├── dev/                          # ✅ File sviluppo/temporanei
│   ├── archive/                  # File archiviati (non più attivi)
│   │   ├── status/               # File status temporanei (archiviati)
│   │   └── lac_translate_italia.py  # Versione alternativa PyQt6 (archiviata)
│   └── application.log           # Log sviluppo
│
├── resources/                     # ✅ Risorse applicazione
│   └── icons/
│       └── logo_alt.ico          # Icona applicazione
│
├── build/                        # ✅ Output build (generato)
│   └── (vuoto - creato da build script)
│
├── dist/                         # ✅ Eseguibili compilati (generato)
│   └── (vuoto - creato da PyInstaller)
│
├── release/                      # ✅ Package distribuzione (generato)
│   └── (vuoto - creato da build script)
│
├── config/                       # ✅ Configurazione applicazione
│   └── settings.json             # Settings utente
│
├── license/                      # ✅ Dati licenze
│   ├── license.dat               # Cache licenza
│   ├── config.json               # Config licenza
│   └── eula_accepted.txt         # Accettazione EULA
│
├── logs/                         # ✅ Log applicazione
│   ├── pdf_translator.log
│   └── README.txt
│
├── output/                       # ✅ Output traduzioni (temporaneo)
│   └── README.txt
│
├── build.py                      # ✅ Script build Windows
├── build_multi_platform.py       # ✅ Script build multi-piattaforma
├── installer_setup.iss           # ✅ Script InnoSetup installer
├── lac_translate.spec            # ✅ PyInstaller spec file
├── requirements.txt              # ✅ Dipendenze Python
├── LICENSE.txt                   # ✅ EULA (root per installer)
├── README.md                     # ✅ README principale
└── STRUTTURA_PROGETTO.md         # ✅ Questo documento
```

---

## 📋 File Principali Root (Solo Essenziali)

### File Root Mantenuti:
- ✅ `README.md` - README principale progetto
- ✅ `LICENSE.txt` - EULA (richiesto per installer)
- ✅ `requirements.txt` - Dipendenze Python
- ✅ `build.py` - Build script Windows
- ✅ `build_multi_platform.py` - Build script multi-piattaforma
- ✅ `installer_setup.iss` - Installer InnoSetup
- ✅ `lac_translate.spec` - PyInstaller config
- ✅ `STRUTTURA_PROGETTO.md` - Documentazione struttura

**Nota**: `CHANGELOG.md` è stato spostato in `changelog/CHANGELOG.md` (unico changelog)

### Cartelle Root:
- ✅ `app/` - Codice sorgente
- ✅ `scripts/` - Script e utility
- ✅ `docs/` - Documentazione
- ✅ `guides/` - Guide utente
- ✅ `changelog/` - Changelog
- ✅ `dev/` - File sviluppo
- ✅ `resources/` - Risorse
- ✅ `build/` - Output build (generato)
- ✅ `dist/` - Eseguibili (generato)
- ✅ `release/` - Package (generato)
- ✅ `config/` - Configurazione
- ✅ `license/` - Dati licenze
- ✅ `logs/` - Log applicazione
- ✅ `output/` - Output temporaneo

---

## 🚫 File/Cartelle Rimosse/Spostate

### File Spostati/Unificati in `docs/internal/`:
- `STATO_COMPLETAMENTO.md` - Stato completamento (unificato)
- `COSA_MANCA_RIEPILOGO.md` - Cosa manca (unificato, COSA_MANCA.md eliminato)
- `DOCUMENTAZIONE_SICUREZZA_E_LICENZE.md`
- `STATO_BUILD_E_GIU.md`
- `TESTING_CHECKLIST.md`
- `TESTING_MODE_README.md`
- `BUILD_README.md`
- `INSTALLER_README.md`
- `LICENSE_KEY_GENERATOR_README.md`
- Altri documenti tecnici interni

**File Eliminati (duplicati unificati)**:
- `COSA_MANCA.md` → Unificato in `COSA_MANCA_RIEPILOGO.md`
- `COMPLETAMENTO_FINALE.md` → Unificato in `STATO_COMPLETAMENTO.md`
- `RIEPILOGO_FINALE_COMPLETAMENTO.md` → Unificato in `STATO_COMPLETAMENTO.md`
- `docs/README_FINALE.md`, `README_MIGLIORAMENTI_v2.1.md`, `README_v2.2_SEARCHABLE_IBRIDO.md`, `VERSIONE_FINALE_v2.1_ROBUSTO.md` → Eliminati (duplicati)
- `docs/RIEPILOGO_COMPLETAMENTO.md` → Eliminato (duplicato)

### File in `scripts/windows/`:
- `AVVIA.bat` / `AVVIA_GUI.bat` - Avvia applicazione
- `INSTALLA_DIPENDENZE.bat`
- `INSTALLA_OCR.bat`
- `VERIFICA_INSTALLAZIONE.bat`
- `CREA_SHORTCUT_DESKTOP.bat`
- `AGGIORNA_ICONA_DESKTOP.bat`
- `RISOLVI_ICONA_DESKTOP.bat`
- Tutti i file `.ps1`

**File Eliminati dalla root**:
- `AVVIA.bat` (root) → Duplicato di `scripts/windows/AVVIA.bat`

### File Spostati in `scripts/development/`:
- `QUICK_TEST.bat`
- `REORGANIZZA_PROGETTO.bat`

### File Spostati in `scripts/`:
- `INSTALL_MACOS.sh`
- `INSTALL_LINUX.sh`

### File Spostati in `docs/legal/`:
- `LICENSE.txt` (copia, originale rimane root)
- `docs/PRIVACY_POLICY.md`
- `docs/TERMS_OF_SERVICE.md`

### File Spostati in `docs/user/`:
- `docs/README_DISTRIBUZIONE.md`
- `docs/INSTALLAZIONE_MULTIPIATTAFORMA.md`
- `guides/QUICK_START.txt`

### File Archiviati in `dev/archive/`:
- `dev/archive/status/*.txt` - File status temporanei di sviluppo (archiviati)
- `dev/archive/lac_translate_italia.py` - Versione alternativa PyQt6 (archiviata)

### File Spostati in `resources/icons/`:
- `logo_alt.ico`

### Cartelle Rimosse:
- `status/` (sostituita da `dev/status/`)

---

## ✅ Regole Organizzazione

### 1. Root Directory
**Solo file essenziali per:**
- Build e distribuzione
- README principale
- Requirements
- LICENSE (richiesto installer)
- STRUTTURA_PROGETTO.md

**Nota**: Changelog è in `changelog/CHANGELOG.md` (non più in root)

### 2. Script
**Organizzati per piattaforma e uso:**
- `scripts/windows/` - Script Windows utente
- `scripts/development/` - Script sviluppo
- `scripts/` - Script installazione cross-platform

### 3. Documentazione
**Separata per audience:**
- `docs/user/` - Per utenti finali
- `docs/legal/` - Documenti legali
- `docs/internal/` - Documentazione sviluppo
- `docs/` - Documentazione generale

### 4. File Temporanei e Archiviati
**In `dev/`:**
- `dev/application.log` - Log sviluppo
- `dev/archive/` - File archiviati (non più attivi ma mantenuti per storico)
  - `dev/archive/status/` - File status temporanei archiviati
  - `dev/archive/lac_translate_italia.py` - Versioni alternative archiviate

### 5. Risorse
**In `resources/`:**
- Icone
- Immagini
- Template

---

## 🎯 Vantaggi Struttura

✅ **Professionale**: Struttura chiara e standard
✅ **Scalabile**: Facile aggiungere nuovi file
✅ **Pulita**: Root directory minimalista
✅ **Organizzata**: Ogni file ha la sua posizione logica
✅ **Mantenibile**: Facile trovare file
✅ **Distribuzione**: Solo file necessari in package finale

---

## 📝 Note

- File generati (`build/`, `dist/`, `release/`) non vanno in commit
- Documentazione interna (`docs/internal/`) non va in distribuzione utente
- File temporanei (`dev/`) non vanno in distribuzione
- File archiviati (`dev/archive/`) sono storici e non attivi
- Solo `docs/user/` e `docs/legal/` vanno in package vendita
- `changelog/CHANGELOG.md` è l'unico changelog principale (non più duplicato in root)

## 🔄 Riorganizzazione Completata

**Modifiche Applicate**:
- ✅ Duplicati documentazione eliminati/unificati
- ✅ Changelog consolidato in `changelog/CHANGELOG.md` (unico)
- ✅ File temporanei archiviati in `dev/archive/`
- ✅ File root duplicati eliminati (`AVVIA.bat`, `CHANGELOG.md`)
- ✅ Struttura documentazione consolidata in `docs/internal/`
- ✅ Versione alternativa `lac_translate_italia.py` archiviata


