# 📦 Installazione Dolphin OCR e Chandra OCR

Guida completa per installare e configurare Dolphin OCR e Chandra OCR in LAC TRANSLATE.

---

## 🐬 Dolphin OCR

**Repository**: [https://github.com/bytedance/Dolphin](https://github.com/bytedance/Dolphin)

Dolphin è un modello avanzato di parsing documenti immagine (0.3B parametri) che supporta parsing a livello pagina ed elemento.

### Installazione

#### Opzione 1: Repository Locale (Raccomandato)

```bash
# 1. Clona il repository
cd C:\Users\jecho\Desktop\Apps_LAC\Lac_Translate
git clone https://github.com/bytedance/Dolphin.git

# 2. Installa dipendenze
cd Dolphin
pip install -r requirements.txt

# 3. Scarica modello pre-trained (Dolphin-1.5)
# Metodo A: Git LFS
git lfs install
git clone https://huggingface.co/ByteDance/Dolphin-1.5 ../hf_model

# Metodo B: Hugging Face CLI
pip install huggingface_hub
cd ..
huggingface-cli download ByteDance/Dolphin-1.5 --local-dir ./hf_model

# 4. Torna alla directory principale
cd ..
```

#### Opzione 2: Solo Modello (se repository già presente)

Se hai già Dolphin installato altrove, crea symlink o copia:
```bash
# Crea directory per modello
mkdir hf_model

# Scarica solo il modello
huggingface-cli download ByteDance/Dolphin-1.5 --local-dir ./hf_model
```

### Verifica Installazione

```bash
python app/test_ocr.py
```

Dovrebbe mostrare:
```
dolphin: [OK] DISPONIBILE
```

---

## 🌟 Chandra OCR

**Repository**: [https://github.com/datalab-to/chandra](https://github.com/datalab-to/chandra)

Chandra OCR gestisce tabelle complesse, moduli e scrittura a mano mantenendo il layout completo.

### Installazione

```bash
# 1. Clona il repository
cd C:\Users\jecho\Desktop\Apps_LAC\Lac_Translate
git clone https://github.com/datalab-to/chandra.git

# 2. Installa dipendenze
cd chandra
pip install -r requirements.txt

# 3. Torna alla directory principale
cd ..
```

### Verifica Installazione

```bash
python app/test_ocr.py
```

Dovrebbe mostrare:
```
chandra: [OK] DISPONIBILE
```

---

## 📋 Dipendenze Comuni

Entrambi i progetti richiedono:

```bash
# Dipendenze base
pip install torch torchvision transformers
pip install pillow numpy

# Per Dolphin
pip install huggingface_hub

# Per Chandra (verifica requirements.txt del progetto)
```

---

## 🔧 Configurazione

### Struttura Directory Attesa

```
Lac_Translate/
├── app/
│   └── ocr_manager.py  # Gestisce tutti gli OCR
├── Dolphin/            # Repository Dolphin clonato (opzionale)
├── chandra/            # Repository Chandra clonato (opzionale)
├── hf_model/           # Modello Dolphin-1.5 (necessario per Dolphin)
└── ...
```

### Variabili d'Ambiente (Opzionale)

Puoi impostare path personalizzati tramite environment variables:

```bash
# Windows
set DOLPHIN_MODEL_PATH=C:\path\to\model
set CHANDRA_PATH=C:\path\to\chandra

# Linux/Mac
export DOLPHIN_MODEL_PATH=/path/to/model
export CHANDRA_PATH=/path/to/chandra
```

---

## 🧪 Test Integrazione

### Test Automatico

```bash
python app/test_ocr.py
```

### Test Manuale

```python
from app.ocr_manager import get_ocr_manager, OCREngine
from PIL import Image

# Crea immagine test
img = Image.new('RGB', (400, 100), color='white')
# ... aggiungi testo ...

# Test Dolphin
ocr_manager = get_ocr_manager()
text = ocr_manager.extract_text(img, engine=OCREngine.DOLPHIN, lang='eng')
print(f"Dolphin: {text}")

# Test Chandra
text = ocr_manager.extract_text(img, engine=OCREngine.CHANDRA, lang='eng')
print(f"Chandra: {text}")
```

---

## ⚠️ Note Importanti

### Dolphin OCR

1. **Modello Richiesto**: Dolphin richiede il modello pre-trained (~800MB)
   - Scarica da Hugging Face: `ByteDance/Dolphin-1.5`
   - Salva in `hf_model/` nella root del progetto

2. **GPU Consigliata**: Dolphin funziona meglio con GPU NVIDIA
   - CPU supportata ma più lenta
   - Verifica: `python -c "import torch; print(torch.cuda.is_available())"`

3. **Tempo Processing**: 
   - Dolphin è più accurato ma più lento di Tesseract
   - ~5-15 secondi per pagina (GPU), ~30-60 secondi (CPU)

### Chandra OCR

1. **Requisiti**: Verifica `requirements.txt` nel repository Chandra
   - Potrebbe richiedere dipendenze specifiche

2. **API**: Chandra potrebbe avere API diverse
   - Consulta documentazione nel repository
   - Adatta `_extract_chandra()` in `ocr_manager.py` se necessario

---

## 🐛 Troubleshooting

### Dolphin non viene rilevato

1. Verifica che `Dolphin/` o `hf_model/` esistano:
   ```bash
   ls Dolphin/
   ls hf_model/
   ```

2. Verifica che torch sia installato:
   ```bash
   python -c "import torch; print(torch.__version__)"
   ```

3. Verifica log:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   from app.ocr_manager import get_ocr_manager
   ocr = get_ocr_manager()
   ```

### Chandra non viene rilevato

1. Verifica che `chandra/` esista:
   ```bash
   ls chandra/
   ```

2. Verifica che requirements siano installati:
   ```bash
   cd chandra
   pip install -r requirements.txt
   ```

3. Controlla se ha un package installabile:
   ```bash
   pip install chandra-ocr  # Se disponibile su PyPI
   ```

---

## 📚 Risorse

- **Dolphin GitHub**: https://github.com/bytedance/Dolphin
- **Dolphin Hugging Face**: https://huggingface.co/ByteDance/Dolphin-1.5
- **Chandra GitHub**: https://github.com/datalab-to/chandra

---

## ✅ Checklist Installazione

- [ ] Repository Dolphin clonato
- [ ] Dipendenze Dolphin installate
- [ ] Modello Dolphin-1.5 scaricato in `hf_model/`
- [ ] Repository Chandra clonato
- [ ] Dipendenze Chandra installate
- [ ] Test OCR eseguito con successo
- [ ] Dolphin rilevato da `test_ocr.py`
- [ ] Chandra rilevato da `test_ocr.py`

---

**Una volta completata l'installazione, LAC TRANSLATE userà automaticamente Dolphin e Chandra quando disponibili!** 🚀

