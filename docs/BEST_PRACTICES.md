# Best Practices per OCR e Traduzione

## PaddleOCR v3.3+ Best Practices

### 1. Configurazione Ottimale per Documenti Scansionati

```python
from paddleocr import PaddleOCR

ocr = PaddleOCR(
    # Modelli raccomandati per documenti EN
    det_model_name="PP-OCRv5_server_det",  # Detection più accurato
    rec_model_name="en_PP-OCRv5_mobile_rec",  # Recognition per EN
    
    # Preprocessing documento
    use_doc_orientation_classify=True,  # Correggi orientamento
    use_doc_unwarping=True,  # Correggi distorsioni
    use_textline_orientation=True,  # Orientamento linee di testo
    
    # Soglie di detection
    text_det_thresh=0.3,  # Lower = più sensibile (default 0.5)
    text_det_box_thresh=0.5,  # Threshold bounding box
    
    # Performance
    lang="en",
)
```

### 2. Parametri Critici

| Parametro | Valore Consigliato | Note |
|-----------|-------------------|------|
| `text_det_thresh` | 0.3-0.5 | Più basso = più testo rilevato |
| `text_det_box_thresh` | 0.5-0.6 | Qualità bounding box |
| `use_doc_orientation_classify` | True | Per scansioni ruotate |
| `use_doc_unwarping` | True | Per documenti storti |

### 3. Risoluzione Immagine

```python
# Scala ottimale per OCR
ocr_scale = 2.0  # 2x la risoluzione originale

mat = fitz.Matrix(ocr_scale, ocr_scale)
pix = page.get_pixmap(matrix=mat, alpha=False)
```

- **Minimo**: 150 DPI
- **Ottimale**: 300 DPI (scale 2.0 per PDF standard a 72 DPI)
- **Massimo utile**: 400 DPI (oltre non migliora, solo rallenta)

### 4. Post-processing OCR

Errori comuni da correggere con pattern matching:
- I/l/1 confusione (es. "Mimakl" → "Mimaki")
- O/0 confusione (es. "Auth0rized" → "Authorized")
- rn/m confusione (es. "cornpany" → "company")
- Ligature non risolte (ﬁ, ﬂ, ﬀ)

### 5. Layout Detection per Multi-Colonna

```python
from paddleocr import LayoutDetection

layout = LayoutDetection()
result = layout.predict(image)

# Estrai colonne
text_boxes = [b for b in result[0]['boxes'] 
              if b['label'] in ['text', 'title'] 
              and b['score'] > 0.5]
```

---

## OPUS-MT (Helsinki-NLP) Best Practices

### 1. Segmentazione Frasi

```python
import re

def segment_sentences(text):
    """Segmenta correttamente per traduzione."""
    # Pattern che preserva abbreviazioni
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
# Termini da NON tradurre
PRESERVE_TERMS = [
    "Mimaki", "MIMAKI",
    "Trotec", "Bompan",
    "URL", "PDF", "ISO",
]

def protect_terms(text, terms):
    """Proteggi termini dalla traduzione."""
    placeholders = {}
    for i, term in enumerate(terms):
        if term in text:
            placeholder = f"[[TERM{i}]]"
            text = text.replace(term, placeholder)
            placeholders[placeholder] = term
    return text, placeholders

def restore_terms(text, placeholders):
    """Ripristina termini dopo traduzione."""
    for placeholder, term in placeholders.items():
        text = text.replace(placeholder, term)
    return text
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
- **Confidence minima** > 0.5 = accettabile
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

## Checklist Iterazione

Prima di ogni modifica:
- [ ] Test baseline su documento target
- [ ] Cattura metriche OCR/Translation/Format

Dopo ogni modifica:
- [ ] Ri-test su documento target
- [ ] Confronto metriche con baseline
- [ ] Test regressione su altri documenti
- [ ] Solo se tutti ok → commit modifica
