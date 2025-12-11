# 🗺️ LAC TRANSLATE - ROADMAP SVILUPPO

**Data creazione:** 4 Dicembre 2025  
**Versione attuale:** v2.0 (MVP Tkinter)  
**Target:** Contratto LUCERTAE SRLS - 3 Milestone

---

## 📊 STATO ATTUALE CODEBASE

### ✅ GIÀ IMPLEMENTATO
- [x] GUI Tkinter funzionante con tema bianco/nero
- [x] Traduzione offline: Argos Translate (Google Translate rimosso)
- [x] **7 lingue supportate**: Italiano, English, Español, Français, Deutsch, Português, Nederlands
- [x] 8 metodi estrazione testo progressivi
- [x] **OCR Tesseract multi-lingua** (ita, eng, spa, fra, deu, por, nld)
- [x] **Auto-detection lingua OCR** basata su selezione utente
- [x] Visualizzazione affiancata PDF originale/tradotto
- [x] Navigazione pagina per pagina
- [x] Cache traduzione per pagina
- [x] Export PDF tradotto
- [x] Logging dettagliato in logs/
- [x] Auto-scaling immagini PDF su canvas
- [x] Status bar con feedback colorato
- [x] Argos Translate con 14 modelli installati
- [x] PyMuPDF (fitz) per manipolazione PDF
- [x] Threading per operazioni lunghe

### ❌ MANCANTE / DA IMPLEMENTARE
- [ ] Interfaccia Qt (richiesto da contratto - da negoziare)
- [ ] Drag-and-drop files
- [ ] Export TXT e DOCX
- [ ] Tema scuro/chiaro switchable
- [ ] Supporto file immagine diretto (JPG, PNG, TIFF, BMP)
- [ ] Scorciatoie tastiera
- [ ] Barre progresso determinate (ora solo indeterminate)
- [ ] Installer Windows .exe
- [ ] Script build per packaging
- [ ] Documentazione tecnica completa
- [ ] Manuale utente PDF
- [ ] Video tutorial
- [ ] Test suite automatici
- [ ] Profiling performance/memoria
- [ ] Gestione configurazione utente (settings.json)

---

## 🎯 MILESTONE 1 - BUILD BASE WINDOWS (3 settimane)

**Obiettivo:** Installer .exe funzionante con funzionalità base offline

### 1.1 PULIZIA CODEBASE (3 giorni)
**Priorità:** ALTA - Da fare SUBITO

#### ✅ COMPLETATO: Aggiungere Olandese (Nederlands)
- [x] Aggiunto "Nederlands": "nl" a `ARGOS_LANG_MAP`
- [x] Verificato modelli EN↔NL installati
- [x] Aggiornato README con 7 lingue complete
- [x] Rimosso Russo (non nel contratto)

**Status:** ✅ Completato 4 Dic 2025 - Commit 683b844

---

#### Rimuovere Google Translate (conformità offline)
- [ ] Eliminare `from deep_translator import GoogleTranslator`
- [ ] Rimuovere radio button "Google Translate" dalla GUI
- [ ] Rimuovere logica GoogleTranslator da `get_translator()`
- [ ] Aggiornare README per rimuovere riferimenti Google
- [ ] Testare che Argos funzioni come unico traduttore
- [ ] Aggiornare messaggi UI per indicare solo offline

**File da modificare:**
- `app/pdf_translator_gui.py` (linee 12, 150, 320-330, 606-612)
- `README.md`, `FEATURES.md`, `QUICK_START_GUI.md`

**Motivazione contratto:** Art. 1.3 "interamente full offline"

---

### 1.2 OCR MULTI-LINGUA ✅ COMPLETATO
**Priorità:** ALTA
**Status:** ✅ Completato 4 Dic 2025

#### ✅ Configurare Tesseract per 7 lingue
- [x] Installati modelli Tesseract: ita, fra, deu, spa, por, nld
- [x] Creata funzione `get_tesseract_lang()` per auto-detect
- [x] Modificato `extract_text_improved()` per usare lang corretta
- [x] Parametro OCR dinamico basato su lingua sorgente selezionata
- [x] Creata mappa `TESSERACT_LANG_MAP` completa

**Implementazione:**
- Creata funzione `get_tesseract_lang()` in `pdf_translator_gui.py`
- Aggiunta mappa `TESSERACT_LANG_MAP` con 7 lingue + Auto
- Modificate linee 680-690 per OCR dinamico
- Modelli Tesseract installati su sistema Linux

