# 🌍 LAC TRANSLATE - PDF Translator v2.0

**Traduttore PDF professionale con OCR integrato, privacy totale e interfaccia moderna**

---

## ✨ CARATTERISTICHE v2.0

### 🔄 Due Motori di Traduzione:
- **Google Translate** - Online, qualità eccellente (documenti normali)
- **Argos Translate** - Offline, privacy totale sul PC (documenti sensibili)

### 🔍 OCR Integrato (NUOVO!):
- **Tesseract OCR** - Riconoscimento ottico caratteri open source
- **8 metodi estrazione** - Dalla normale alla OCR avanzata
- **Rilevamento automatico** - Identifica PDF scansionati
- **Formattazione strutturata** - Riconosce sezioni, sottosezioni e liste

### 📄 Funzionalità:
- ✅ Visualizzazione affiancata (originale + traduzione)
- ✅ Navigazione pagina per pagina
- ✅ Traduzione singola pagina o intero documento
- ✅ Salvataggio PDF tradotto
- ✅ Cache intelligente
- ✅ Scelta colore testo tradotto
- ✅ **Auto-ridimensionamento** - Pagine sempre visibili completamente
- ✅ **Tema bianco e nero** - Interfaccia moderna e professionale
- ✅ **Status bar intelligente** - Feedback dettagliato

---

## 🚀 INSTALLAZIONE (Prima volta)

### 1. Installa tutto (dipendenze + OCR):
```
Doppio click su: INSTALLA_DIPENDENZE.bat
```

### 2. Solo OCR (se già installato):
```
Doppio click su: INSTALLA_OCR.bat
```

### 3. Installazione automatica OCR:
```
Doppio click su: INSTALLA_OCR_AUTO.ps1
```

Oppure manualmente:
```bash
pip install -r requirements.txt
winget install UB-Mannheim.TesseractOCR
cd app
python setup_argos_models.py
```

---

## 💻 AVVIO

```
Doppio click su: AVVIA_GUI.bat
```

Oppure da terminale:
```bash
cd app
python pdf_translator_gui.py
```

---

## 📖 GUIDA RAPIDA

### 1️⃣ **Apri PDF**
   - Click "Apri PDF"
   - Seleziona il documento
   - **Rilevamento automatico**: L'app rileva se è scansionato

### 2️⃣ **Scegli Traduttore**
   - **Google Translate**: Per documenti normali (serve internet)
   - **Argos Translate**: Per documenti privati (tutto offline)

### 3️⃣ **Imposta Lingue**
   - **Origine**: Auto / English / Italiano / ...
   - **Destinazione**: Italiano / English / Español / ...

### 4️⃣ **Traduci**
   - **Traduci Pagina**: Solo pagina corrente (veloce)
   - **Traduci Tutto**: Intero documento (lento)
   - **OCR automatico**: Per PDF scansionati

### 5️⃣ **Salva**
   - Click "Salva PDF"
   - I PDF tradotti vanno nella cartella `output/`

---

## 🔍 OCR TESSERACT

### Caratteristiche:
- ✅ **Open Source** - Completamente gratuito
- ✅ **Potente** - Sviluppato da Google
- ✅ **Multi-lingua** - Supporta 100+ lingue
- ✅ **Accurato** - Ottimo con PDF di alta qualità
- ✅ **Privacy** - Tutto locale, nessun cloud

### Metodi di Estrazione (8 totali):
1. **Normale** - Estrazione standard PyMuPDF
2. **Preserva spazi** - Con flag TEXT_PRESERVE_WHITESPACE
3. **Dehyphenate** - Con flag TEXT_DEHYPHENATE
4. **Da blocchi** - Ricostruzione da blocchi di testo
5. **Da dizionario** - Estrazione dettagliata per carattere
6. **Da parole** - Ricostruzione da parole singole
7. **Da HTML** - Estrazione HTML con pulizia
8. **OCR Tesseract** - Riconoscimento ottico caratteri

### Formattazione Strutturata:
- **Sezioni principali**: `1. TITOLO` → Grassetto, 12pt
- **Sottosezioni**: `1.1. Sottotitolo` → Grassetto, 11pt
- **Liste**: `a) Elemento` → Indentato, margini
- **Paragrafi**: Testo normale → 10pt, interlinea 1.4

---

## 🔒 PRIVACY & SICUREZZA

### Google Translate (online):
- ⚠️ Invia testo ai server Google
- ✅ Qualità eccellente
- ❌ NON usare per documenti sensibili/legali

### Argos Translate (offline):
- ✅ Tutto sul tuo PC
- ✅ Privacy totale - GDPR compliant
- ✅ Perfetto per: contratti, documenti legali, dati sensibili
- ⚠️ Qualità buona (leggermente inferiore a Google)

