# 🌍 LAC TRANSLATE - PDF Translator

Traduttore PDF professionale con OPUS-MT e PaddleOCR.

---

## 🔧 Sviluppo: Ciclo Iterativo di Miglioramento

### Metodologia

Lo sviluppo segue un **ciclo iterativo** basato su test di regressione visuale:

```
1. IDENTIFICA PROBLEMA
   └─> Esamina PNG di confronto (originale | tradotto)
   └─> Scegli UN problema specifico da affrontare

2. IMPLEMENTA FIX
   └─> Modifica app/core/pdf_processor.py
   └─> Focus su una singola causa alla volta

3. TEST MIRATO (prima del regression completo!)
   └─> Testa SOLO sui documenti che esibiscono il problema
   └─> Usa test manuali rapidi prima del regression completo
   └─> Verifica che il fix funzioni sul caso specifico

4. TEST REGRESSIONE COMPLETO
   └─> Esegui: python test_regression.py
   └─> Genera PNG confronto per TUTTI i documenti
   └─> ⚠️ SOLO dopo aver verificato il fix in modo mirato!

5. VALUTA RISULTATI
   └─> Controlla PNG in output/regression_test/
   └─> Verifica che il fix funzioni
   └─> Verifica che non ci siano regressioni

6. RIPETI
   └─> Torna al punto 1 con il prossimo problema
```

### ⚠️ Best Practice: Test Prima del Regression

**IMPORTANTE**: Il test di regressione completo richiede molto tempo (30+ minuti).

Prima di eseguirlo:

1. **Verifica il fix su documenti specifici** che esibiscono il problema
2. **Procedi con precisione e cautela** - ogni modifica può avere effetti collaterali
3. **Ricorda**: il programma deve funzionare in modo eccellente per **qualsiasi documento**
4. **Segui le best practice** - non fare modifiche affrettate

---

### 🔬 Controllo Qualità Codice

Ogni iterazione DEVE includere verifiche sulla qualità del codice:

#### 1. Dimensione e Complessità

```bash
# Conta linee di codice (esclusi commenti e righe vuote)
find app -name "*.py" -exec cat {} \; | grep -v '^\s*#' | grep -v '^\s*$' | wc -l

# Analisi complessità con radon
pip install radon
radon cc app/core/*.py -a -s  # Complessità ciclomatica
radon mi app/core/*.py -s     # Maintainability Index

# Target:
# - Complessità ciclomatica media: A o B (≤10)
# - Maintainability Index: >65 (buono), >85 (eccellente)
```

#### 2. Codice Morto e Import Inutilizzati

```bash
# Trova import non usati
pip install autoflake
autoflake --check --remove-all-unused-imports app/core/*.py

# Trova codice morto con vulture
pip install vulture
vulture app/core/ --min-confidence 80

# Rimuovi import inutilizzati (dry-run prima!)
autoflake --in-place --remove-all-unused-imports app/core/*.py
```

#### 3. Duplicazione Codice

```bash
# Analisi duplicati con pylint
pylint app/core/*.py --disable=all --enable=duplicate-code

# Oppure con CPD (Copy-Paste Detector) - più dettagliato
pip install flake8 flake8-pep3101
# O usa: https://github.com/jscpd/jscpd (npm install -g jscpd)
jscpd app/core/ --min-lines 5 --min-tokens 50

# Target: <5% duplicazione
```

#### 4. Type Checking e Linting

```bash
# Type checking con mypy
pip install mypy
mypy app/core/*.py --ignore-missing-imports

# Linting completo con ruff (più veloce di flake8+pylint)
pip install ruff
ruff check app/core/

# Fix automatico problemi semplici
ruff check app/core/ --fix
```

#### 5. Checklist Controllo Codice

Prima di ogni commit, verifica:

| Check | Comando | Target |
|-------|---------|--------|
| Import inutilizzati | `autoflake --check` | 0 |
| Codice morto | `vulture --min-confidence 80` | 0 falsi positivi |
| Duplicazione | `pylint --enable=duplicate-code` | <5% |
| Complessità | `radon cc -a` | Media ≤10 (A/B) |
| Type errors | `mypy` | 0 errori |
| Linting | `ruff check` | 0 errori |
| LOC variazione | `wc -l` | Giustificata |

#### 6. Monitoraggio Crescita Codebase

```bash
# Snapshot dimensioni attuali
echo "=== Snapshot Codebase ===" > code_metrics.txt
date >> code_metrics.txt
echo "LOC per file:" >> code_metrics.txt
find app -name "*.py" -exec wc -l {} \; | sort -n >> code_metrics.txt
echo "Totale:" >> code_metrics.txt
find app -name "*.py" -exec cat {} \; | wc -l >> code_metrics.txt
```

**Regola d'oro**: Se una modifica aumenta le LOC >10% senza nuove feature, probabilmente c'è refactoring da fare.

```bash
# Test mirato su UN documento specifico (rapido)
python -c "
from app.core.pdf_processor import PDFProcessor
from app.core.translator import TranslationEngine
processor = PDFProcessor('input/documento_problematico.pdf')
translator = TranslationEngine('en', 'it')
result = processor.translate_page(0, translator)
result.save('output/test_rapido.pdf')"

# Solo DOPO aver verificato, esegui il test completo
python test_regression.py
```

### Script di Test

```bash
# Test regressione completo (4 pagine per documento)
python test_regression.py

# Output: PNG in output/regression_test/*.png
```

Il test genera immagini affiancate: **originale a sinistra, tradotto a destra**.

### Metriche Qualità