**Verifica lingue disponibili:**
```bash
tesseract --list-langs
# Output: deu, eng, fra, ita, nld, por, spa ✅
```

**Commit:** `683b844 - feat: Add Nederlands language and multi-language OCR support`

**Motivazione contratto:** ✅ Allegato A punto 5.3 - CONFORME

---

### 1.3 SUPPORTO FILE IMMAGINE (3 giorni)
**Priorità:** MEDIA

#### Accettare JPG, PNG, TIFF, BMP come input
- [ ] Modificare `select_pdf()` per accettare immagini
- [ ] Creare funzione `load_image()` per convertire img→PDF temporaneo
- [ ] Usare PyMuPDF per creare PDF da immagine
- [ ] Applicare OCR direttamente su immagini
- [ ] Gestire multi-immagine (batch conversion)

**File da modificare:**
- `app/pdf_translator_gui.py` linee 435-450

**Codice esempio:**
```python
def load_image(self, image_path):
    """Converte immagine in PDF temporaneo per elaborazione"""
    img = Image.open(image_path)
    temp_pdf = OUTPUT_DIR / f"temp_{Path(image_path).stem}.pdf"
    img.save(temp_pdf, "PDF", resolution=300.0)
    self.pdf_path = str(temp_pdf)
    self.load_pdf()
```

**Motivazione contratto:** Allegato A punto 1.2

---

### 1.4 WINDOWS INSTALLER (6 giorni)
**Priorità:** CRITICA - Blocca M1

#### Setup PyInstaller / Nuitka
- [ ] Scegliere tool: PyInstaller (più semplice) vs Nuitka (più veloce)
- [ ] Creare `build.py` script per packaging
- [ ] Configurare `.spec` file per PyInstaller
- [ ] Includere tutti i modelli Argos (~300MB)
- [ ] Includere Tesseract binari Windows (~150MB)
- [ ] Includere modelli Tesseract 7 lingue (~200MB)
- [ ] Testare eseguibile su Windows 10/11 clean install
- [ ] Firma digitale (opzionale, costa €100-300/anno)

**Stima dimensione finale:** ~800MB (NON 500MB come da contratto!)

**File da creare:**
- `build/build.py`
- `build/LacTranslate.spec`
- `build/installer.iss` (Inno Setup per installer wizard)

**Esempio build.py:**
```python
import PyInstaller.__main__
import shutil
from pathlib import Path

PyInstaller.__main__.run([
    'app/pdf_translator_gui.py',
    '--name=LacTranslate',
    '--onefile',
    '--windowed',
    '--icon=assets/icon.ico',
    '--add-data=models;models',
    '--add-binary=tesseract/tesseract.exe;tesseract',
    '--hidden-import=argostranslate',
    '--hidden-import=pytesseract',
    '--clean',
])
```

**Testing Windows:**
- [ ] VM Windows 10 Pro (build 1809+)
- [ ] VM Windows 11
- [ ] Test senza Python installato
- [ ] Test senza internet (solo Argos)
- [ ] Verifica RAM usage < 500MB

**Motivazione contratto:** Allegato A punto 4.1, Allegato B M1

---

### 1.5 DOCUMENTAZIONE TECNICA BASE (3 giorni)
**Priorità:** MEDIA

#### Commenti inline e architettura
- [ ] Aggiungere docstring a tutte le funzioni
- [ ] Documentare classe `ArgosTranslator`
- [ ] Documentare classe `PDFTranslatorGUI`
- [ ] Creare `docs/ARCHITECTURE.md` con diagramma componenti
- [ ] Creare `docs/API.md` con metodi pubblici
- [ ] Aggiornare `README.md` con sezione sviluppatori

**File da creare:**
- `docs/ARCHITECTURE.md`
- `docs/API.md`
- `docs/BUILD.md` (come compilare)

**Motivazione contratto:** Allegato A punto 8, Art. 9.5

---

## 🔧 MILESTONE 2 - BUG FIXING E OTTIMIZZAZIONE (3 settimane)

**Obiettivo:** Versione stabile testata su 10 PDF benchmark

### 2.1 SISTEMA TEST AUTOMATICI (4 giorni)
**Priorità:** ALTA

