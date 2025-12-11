# 🌍 LAC TRANSLATE - Professional PDF Translator v3.0

**Traduttore PDF professionale con OPUS-MT e PaddleOCR - Qualità superiore, velocità eccezionale**

---

## ✨ CARATTERISTICHE v3.0

### 🔄 Traduzione di Classe Mondiale:
- **OPUS-MT** - Modelli Helsinki-NLP specializzati per ogni coppia linguistica
- **Qualità Superiore** - Nessun word-dropping, traduzioni complete e accurate
- **Velocissimo** - ~0.3s per frase (100x più veloce di modelli grandi)
- **Completamente Offline** - Privacy totale, funziona senza internet
- **7 Lingue Supportate** - Italiano, Inglese, Francese, Tedesco, Spagnolo, Portoghese, Olandese

### 🔍 OCR Avanzato (PaddleOCR):
- **PaddleOCR** - Riconoscimento ottico 3-5x più veloce di Tesseract
- **95% di Accuratezza** - Superiore a Tesseract (~85%)
- **7 Lingue OCR** - Auto-detection basata su lingua sorgente
- **Detection Automatica** - Trova e riconosce regioni di testo automaticamente
- **Layout Intelligente** - Gestisce testo ruotato, distorto e layout complessi
- **8 Metodi Estrazione** - Dalla normale alla OCR avanzata

### 📄 Funzionalità Professionali:
- ✅ Interfaccia Qt6 moderna con glassmorphism design
- ✅ Visualizzazione PDF con zoom e navigazione
- ✅ Traduzione singola pagina o documento completo
- ✅ Salvataggio PDF tradotto con layout preservato
- ✅ Font scaling dinamico per adattamento perfetto
- ✅ Fallback multi-livello (HTML → Text → Truncate)
- ✅ Debug logging completo
- ✅ **100% Offline** - Nessuna connessione richiesta dopo setup

---

## 🚀 INSTALLAZIONE RAPIDA

### Requisiti:
- Python 3.10+
- ~1GB spazio disco (modelli OPUS-MT + PaddleOCR)

### Setup:
### Setup:
```bash
# 1. Crea ambiente virtuale
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# oppure .venv\Scripts\activate  # Windows

# 2. Installa dipendenze
pip install -r requirements.txt

# 3. Avvia l'applicazione
python app/main_qt.py
```

**Nota**: I modelli OPUS-MT e PaddleOCR si scaricano automaticamente al primo utilizzo (~1GB totale).

---

## 💻 UTILIZZO

### 1️⃣ **Apri PDF**
   - Click "Apri PDF"
   - Seleziona il documento
   - **Rilevamento automatico**: L'app rileva se è scansionato

### 2️⃣ **Imposta Lingue**
   - **Origine**: Auto / English / Italiano / ...
   - **Destinazione**: Italiano / English / Español / ...

### 3️⃣ **Traduci**
   - **Traduci Pagina**: Solo pagina corrente (veloce)
   - **Traduci Tutto**: Intero documento (lento)
   - **OCR automatico**: Per PDF scansionati

### 4️⃣ **Salva**
   - Click "Salva PDF"
   - I PDF tradotti vanno nella cartella `output/`

---

## 🔍 OCR TESSERACT

### Caratteristiche:
- ✅ **Open Source** - Completamente gratuito
- ✅ **Potente** - Riconoscimento OCR avanzato
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

## 🔒 PRIVACY & SICUREZZA (100% OFFLINE)

### OPUS-MT Translation Engine:
- ✅ **Zero Cloud** - Modelli salvati localmente (~300MB per coppia linguistica)
- ✅ **GDPR Compliant** - Nessun dato trasmesso, nessun tracking
- ✅ **Perfetto per uso legale** - Contratti, documenti sensibili, privacy totale
- ✅ **Qualità professionale** - Nessun word-dropping, traduzioni complete

### PaddleOCR (offline):
- ✅ **Completamente locale** - Nessun invio dati
- ✅ **Privacy assoluta** - Tutto sul tuo PC
- ✅ **Modelli leggeri** - ~10MB, funziona ovunque
- ✅ **Velocità superiore** - 3-5x più veloce di Tesseract

**Garanzia**: Dopo il download iniziale dei modelli, LAC Translate funziona **100% offline**. 
Puoi disconnettere internet e continuare a tradurre senza limitazioni.

---

## 🌍 LINGUE SUPPORTATE (7 Lingue)

### Traduzione (OPUS-MT):
- 🇬🇧 English
- 🇮🇹 Italiano
- 🇪🇸 Español
- 🇫🇷 Français
- 🇩🇪 Deutsch
- 🇵🇹 Português
- 🇳🇱 Nederlands

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
→ La traduzione offline richiede più tempo (normale)
→ Traduci pagina per pagina invece di tutto
→ Usa un PC con buone prestazioni

### "PDF scansionato non tradotto"
→ L'OCR dovrebbe attivarsi automaticamente
→ Controlla i log per messaggi OCR
→ Verifica che Tesseract sia installato

### "Errore apertura PDF"
→ Verifica che il PDF non sia protetto da password
→ Prova ad aprire il PDF con Adobe Reader per verificare

---

## 📊 CONFRONTO TRADUTTORI

| Caratteristica | Argos | OCR |
|----------------|-------|-----|
| **Qualità** | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Velocità** | ⭐⭐⭐ | ⭐⭐ |
| **Privacy** | ✅ Offline | ✅ Offline |
| **Costo** | Gratis | Gratis |
| **Internet** | Non serve | Non serve |
| **PDF Scansionati** | ❌ No | ✅ Sì |
| **Per Avvocati** | ✅ Sì | ✅ Sì |
| **GDPR** | ✅ Compliant | ✅ Compliant |

---

## 🛠️ REQUISITI SISTEMA

- **Sistema**: Windows 10/11, macOS, Linux
- **Python**: 3.11 o superiore
- **RAM**: 4GB minimo (8GB consigliato)
- **Spazio**: 1GB per modelli Argos + Tesseract
- **Internet**: Solo per download iniziale modelli
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