- **Overlap <10%**: ✅ OK
- **Overlap ≥10%**: ⚠️ Warning
- **Font <7pt >20%**: ⚠️ Warning (testo troppo piccolo)

### Documenti di Test

| Documento | Tipo | Pagine | Note |
|-----------|------|--------|------|
| xxx_825.pdf | PDF nativo | 36 | Testo denso, footnotes |
| xxx | Scansione | 21 | Contratto, OCR |
| xxx | Scansione | 13 | Landscape, OCR |
| xxx pdf | Vari | - | Documenti reali |

---

## 📁 Struttura Progetto

```
documents_translator/
├── app/
│   ├── core/
│   │   ├── pdf_processor.py    ← Logica principale traduzione
│   │   └── translator.py       ← Engine OPUS-MT
│   ├── ui/
│   │   ├── main_window.py      ← GUI Qt6
│   │   └── pdf_viewer.py       ← Visualizzatore PDF
│   └── main_qt.py              ← Entry point GUI
│
├── input/                      ← Documenti da tradurre
│   └── confidenziali/          ← Documenti sensibili
│
├── output/
│   ├── regression_test/        ← PNG confronto test
│   └── *.pdf                   ← PDF tradotti
│
├── test_regression.py          ← Script test regressione
├── QUALITY_REPORT.md           ← Report qualità attuale
└── README.md                   ← Questa guida
```

---

## 🚀 Avvio Rapido

```bash
# Setup ambiente
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Avvia GUI
python app/main_qt.py

# Oppure test regressione
python test_regression.py
```

---

## 🔍 Problemi Noti e Priorità

Vedere [QUALITY_REPORT.md](QUALITY_REPORT.md) per analisi dettagliata.

### Priorità Alta
1. **Overlap testo** - Testo tradotto più lungo dell'originale
2. **Font troppo piccoli** - Scaling eccessivo in spazi ristretti

### Priorità Media
3. **Footnotes** - Sovrapposizioni nelle note a piè pagina
4. **Layout multi-colonna** - Non gestito correttamente

---

## � Error Tracking con Sentry

LAC Translate utilizza **Sentry** per il monitoraggio degli errori in produzione.

### Configurazione

1. Crea un progetto su [sentry.io](https://sentry.io)
2. Copia il DSN del progetto
3. Crea un file `.env` nella root del progetto:

```bash
# .env
SENTRY_DSN=https://your-dsn@sentry.io/project-id
SENTRY_ENVIRONMENT=development  # oppure: production, staging
```

### Cosa viene tracciato

| Evento | Categoria | Dettagli |
|--------|-----------|----------|
| Errori PDF | `pdf` | Caricamento, estrazione testo, salvataggio |
| Errori Traduzione | `translation` | Modello, encoding, timeout |
| Errori OCR | `ocr` | PaddleOCR, layout detection |
| Errori UI | `ui` | Worker threads, callbacks Qt |

### Informazioni inviate

Ogni errore include automaticamente:
- **Versione app**: `lac-translate@0.1.3` (release tag)
- **Tag versione**: `app.version.major`, `app.version.minor`, `app.version.patch`
- **Sistema**: OS, versione Python, disponibilità CUDA
- **Breadcrumbs**: Trail di azioni prima dell'errore
- **Stack trace**: Completo con variabili locali

### Privacy

Il flag `send_default_pii=True` è abilitato. Per disabilitarlo, modifica in `sentry_integration.py`:

```python
init_sentry(send_default_pii=False)
```

---

## 🏷️ Versioning e Release

### Schema Versione

Il progetto segue [Semantic Versioning](https://semver.org/):

```
MAJOR.MINOR.PATCH[-BUILD]
  │     │     │      │
  │     │     │      └── Build number (da GitHub Actions)
  │     │     └── Bug fix, patch di sicurezza
  │     └── Nuove feature retrocompatibili
  └── Breaking changes
```

**Versione corrente**: `0.1.3`

### File di Versione

La versione è centralizzata in `app/__version__.py`:

```python
VERSION_MAJOR = 0
VERSION_MINOR = 1
VERSION_PATCH = 3
VERSION_BUILD = ""  # Popolato da GitHub Actions

__version__ = f"{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_PATCH}"
APP_NAME = "lac-translate"
```

### Build con GitHub Actions

Le build automatiche popolano il numero di build:

```yaml
# .github/workflows/build.yml
name: Build Release

on:
  push:
    tags:
      - 'v*'
  workflow_dispatch:

jobs:
  build:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest]
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.13'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pyinstaller
      
      - name: Set version build number
        run: |
          # Inserisce build number nel file versione
          BUILD_NUM="${{ github.run_number }}"
          sed -i "s/VERSION_BUILD = \"\"/VERSION_BUILD = \"$BUILD_NUM\"/" app/__version__.py
      
      - name: Build executable
        run: |
          pyinstaller lac_translate.spec
      
      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: lac-translate-${{ matrix.os }}
          path: dist/
```

### Creare una Release

```bash
# 1. Aggiorna versione in app/__version__.py
# 2. Commit e tag
git add app/__version__.py
git commit -m "Bump version to 0.2.0"
git tag v0.2.0
git push origin main --tags

# GitHub Actions builderà automaticamente per Linux e Windows
```

### Visualizzare Versione

```bash
# Da Python
python -c "from app.__version__ import get_version_with_build; print(get_version_with_build())"
# Output: 0.1.3+42 (dove 42 è il build number)

# In Sentry, vedrai: lac-translate@0.1.3+42
```

---

## �📜 Licenza

Apache 2.0 - Basato su pdf-translator-for-human

