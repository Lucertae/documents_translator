# 🔍 GUIDA OCR - LAC TRANSLATE v2.0

**Guida completa per l'uso dell'OCR integrato con Tesseract**

---

## 🎯 COS'È L'OCR?

**OCR** (Optical Character Recognition) = **Riconoscimento Ottico Caratteri**

L'OCR permette di "leggere" il testo da immagini e PDF scansionati, convertendolo in testo digitale che può essere tradotto.

---

## 🔧 INSTALLAZIONE OCR

### Metodo 1: Automatico (Consigliato)
```bash
# Esegui il file batch
INSTALLA_OCR.bat
```

### Metodo 2: PowerShell (Windows)
```bash
# Esegui lo script PowerShell
INSTALLA_OCR_AUTO.ps1
```

### Metodo 3: Manuale
```bash
# Installa Tesseract OCR
winget install UB-Mannheim.TesseractOCR

# Installa pacchetti Python
pip install pytesseract pdf2image
```

---

## 🚀 COME FUNZIONA

### 1. **Rilevamento Automatico**
L'app rileva automaticamente se un PDF è scansionato:
- ✅ **PDF normale**: Usa estrazione testo standard
- 🔍 **PDF scansionato**: Attiva OCR automaticamente

### 2. **Cascata di 8 Metodi**
Se il testo normale non funziona, prova:
1. Estrazione normale
2. Con preserve whitespace
3. Con dehyphenate
4. Da blocchi di testo
5. Da dizionario dettagliato
6. Da parole singole
7. Da HTML
8. **OCR Tesseract** ← Entra in azione!

### 3. **Formattazione Strutturata**
Il testo OCR viene formattato automaticamente:
- **Sezioni**: `1. TITOLO` → Grassetto, 12pt
- **Sottosezioni**: `1.1. Sottotitolo` → Grassetto, 11pt
- **Liste**: `a) Elemento` → Indentato
- **Paragrafi**: Testo normale → 10pt

---

## 📊 TIPI DI PDF SUPPORTATI

### ✅ **PDF Normali** (con testo selezionabile)
- Estrazione standard veloce
- Layout preservato perfettamente
- Traduzione blocco per blocco

### 🔍 **PDF Scansionati** (solo immagini)
- OCR Tesseract automatico
- Formattazione strutturata
- Traduzione chunk per chunk

### ⚠️ **PDF Ibridi** (testo + immagini)
- Combina estrazione normale + OCR
- Risultato ottimale

---

## 🎨 QUALITÀ OCR

### **Fattori che influenzano la qualità:**

#### ✅ **Ottima Qualità:**
- PDF ad alta risoluzione (300+ DPI)
- Testo nero su sfondo bianco
- Font chiari e leggibili
- Contrasto elevato
- Pagine dritte (non ruotate)

#### ⚠️ **Qualità Media:**
- PDF a risoluzione media (150-300 DPI)
- Testo colorato su sfondo colorato
- Font piccoli o stilizzati
- Pagine leggermente ruotate

#### ❌ **Qualità Bassa:**
- PDF a bassa risoluzione (<150 DPI)
- Testo sfocato o distorto
- Sfondo complesso o rumore
- Pagine molto ruotate

---

## 🔧 CONFIGURAZIONE AVANZATA

### **Lingue Supportate:**
```python
# Inglese (preinstallato)
ocr_text = pytesseract.image_to_string(img, lang='eng')

# Italiano
ocr_text = pytesseract.image_to_string(img, lang='ita')

# Multi-lingua
ocr_text = pytesseract.image_to_string(img, lang='eng+ita')
```

### **Parametri di Qualità:**
```python
# Alta risoluzione per OCR migliore
pix = page.get_pixmap(matrix=pymupdf.Matrix(2.0, 2.0))  # 2x resolution
```

---

## 📝 ESEMPI PRATICI

### **Contratto Legale:**
```
INPUT (PDF scansionato):
"3. PROCUREMENT OF CONTRACTUAL PRODUCTS
3.1. Trotec shall be solely responsible..."

OUTPUT (OCR + Traduzione):
"3. APPROVVIGIONAMENTO PRODOTTI CONTRATTUALI
3.1. Trotec sarà l'unico responsabile..."
```

### **Documento Tecnico:**
```
INPUT (PDF scansionato):
"2.6. Any contract with sub-distributors..."

OUTPUT (OCR + Traduzione):
"2.6. Qualsiasi contratto con sub-distributori..."
```

---

## 🚨 RISOLUZIONE PROBLEMI

### **"OCR non funziona"**
1. Verifica che Tesseract sia installato
2. Controlla i log: `logs/pdf_translator.log`
3. Prova a reinstallare: `INSTALLA_OCR.bat`

### **"Qualità OCR bassa"**
1. Verifica la risoluzione del PDF originale
2. Prova a migliorare il contrasto
3. Ruota la pagina se necessario

### **"Testo OCR malformattato"**
1. L'app formatta automaticamente
2. Controlla che il PDF non sia troppo complesso
3. Prova con un PDF più semplice

### **"Traduzione OCR lenta"**
1. OCR è più lento dell'estrazione normale
2. Traduci pagina per pagina invece di tutto
3. Usa Google Translate per velocità

---

## 📊 CONFRONTO PRESTAZIONI

| Metodo | Velocità | Qualità | Privacy |
|--------|----------|---------|---------|
| **Estrazione normale** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ |
| **OCR Tesseract** | ⭐⭐ | ⭐⭐⭐⭐ | ✅ |
| **Google Translate** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ❌ |

---

## 💡 CONSIGLI PER MIGLIORI RISULTATI

### **Prima di usare OCR:**
1. **Scansiona ad alta risoluzione** (300+ DPI)
2. **Usa contrasto elevato** (nero su bianco)
3. **Mantieni pagine dritte**
4. **Evita sfondi complessi**

### **Durante l'uso:**
1. **Traduci pagina per pagina** per controllo qualità
2. **Verifica il risultato** prima di salvare
3. **Usa Google per velocità** se privacy non è critica
4. **Usa Argos per privacy** se dati sono sensibili

---

## 🔍 LOG E DEBUGGING

### **Messaggi di Log:**
```
INFO - Attempting OCR extraction with Tesseract...
INFO - OCR successful: extracted 2239 characters
INFO - Translated chunk 1/4
INFO - Successfully translated OCR text (4 chunks)
```

### **File di Log:**
- Posizione: `logs/pdf_translator.log`
- Contiene: Tutti i dettagli dell'elaborazione OCR
- Utile per: Debug e risoluzione problemi

---

## 🆕 NOVITÀ v2.0

- ✅ **OCR integrato** - Nessuna configurazione manuale
- ✅ **Rilevamento automatico** - Identifica PDF scansionati
- ✅ **8 metodi estrazione** - Cascata intelligente
- ✅ **Formattazione strutturata** - Layout preservato
- ✅ **Installazione automatica** - Script batch e PowerShell
- ✅ **Logging dettagliato** - Debug completo

---

## 📞 SUPPORTO

Per problemi specifici OCR:
1. Controlla i log in `logs/pdf_translator.log`
2. Verifica che Tesseract sia installato
3. Prova con un PDF di test semplice
4. Reinstalla OCR se necessario

---

**Buon OCR! 🔍✨**

*LAC Translate v2.0 - OCR integrato per PDF scansionati*
