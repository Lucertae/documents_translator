# Best Practices per OCR e Traduzione

## GLM-OCR Best Practices

### 1. Installazione e Setup

GLM-OCR usa Ollama come backend. Per installare:

```bash
# 1. Installa Ollama
# macOS/Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows - scarica da https://ollama.com/download

# 2. Avvia il servizio Ollama
ollama serve

# 3. Pull del modello GLM-OCR (2.2GB)
ollama pull glm-ocr
```

### 2. Utilizzo Base

```python
from app.core.glm_ocr import GlmOcrEngine, check_ollama_status

# Verifica stato
is_ready, message = check_ollama_status()
print(f"GLM-OCR: {message}")

# Uso basico
engine = GlmOcrEngine()
text, confidence = engine.recognize_text(image_bytes, mode="text")
```

### 3. Modalità di Riconoscimento

| Modalità | Uso | Prompt |
|----------|-----|--------|
| `text` | Testo normale | "Text Recognition:" |
| `table` | Tabelle | "Table Recognition:" |
| `figure` | Figure/diagrammi | "Figure Recognition:" |

```python
# Riconoscimento testo normale
text, conf = engine.recognize_text(image_bytes, mode="text")

# Riconoscimento tabelle
table_text, conf = engine.recognize_text(image_bytes, mode="table")

# Riconoscimento automatico (rileva tabelle)
text = engine.recognize_document_page(image_bytes, detect_tables=True)
```

### 4. Risoluzione Immagine

- **Ottimale**: 300 DPI (scale 2.0 per PDF standard a 72 DPI)
- GLM-OCR gestisce automaticamente orientamento e dewarping
- Usa PNG per massima qualità

```python
import pymupdf

# Scala ottimale per OCR
pix = page.get_pixmap(matrix=pymupdf.Matrix(2.0, 2.0))
img_data = pix.tobytes("png")
```

### 5. Post-processing OCR

Il post-processing in `ocr_utils.py` corregge errori comuni:

- I/l/1 confusione (es. "Mimakl" → "Mimaki")
- O/0 confusione (es. "Auth0rized" → "Authorized")
- Normalizzazione spazi e punteggiatura
- Rimozione artefatti di pagina

```python
from app.core.ocr_utils import clean_ocr_text, post_process_ocr_text

# Applica correzioni OCR
text = clean_ocr_text(raw_text)
text = post_process_ocr_text(text)
```

### 6. Performance

GLM-OCR (0.9B parametri) è ottimizzato per:
- Inferenza veloce su CPU
- Basso consumo di memoria (~2.2GB)
- Alta precisione (#1 su OmniDocBench V1.5 con 94.62)

---

## OPUS-MT (Helsinki-NLP) Best Practices

### 1. Segmentazione Frasi

```python
import re

def segment_sentences(text):
    """Segmenta correttamente per traduzione."""
    pattern = r'(?<=[.!?])\s+(?=[A-Z])'
    sentences = re.split(pattern, text)
    return [s.strip() for s in sentences if s.strip()]
```

### 2. Normalizzazione Pre-Traduzione

```python
def normalize_for_opus(text):
    """Normalizza caratteri problematici per OPUS-MT."""
    # Smart quotes → straight quotes
    text = text.replace('"', '"').replace('"', '"')
    text = text.replace(''', "'").replace(''', "'")
    
    # Dashes → ASCII hyphen
    text = text.replace('–', '-').replace('—', '-')
    
    # Ellipsis → dots
    text = text.replace('…', '...')
    
    # Ligatures
    text = text.replace('ﬁ', 'fi').replace('ﬂ', 'fl')
    
    return text
```

### 3. Protezione Termini

```python
PRESERVE_TERMS = ["Mimaki", "MIMAKI", "Trotec", "URL", "PDF", "ISO"]

def protect_terms(text, terms):
    """Proteggi termini dalla traduzione."""
    placeholders = {}
    for i, term in enumerate(terms):
        if term in text:
            placeholder = f"[[TERM{i}]]"
            text = text.replace(term, placeholder)
            placeholders[placeholder] = term
    return text, placeholders
```

### 4. Lunghezza Chunk Ottimale

```python
MAX_TOKENS = 512  # Limite OPUS-MT

def chunk_text(text, max_chars=1500):
    """Dividi in chunk mantenendo frasi intere."""
    sentences = segment_sentences(text)
    chunks = []
    current_chunk = []
    current_length = 0
    
    for sentence in sentences:
        if current_length + len(sentence) > max_chars:
            chunks.append(' '.join(current_chunk))
            current_chunk = [sentence]
            current_length = len(sentence)
        else:
            current_chunk.append(sentence)
            current_length += len(sentence)
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks
```

---

## Verifica Qualità

### 1. Metriche OCR
- **Confidence media** > 0.85 = buona qualità
- **Lunghezza output** ragionevole per il documento
- **Termini attesi** trovati = 100%

### 2. Metriche Traduzione
- **Rapporto frasi** (orig/trad) ≈ 1.0 (±20%)
- **Termini preservati** = 100%
- **Nessuna troncatura** visibile

### 3. Metriche Formattazione
- **Numero blocchi** preservato
- **Font sizes** coerenti
- **Layout** riconoscibile

---

## Troubleshooting

### Ollama non risponde

```bash
# Verifica che il servizio sia attivo
curl http://localhost:11434/api/tags

# Riavvia se necessario
ollama serve
```

### Modello non trovato

```bash
# Pull del modello
ollama pull glm-ocr

# Verifica modelli installati
ollama list
```

### OCR lento

- Riduci la risoluzione (scale 1.5 invece di 2.0)
- Usa la versione quantizzata: `ollama pull glm-ocr:q8_0`
- Verifica che nessun altro processo usi Ollama