#### Creare test suite con pytest
- [ ] Setup `tests/` directory
- [ ] Test estrazione testo da 10 PDF forniti
- [ ] Test traduzione EN→IT, IT→EN
- [ ] Test performance (tempo, memoria)
- [ ] Test OCR su PDF scansionati
- [ ] Test edge cases (PDF vuoto, corrotto, criptato)
- [ ] CI/CD con GitHub Actions (opzionale)

**File da creare:**
- `tests/test_extraction.py`
- `tests/test_translation.py`
- `tests/test_ocr.py`
- `tests/test_performance.py`
- `tests/fixtures/` (10 PDF benchmark)

**Esempio test:**
```python
import pytest
from app.pdf_translator_gui import extract_text_improved

def test_extract_normal_pdf():
    doc = pymupdf.open("tests/fixtures/sample_en.pdf")
    text = extract_text_improved(doc[0])
    assert len(text) > 100
    assert "sample" in text.lower()
```

**Motivazione contratto:** Allegato B M2 "Test su 10 file PDF benchmark"

---

### 2.2 PROFILING PERFORMANCE (3 giorni)
**Priorità:** ALTA

#### Misurare e ottimizzare
- [ ] Profiling con `cProfile` e `memory_profiler`
- [ ] Misurare tempo avvio applicazione (target <5s)
- [ ] Misurare tempo caricamento PDF 10MB (target <3s)
- [ ] Misurare tempo OCR pagina A4 300dpi (target <10s)
- [ ] **Misurare tempo traduzione 1000 parole Argos** (realistico 30-45s!)
- [ ] Ottimizzare chunking traduzione
- [ ] Ottimizzare rendering PDF (cache pixmap)

**File da creare:**
- `scripts/benchmark.py`
- `docs/PERFORMANCE_REPORT.md`

**Codice benchmark:**
```python
import time
import pymupdf
from app.pdf_translator_gui import extract_text_improved

def benchmark_extraction(pdf_path):
    start = time.time()
    doc = pymupdf.open(pdf_path)
    text = extract_text_improved(doc[0])
    elapsed = time.time() - start
    return elapsed, len(text)

# Test su 10 PDF
results = []
for pdf in PDF_BENCHMARK_LIST:
    elapsed, chars = benchmark_extraction(pdf)
    results.append((pdf, elapsed, chars))
```

**Motivazione contratto:** Allegato A punto 2.1, 2.2

---

### 2.3 GESTIONE MEMORIA OTTIMIZZATA (4 giorni)
**Priorità:** ALTA

#### Ridurre footprint RAM
- [ ] Implementare cache LRU per pagine tradotte (max 10 pagine)
- [ ] Liberare pixmap dopo rendering
- [ ] Garbage collection esplicito per PDF grandi
- [ ] Elaborazione streaming per file >50MB
- [ ] Monitoraggio RAM real-time in status bar

**Codice da aggiungere:**
```python
from functools import lru_cache
import gc

class PDFTranslatorGUI:
    def __init__(self):
        self.max_cache_pages = 10
        self.translated_pages = {}  # dict invece di list
    
    def translate_page(self, page_num):
        # Cleanup cache se pieno
        if len(self.translated_pages) > self.max_cache_pages:
            oldest = min(self.translated_pages.keys())
            del self.translated_pages[oldest]
            gc.collect()
        # ... resto codice
```

**Motivazione contratto:** Allegato A punto 2.2 "RAM <500MB"

---

### 2.4 GESTIONE ERRORI ROBUSTA (3 giorni)
**Priorità:** MEDIA

#### Try/catch e user feedback
- [ ] Gestire PDF corrotti/criptati
- [ ] Gestire timeout traduzione (Argos lento)
- [ ] Gestire crash Tesseract
- [ ] Messaggi errore user-friendly
- [ ] Logging dettagliato in `logs/errors.log`
- [ ] Recovery automatico da crash (salva stato)

**File da creare:**
- `app/error_handler.py`

**Codice esempio:**
```python
class TranslationError(Exception):
    """Errore durante traduzione"""
    pass

def safe_translate(translator, text, timeout=60):
    """Traduci con timeout e retry"""
    try:
        # Usa threading con timeout
        result = [None]
        def _translate():
            result[0] = translator.translate(text)
        
        thread = threading.Thread(target=_translate)
        thread.start()
        thread.join(timeout)
        
        if thread.is_alive():
            raise TranslationError(f"Timeout dopo {timeout}s")
        
        return result[0]
    except Exception as e:
        logging.error(f"Translation failed: {e}")
        raise TranslationError(str(e))
```

