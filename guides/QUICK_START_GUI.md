# ⚡ QUICK START GUI - LAC TRANSLATE v2.0

**Guida rapida per iniziare subito con l'interfaccia grafica**

---

## 🚀 AVVIO IMMEDIATO

### 1️⃣ **Prima Volta**
```bash
# Doppio click su:
INSTALLA_DIPENDENZE.bat
```

### 2️⃣ **Avvia App**
```bash
# Doppio click su:
AVVIA_GUI.bat
```

**Fatto! L'app si apre e sei pronto! 🎉**

---

## 🎯 INTERFACCIA PRINCIPALE

### **Barra Superiore:**
- 📁 **"Apri PDF"** - Carica documento
- 📄 **Nome file** - Mostra PDF corrente
- ⬅️ **"Prec"** - Pagina precedente
- 📊 **"Pag: X/Y"** - Pagina corrente/totale
- ➡️ **"Succ"** - Pagina successiva

### **Pannello Sinistro (Impostazioni):**
- 🔄 **Traduttore** - Google (online) o Argos (offline)
- 🌍 **Lingue** - Da/A verso
- 🎨 **Colore** - Colore testo tradotto

### **Area Centrale:**
- 📖 **"Originale"** - PDF originale (sinistra)
- 📝 **"Tradotto"** - PDF tradotto (destra)

### **Barra Inferiore:**
- ⚡ **"Traduci Pagina"** - Solo pagina corrente
- 🔄 **"Traduci Tutto"** - Intero documento
- 💾 **"Salva PDF"** - Salva risultato

---

## 📋 WORKFLOW RAPIDO

### **Step 1: Apri PDF**
1. Click **"Apri PDF"**
2. Seleziona il documento
3. L'app rileva automaticamente se è scansionato

### **Step 2: Scegli Traduttore**
- **Google** → Veloce, serve internet
- **Argos** → Privacy totale, offline

### **Step 3: Imposta Lingue**
- **Da**: Auto-rileva o seleziona
- **A**: Scegli lingua destinazione

### **Step 4: Traduci**
- **"Traduci Pagina"** → Veloce, una pagina
- **"Traduci Tutto"** → Lento, tutto il documento

### **Step 5: Salva**
- Click **"Salva PDF"**
- Il file va in `output/`

---

## 🔍 OCR AUTOMATICO

### **Come Funziona:**
1. **PDF normale** → Estrazione testo standard
2. **PDF scansionato** → OCR Tesseract automatico
3. **Formattazione** → Struttura preservata

### **Cosa Vedrai:**
```
Status bar: "⚠ PDF scansionato rilevato - traduzione limitata"
Log: "INFO - Attempting OCR extraction with Tesseract..."
Log: "INFO - OCR successful: extracted 2239 characters"
```

---

## 🎨 PERSONALIZZAZIONE

### **Colori Testo Tradotto:**
- **Rosso** - Default, ben visibile
- **Blu** - Professionale
- **Verde** - Naturale
- **Nero** - Minimalista

### **Tema:**
- **Bianco e nero** - Moderno e professionale
- **Auto-ridimensionamento** - Pagine sempre visibili
- **Scroll fluido** - Navigazione comoda

---

## ⚡ SCORCIATOIE RAPIDE

### **Navigazione:**
- **Mouse wheel** → Scroll verticale
- **Ctrl + Mouse wheel** → Zoom
- **Frecce** → Pagina precedente/successiva

### **Traduzione:**
- **"Traduci Pagina"** → Veloce per test
- **"Traduci Tutto"** → Per documenti completi

### **Salvataggio:**
- **"Salva PDF"** → Salva in `output/`
- **Nome automatico** → `originale_tradotto.pdf`

---

## 🚨 PROBLEMI COMUNI

### **"App non si avvia"**
```bash
# Verifica Python installato
python --version

# Reinstalla dipendenze
INSTALLA_DIPENDENZE.bat
```

### **"PDF non si carica"**
- Verifica che non sia protetto da password
- Prova con un PDF più semplice
- Controlla i log in `logs/`

### **"Traduzione non funziona"**
- **Google**: Verifica connessione internet
- **Argos**: Esegui `INSTALLA_DIPENDENZE.bat`
- **OCR**: Esegui `INSTALLA_OCR.bat`

### **"Testo OCR malformattato"**
- Normale per PDF scansionati complessi
- L'app formatta automaticamente
- Prova con PDF più semplici

---

## 📊 CONFRONTO VELOCE

| Caratteristica | Google | Argos | OCR |
|----------------|--------|-------|-----|
| **Velocità** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| **Privacy** | ❌ | ✅ | ✅ |
| **Qualità** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **PDF Scansionati** | ❌ | ❌ | ✅ |

---

## 💡 CONSIGLI VELOCI

### **Per Documenti Normali:**
1. Usa **Google** per velocità
2. **"Traduci Tutto"** per documenti piccoli
3. **"Traduci Pagina"** per documenti grandi

### **Per Documenti Sensibili:**
1. Usa **Argos** per privacy
2. **"Traduci Pagina"** per controllo qualità
3. Verifica risultato prima di salvare

### **Per PDF Scansionati:**
1. L'**OCR** si attiva automaticamente
2. **Formattazione** è automatica
3. **Qualità** dipende dal PDF originale

---

## 📁 FILE IMPORTANTI

### **Cartelle:**
- `app/` → Codice applicazione
- `output/` → PDF tradotti salvati
- `logs/` → Log e debug

### **File Batch:**
- `AVVIA_GUI.bat` → Avvia app
- `INSTALLA_DIPENDENZE.bat` → Installazione completa
- `INSTALLA_OCR.bat` → Solo OCR

### **Documentazione:**
- `README.md` → Guida completa
- `FEATURES.md` → Caratteristiche dettagliate
- `GUIDA_OCR.md` → Guida OCR specifica

---

## 🆕 NOVITÀ v2.0

- ✅ **OCR integrato** - PDF scansionati automatici
- ✅ **Formattazione strutturata** - Layout preservato
- ✅ **Auto-ridimensionamento** - Pagine sempre visibili
- ✅ **Tema migliorato** - Bianco e nero professionale
- ✅ **Status intelligente** - Feedback dettagliato
- ✅ **Installazione automatica** - Script batch

---

## 🎯 PRONTO!

**Ora sei pronto per tradurre qualsiasi PDF!**

1. **Apri** il PDF
2. **Scegli** il traduttore
3. **Traduci** e **salva**

**Buona traduzione! 🚀✨**

---

*LAC Translate v2.0 - Quick Start GUI*
