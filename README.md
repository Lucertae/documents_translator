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
| Coates_825.pdf | PDF nativo | 36 | Testo denso, footnotes |
| Trotec Distribution Contract | Scansione | 21 | Contratto, OCR |
| Mimaki Agreement | Scansione | 13 | Landscape, OCR |
| confidenziali/*.pdf | Vari | - | Documenti reali |

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

## 📜 Licenza

Apache 2.0 - Basato su pdf-translator-for-human