**Motivazione contratto:** Allegato A punto 2.3, 3.2

---

### 2.5 BUG FIX SU FEEDBACK COMMITTENTE (5 giorni)
**Priorità:** CRITICA - Dipende da M1

#### Dopo ricezione 10 PDF benchmark
- [ ] Analizzare report committente
- [ ] Riprodurre ogni bug
- [ ] Fixare in ordine priorità
- [ ] Re-testare su tutti i 10 PDF
- [ ] Creare regression test

**Strategia:**
1. Creare issue GitHub per ogni bug
2. Assegnare priorità (P0-P3)
3. Fixare P0 (blocker) entro 3 giorni
4. Fixare P1-P2 entro 10 giorni
5. P3 (nice-to-have) opzionali

**Motivazione contratto:** Allegato B M2, Art. 5.2

---

## 🎨 MILESTONE 3 - GUI PROFESSIONALE (4-8 settimane)

**DECISIONE CRITICA:** Qt completo (6-8 sett, €3.500) vs Tkinter migliorato (4 sett, €1.500)

### OPZIONE A - TKINTER MIGLIORATO (4 settimane, €1.500)
**Priorità:** Da negoziare con committente

#### 3A.1 Tema Scuro/Chiaro (3 giorni)
- [ ] Creare `themes.py` con due temi
- [ ] Menu View → Switch Theme
- [ ] Persistere scelta in config.json
- [ ] Animazione smooth transition

**Codice esempio:**
```python
THEMES = {
    "light": {
        'bg': '#ffffff',
        'text': '#000000',
        'accent': '#0066cc',
        # ... altri colori
    },
    "dark": {
        'bg': '#1e1e1e',
        'text': '#ffffff',
        'accent': '#4da6ff',
        # ... altri colori
    }
}

def apply_theme(self, theme_name):
    """Applica tema dinamicamente"""
    theme = THEMES[theme_name]
    self.colors = theme
    self.setup_style()
    # Refresh UI components
```

---

#### 3A.2 Drag-and-Drop Files (2 giorni)
- [ ] Abilitare drop su canvas sinistro
- [ ] Supportare drag multipli (batch)
- [ ] Feedback visivo durante drag
- [ ] Auto-load primo file droppato

**Codice esempio:**
```python
from tkinterdnd2 import DND_FILES, TkinterDnD

root = TkinterDnD.Tk()  # invece di tk.Tk()

def on_drop(event):
    files = root.tk.splitlist(event.data)
    for file in files:
        if file.endswith('.pdf'):
            self.pdf_path = file
            self.load_pdf()
            break

self.original_canvas.drop_target_register(DND_FILES)
self.original_canvas.dnd_bind('<<Drop>>', on_drop)
```

**Dipendenza:** `pip install tkinterdnd2`

---

#### 3A.3 Export TXT e DOCX (4 giorni)
- [ ] Implementare `export_txt()`
- [ ] Implementare `export_docx()` con python-docx
- [ ] Mantenere formattazione (bold, italic)
- [ ] Menu File → Export → TXT/PDF/DOCX
- [ ] Batch export (tutte le pagine)

**Codice esempio:**
```python
from docx import Document
from docx.shared import Pt, RGBColor

def export_docx(self, output_path):
    """Esporta traduzione in DOCX"""
    doc = Document()
    
    for page_num in range(self.current_doc.page_count):
        if self.translated_pages.get(page_num):
            # Estrai testo tradotto
            page = self.translated_pages[page_num][0]
            text = page.get_text()
            
            # Aggiungi a DOCX
            paragraph = doc.add_paragraph(text)
            paragraph.style.font.size = Pt(11)
            
            # Page break tra pagine
            doc.add_page_break()
    
    doc.save(output_path)
    logging.info(f"Exported DOCX: {output_path}")
```

**Dipendenza:** `pip install python-docx`

---

#### 3A.4 Scorciatoie Tastiera (2 giorni)
- [ ] Ctrl+O → Apri PDF
- [ ] Ctrl+S → Salva PDF
- [ ] Ctrl+T → Traduci pagina corrente
- [ ] Ctrl+Shift+T → Traduci tutto
- [ ] PgUp/PgDown → Naviga pagine
- [ ] Ctrl+, → Impostazioni
- [ ] F11 → Fullscreen