### OCR Tesseract (offline):
- ✅ Tutto locale, nessun invio dati
- ✅ Privacy totale
- ✅ Perfetto per PDF scansionati

---

## 🌍 LINGUE SUPPORTATE

### Argos Translate (offline):
- 🇬🇧 English
- 🇮🇹 Italiano
- 🇪🇸 Español
- 🇫🇷 Français
- 🇩🇪 Deutsch
- 🇵🇹 Português
- 🇷🇺 Русский

### Google Translate (online):
Oltre 100 lingue!

### OCR Tesseract:
100+ lingue (inglese preinstallato)

---

## 📁 STRUTTURA CARTELLE

```
Lac_Translate/
│
├── AVVIA_GUI.bat              ← Avvia applicazione
├── INSTALLA_DIPENDENZE.bat    ← Installazione completa
├── INSTALLA_OCR.bat           ← Solo OCR
├── INSTALLA_OCR_AUTO.ps1      ← OCR automatico
├── README.md                  ← Questa guida
├── FEATURES.md                ← Caratteristiche dettagliate
├── QUICK_START_GUI.md         ← Guida rapida GUI
├── GUIDA_OCR.md               ← Guida OCR
├── CHANGELOG.md               ← Cronologia modifiche
├── requirements.txt           ← Dipendenze Python complete
│
├── app/                       ← Codice applicazione
│   ├── pdf_translator_gui.py  ← GUI principale con OCR
│   ├── setup_argos_models.py  ← Setup modelli Argos
│   └── deep_translator/       ← Libreria traduzione
│
├── output/                    ← PDF tradotti (salvati qui)
│
└── logs/                      ← Log applicazione
    └── pdf_translator.log
```

---

## ❓ PROBLEMI COMUNI

### "Python non trovato"
→ Installa Python 3.11+ da: https://www.python.org/downloads/
→ Durante installazione, seleziona "Add Python to PATH"

### "Modelli Argos mancanti"
→ Esegui: `INSTALLA_DIPENDENZE.bat`
→ Oppure: `cd app && python setup_argos_models.py`

### "OCR non funziona"
→ Esegui: `INSTALLA_OCR.bat`
→ Oppure: `winget install UB-Mannheim.TesseractOCR`

### "Traduzione lenta"
→ Argos è più lento di Google (normale per offline)
→ Usa Google per velocità
→ Traduci pagina per pagina invece di tutto

### "PDF scansionato non tradotto"
→ L'OCR dovrebbe attivarsi automaticamente
→ Controlla i log per messaggi OCR
→ Verifica che Tesseract sia installato

### "Errore apertura PDF"
→ Verifica che il PDF non sia protetto da password
→ Prova ad aprire il PDF con Adobe Reader per verificare

---

## 📊 CONFRONTO TRADUTTORI

| Caratteristica | Google | Argos | OCR |
|----------------|--------|-------|-----|
| **Qualità** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Velocità** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| **Privacy** | ❌ Online | ✅ Offline | ✅ Offline |
| **Costo** | Gratis | Gratis | Gratis |
| **Internet** | Richiesto | Non serve | Non serve |
| **PDF Scansionati** | ❌ No | ❌ No | ✅ Sì |
| **Per Avvocati** | ❌ No | ✅ Sì | ✅ Sì |
| **GDPR** | ⚠️ Limitato | ✅ Compliant | ✅ Compliant |

---

## 🛠️ REQUISITI SISTEMA

- **Sistema**: Windows 10/11, macOS, Linux
- **Python**: 3.11 o superiore
- **RAM**: 4GB minimo (8GB consigliato)
- **Spazio**: 1GB per modelli Argos + Tesseract
- **Internet**: Solo per Google Translate
- **Tesseract OCR**: Installato automaticamente

---

## 🆕 NOVITÀ v2.0

- ✅ **OCR Tesseract integrato**
- ✅ **Formattazione strutturata**
- ✅ **Auto-ridimensionamento pagine**
- ✅ **Rilevamento PDF scansionati**
- ✅ **8 metodi estrazione testo**
- ✅ **Tema bianco e nero migliorato**
- ✅ **Status bar intelligente**
- ✅ **Script installazione automatica**

---

## 📞 SUPPORTO

Per problemi o domande:
- Controlla i log in: `logs/pdf_translator.log`
- Repository originale: https://github.com/davideuler/pdf-translator-for-human

---

## 📜 LICENZA

Basato su **pdf-translator-for-human** di davideuler
Licenza: Apache 2.0

---

**Buona traduzione! 🎉**

*LAC Translate v2.0 - Privacy-first PDF translation with OCR*