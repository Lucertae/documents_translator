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