**Codice esempio:**
```python
def setup_keyboard_shortcuts(self):
    """Configura scorciatoie tastiera"""
    self.root.bind('<Control-o>', lambda e: self.select_pdf())
    self.root.bind('<Control-s>', lambda e: self.save_pdf())
    self.root.bind('<Control-t>', lambda e: self.translate_current_page())
    self.root.bind('<Control-T>', lambda e: self.translate_all_pages())
    self.root.bind('<Next>', lambda e: self.next_page())  # PgDown
    self.root.bind('<Prior>', lambda e: self.prev_page())  # PgUp
    self.root.bind('<F11>', lambda e: self.toggle_fullscreen())
```

---

#### 3A.5 Barre Progresso Determinate (2 giorni)
- [ ] Sostituire `mode='indeterminate'` con `mode='determinate'`
- [ ] Calcolare % completamento
- [ ] Mostrare "Pagina 5/20 (25%)"
- [ ] ETA (estimated time remaining)

**Codice esempio:**
```python
def translate_all_pages(self):
    total = self.current_doc.page_count
    self.progress.config(mode='determinate', maximum=total)
    
    for i in range(total):
        # Traduci pagina
        self.translate_page(i)
        
        # Aggiorna progresso
        self.progress['value'] = i + 1
        percent = int((i + 1) / total * 100)
        self.update_status(f"⏳ Traduzione: {i+1}/{total} ({percent}%)")
        self.root.update_idletasks()
```

---

#### 3A.6 Configurazione Utente (3 giorni)
- [ ] Creare `settings.json` per preferenze
- [ ] Salvare: tema, lingue default, colore testo, ultima directory
- [ ] Menu Impostazioni → Preferenze
- [ ] Reset to defaults

**File da creare:**
- `app/config.py`

**Codice esempio:**
```python
import json
from pathlib import Path

CONFIG_FILE = BASE_DIR / "config.json"

DEFAULT_CONFIG = {
    "theme": "light",
    "default_source_lang": "English",
    "default_target_lang": "Italiano",
    "text_color": "Rosso",
    "last_directory": str(OUTPUT_DIR),
    "window_size": "1600x900",
    "ocr_lang": "eng"
}

def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return DEFAULT_CONFIG.copy()

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)
```

---

### OPZIONE B - MIGRAZIONE QT COMPLETA (6-8 settimane, €3.500)
**Priorità:** Solo se committente aumenta budget

**SCONSIGLIATO:** Troppo rischioso per tempi/budget attuali

#### Stima effort Qt:
- Setup Qt Designer + PySide6: 2 giorni
- Riscrittura UI da zero: 15 giorni
- Porting logica business: 5 giorni
- Drag-and-drop Qt: 2 giorni
- Temi Qt (QSS): 3 giorni
- Export multi-formato: 3 giorni
- Testing Qt: 5 giorni
- Bug fixing Qt: 5 giorni

**Totale: 40 giorni (8 settimane)**

**Solo se committente accetta:**
- Tempo: 6-8 settimane
- Compenso M3: €3.500-4.000
- Possibilità subappalto designer UI

---

## 📚 DELIVERABLE FINALI

### Documentazione (5 giorni)
- [ ] `docs/MANUALE_UTENTE.pdf` (20-30 pagine)
- [ ] `docs/ARCHITECTURE.md` tecnico
- [ ] `docs/API.md` reference
- [ ] `docs/BUILD.md` istruzioni build
- [ ] `docs/TROUBLESHOOTING.md` FAQ

### Video Tutorial (3 giorni)
- [ ] Video 1: Installazione (3 min)
- [ ] Video 2: Prima traduzione (5 min)
- [ ] Video 3: Funzioni avanzate (7 min)
- [ ] Editing con Camtasia/OBS
- [ ] Upload su YouTube/Vimeo privato

---

## 🔥 QUICK WINS - DA FARE SUBITO (Questa settimana)

### ✅ Priorità P0 - COMPLETATI (4 Dic 2025)
1. ✅ **Aggiunto Olandese** → 7 lingue complete
2. ✅ **OCR multi-lingua** → Auto-detection implementata
3. ✅ **Rimosso Russo** → Solo lingue da contratto

### Priorità P0 - CRITICO (1-2 giorni)
1. **Rimuovere Google Translate** → Conformità contratto offline
2. **Fix logging** → Evita crash su PDF problematici
3. **Test Argos performance** → Benchmark reale 1000 parole

### Priorità P1 - MOLTO IMPORTANTE (3-4 giorni)
5. **OCR multi-lingua setup** → Installare modelli Tesseract
6. **Configurare venv per Windows** → Cross-platform compatibility
7. **Creare build.py skeleton** → Setup PyInstaller base
8. **Scrivere test basici** → Test extraction + translation

### Priorità P2 - IMPORTANTE (1 settimana)
9. **Supporto immagini** → JPG/PNG input
10. **Export TXT** → Feature richiesta, facile
11. **Gestione config.json** → Persistenza settings
12. **Profiling memoria** → Verifica <500MB

---

## 📝 NOTE CONTRATTUALI

### Punti da negoziare PRIMA di iniziare:
1. **Qt vs Tkinter** → Decidere M3 scope
2. **Installer <500MB impossibile** → Negoziare <800MB
3. **Argos 1000 parole in 15s impossibile** → Realistico 30-45s
4. **OCR 95% accuratezza non garantibile** → Dipende da input
5. **Assistenza 24 mesi** → Ridurre a 12 o royalty minima

### Timeline realistica:
- M1 (Build Base): 3 settimane (non 2)
- M2 (Bug Fix): 3 settimane (non 2-3)
- M3 (GUI): 4 settimane Tkinter / 6-8 settimane Qt

**TOTALE REALISTICO: 10-14 settimane (non 8-12)**

---

## 🛠️ TOOLS E DIPENDENZE NECESSARIE

### Development
- [ ] Windows VM (VirtualBox/VMware) per testing
- [ ] PyInstaller (packaging)
- [ ] Inno Setup (installer wizard Windows)
- [ ] pytest (testing)
- [ ] memory_profiler (profiling)
- [ ] black/pylint (code quality)

### Librerie Python aggiuntive
- [ ] python-docx (export DOCX)
- [ ] tkinterdnd2 (drag-drop) - se Tkinter
- [ ] PySide6/PyQt6 (GUI) - se Qt
- [ ] watchdog (file monitoring)
- [ ] tqdm (progress bars terminal)

### Assets
- [ ] Icon .ico per Windows
- [ ] Splash screen immagine
- [ ] Logo LAC TRANSLATE

---

## 📊 METRICHE DI SUCCESSO

### Performance Targets
- ✅ Avvio <5s su hardware standard
- ✅ Load PDF 10MB <3s
- ⚠️ OCR pagina A4 300dpi <10s (dipende da HW)
- ❌ Traduzione 1000 parole <15s (IMPOSSIBILE con Argos! Realistico: 30-45s)
- ✅ RAM usage <500MB normale, <1GB PDF grandi

### Quality Targets
- ✅ 0 crash su 10 PDF benchmark
- ✅ Messaggi errore chiari al 100%
- ⚠️ OCR >90% accuratezza (non 95%, dipende da input)
- ✅ 100% funzionalità offline (rimuovi Google!)
- ✅ Test coverage >70%

---

## 🎯 PROSSIMI PASSI IMMEDIATI

### ✅ Completati (4 Dicembre 2025)
1. ✅ Aggiunto Nederlands (7 lingue complete)
2. ✅ Setup OCR multi-lingua (auto-detection)
3. ✅ Installati modelli Tesseract 7 lingue
4. ✅ Aggiornato README
5. ✅ Commit e documentazione

### Settimana 1 (5-10 Dicembre) - IN CORSO
1. **Rimuovere Google Translate** (PRIORITÀ MASSIMA)
2. Creare test basici
3. Benchmark performance Argos
4. Profiling memoria
5. Fix logging robusto

### Settimana 2 (11-17 Dicembre)
6. Supporto file immagine
7. Export TXT
8. Gestione config.json
9. Profiling memoria
10. Setup PyInstaller base

### Settimana 3 (18-24 Dicembre)
11. Build installer Windows
12. Testing su VM Windows 10/11
13. Documentazione tecnica
14. Fix bug rilevati
15. **CONSEGNA M1**

---

**Creato da:** GitHub Copilot + Analisi Codebase Completa  
**Ultima modifica:** 4 Dicembre 2025 - 15:05  
**Stato:** IN PROGRESS - M1 avviata

**✅ Progress Milestone 1:**
- [x] OCR multi-lingua (4/12/2025)
- [x] Nederlands aggiunto (4/12/2025)
- [ ] Rimuovere Google Translate
- [ ] Supporto file immagine
- [ ] Windows Installer
- [ ] Documentazione base
