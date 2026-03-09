# Report di Ricerca: Librerie Candidate per Sostituire Codice Custom

**Data:** Ricerca completata su codebase ~8.700 righe (12 file core)  
**Obiettivo:** Identificare librerie testate che possano sostituire blocchi di codice custom

---

## Indice

1. [Riepilogo Raccomandazioni](#1-riepilogo-raccomandazioni)
2. [Stima Larghezza Testo — Font.text_length()](#2-stima-larghezza-testo)
3. [Rilevamento Heading — pymupdf4llm.IdentifyHeaders](#3-rilevamento-heading)
4. [Inserimento Testo con Formattazione Mista — Story.fit_scale()](#4-inserimento-testo-con-formattazione-mista)
5. [Rilevamento Colonne — Deduplicazione su pymupdf4llm](#5-rilevamento-colonne)
6. [Post-Processing OCR — pyspellchecker / symspellpy](#6-post-processing-ocr)
7. [Librerie Scartate](#7-librerie-scartate)

---

## 1. Riepilogo Raccomandazioni

| # | Intervento | Righe sostituite (stima) | Nuove dipendenze | Rischio | Priorità |
|---|---|---|---|---|---|
| **A** | `Font.text_length()` al posto di `char_width_factor * 0.52` | ~30 righe | Nessuna (PyMuPDF) | **BASSO** | **ALTA** |
| **B** | `IdentifyHeaders` / `TocHeaders` per heading detection | ~100 righe | Nessuna (pymupdf4llm già presente) | **BASSO** | **ALTA** |
| **C** | `Story.fit_scale()` per auto-scaling inserimento testo | ~200 righe | Nessuna (PyMuPDF) | **MEDIO** | **ALTA** |
| **D** | Deduplicare rilevamento colonne (3 implementazioni → 1) | ~300 righe | Nessuna | **BASSO** | **MEDIA** |
| **E** | `pyspellchecker` per post-processing OCR multilingue | ~30 righe regex domain-specific | pyspellchecker (MIT, 50KB) | **MEDIO** | **BASSA** |

---

## 2. Stima Larghezza Testo

### Problema Attuale

In `pdf_processor.py` (L2338-2345 e L2981-2984), la larghezza del testo tradotto viene stimata con una costante fissa:

```python
# Codice attuale — APPROSSIMAZIONE GROSSOLANA
char_width_factor = 0.52   # sans-serif
# oppure 0.5 (serif) o 0.6 (monospace)
avg_char_width = target_font_size * char_width_factor
estimated_width = len(plain_text) * avg_char_width
```

Questa stima è **intrinsecamente sbagliata** perché:
- Ogni carattere ha larghezza diversa ("i" vs "W" vs "m")
- Il fattore 0.52 è una media arbitraria per Helvetica
- L'italiano ha lettere accentate (`à`, `è`, `ù`) con larghezze differenti
- Causa sotto/sovrastima sistematica per testi corti e lunghi

### Soluzione: `pymupdf.Font.text_length()`

PyMuPDF ha già un metodo **nativo in C** che calcola la larghezza esatta:

```python
font = pymupdf.Font("helv")  # o qualsiasi altro font
exact_width = font.text_length("Testo tradotto in italiano", fontsize=12)

# Per larghezza per-carattere (utile per wrapping intelligente):
char_widths = font.char_lengths("Testo tradotto", fontsize=12)
# → (7.33, 4.66, 5.66, 4.00, 6.66, ...)  # larghezza in punti per ogni char
```

**Performance:** 12.5ns per carattere dopo il primo (implementato in C). Per una stringa di 100 caratteri: ~1.2μs vs. una semplice moltiplicazione.

### Cosa Verrebbe Sostituito

| File | Righe | Codice |
|---|---|---|
| `pdf_processor.py` L2338-2345 | 8 righe | `char_width_factor` logic in `_insert_formatted_translation()` |
| `pdf_processor.py` L2981-2984 | 4 righe | `char_width_factor` logic in `_insert_line_translation()` |
| `pdf_processor.py` L3106 | 1 riga | `max_chars = int(bbox_width / (target_font_size * 0.45))` — fallback troncamento |

### Rischio

**BASSO.** `Font.text_length()` è stabile da PyMuPDF v1.18.14. Non aggiunge dipendenze. L'unica attenzione è che il font usato per la misurazione deve corrispondere a quello usato per l'inserimento (già garantito nel codice attuale).

### Note Implementative

- Creare l'oggetto `Font` una volta e riutilizzarlo (è molto leggero)
- Il nome font va mappato: `"helv"` → `Font("helv")`, `"tiro"` → `Font("tiro")`, `"cour"` → `Font("cour")`
- Si può mantenere il `char_width_factor` come **fallback** se la creazione del Font fallisce

---

## 3. Rilevamento Heading

### Problema Attuale

**Bug segnalato dall'utente:** "Il titolo viene troncato solo perché va a capo" (tesi di Paolo).

Il rilevamento heading è fatto da `_group_lines_into_paragraphs()` (L2445-2568, ~120 righe) con 5 euristiche:

```python
# Check 2: Font size change > ±20%
# Check 3: Bold status change
# Check 4: Short line + title case → title_pattern
```

**Problemi identificati:**
1. La funzione `detect_title_or_heading()` in `format_utils.py` (L282-322) è **definita ma MAI chiamata** nel codebase
2. Il "Check 4" (title pattern) controlla solo `len < 50 && words ≤ 6 && istitle()` — un titolo che occupa 2 righe viene spezzato perché la seconda riga non ha le stesse caratteristiche
3. Non c'è alcun confronto con il font prevalente del documento — un titolo a 14pt vs body a 12pt potrebbe non superare la soglia del ±20%

### Soluzione: `pymupdf4llm.IdentifyHeaders`

Classe **già presente** nel progetto (pymupdf4llm è già installato per `column_boxes()`).

**Algoritmo interno verificato dal source code:**
1. Scansiona TUTTO il documento e conta i caratteri per ogni dimensione font (arrotondata)
2. La dimensione con il **maggior numero totale di caratteri** = body text
3. Tutte le dimensioni **più grandi** del body = heading levels (h1 → h6, dal più grande al più piccolo)
4. `get_header_id(span)` restituisce `"# "`, `"## "`, ecc.

```python
import pymupdf4llm

# Una volta per documento:
hdr_detector = pymupdf4llm.IdentifyHeaders(doc, max_levels=4)

# Per ogni span estratto:
hdr_prefix = hdr_detector.get_header_id(span)  # "" = body, "# " = h1, ecc.
is_heading = bool(hdr_prefix)
heading_level = len(hdr_prefix.strip())  # 0, 1, 2, 3, ...
```

**Alternativa per PDF con indice:** `pymupdf4llm.TocHeaders(doc)` — usa il Table of Contents del PDF senza scansionare le pagine. Più veloce e più accurato per documenti ben strutturati.

### Cosa Verrebbe Sostituito

| File | Righe | Codice |
|---|---|---|
| `pdf_processor.py` L2519-2536 | 18 righe | Check 2 (size_change) + Check 3 (bold_change) + Check 4 (title_pattern) |
| `format_utils.py` L282-322 | 40 righe | `detect_title_or_heading()` — funzione morta, **da eliminare** |

**NB:** Non sostituirebbe completamente `_group_lines_into_paragraphs()` perché quella funzione gestisce anche gap verticali e punteggiatura. Ma il rilevamento heading sarebbe delegato a `IdentifyHeaders` che è più robusto (basa tutto sul confronto globale delle dimensioni font).

### Come Risolve il Bug del Titolo Troncato

Con `IdentifyHeaders`:
- Il titolo "Analisi delle politiche economiche\nin Italia nel periodo 2020-2024" (14pt, 2 righe)
- Entrambe le righe hanno font size 14pt → entrambe classificate come heading
- La logica di paragraphing può raggruppare righe consecutive con lo **stesso heading level** anziché spezzarle

Attualmente il Check 4 spezza la seconda riga perché `"in Italia nel periodo 2020-2024"` non è `istitle()`.

### Rischio

**BASSO.** `IdentifyHeaders` è la stessa logica usata internamente da `to_markdown()` quando `hdr_info=None`. Testata su migliaia di documenti. Nessuna nuova dipendenza.

---

## 4. Inserimento Testo con Formattazione Mista

### Problema Attuale

**Bug segnalato dall'utente:** "gestione delle dimensioni del testo tradotto generato" — testo che non entra nel bounding box, o che viene rimpicciolito troppo.

`_insert_formatted_translation()` (L2280-2443, ~186 righe) e `_insert_line_translation()` (L2908-3114, ~206 righe) contengono logica custom per:

1. **Stima larghezza testo** (hardcoded 0.52 — vedi sezione 2)
2. **Decisione wrapping vs no-wrapping** (basata sulla stima sbagliata)
3. **Espansione bbox** (`min(required * 1.15, bbox_height * 1.8)` — cap arbitrario)
4. **Scelta scale_low** (0.6 normal, 0.5 footnote — hardcoded)
5. **Costruzione HTML+CSS** (inline string building)

Il tutto si basa su `page.insert_htmlbox()` che internamente già usa la Story, ma il codice custom prima della chiamata fa calcoli di sizing basati su stime errate.

### Soluzione: `insert_htmlbox` con `Font.text_length()` + Logica Semplificata

Il metodo `insert_htmlbox` **già gestisce auto-scaling** via `scale_low`. Il problema è che il codice attuale cerca di pre-calcolare il sizing con stime sbagliate e poi modifica il bbox prima di passarlo a `insert_htmlbox`.

**Approccio proposto:**
1. **Rimuovere** tutta la pre-stima width/height (righe 2338-2372)
2. Calcolare la larghezza reale con `Font.text_length()` solo per decidere se servono **wrapping o multi-riga** a livello CSS
3. Passare il bbox **originale** a `insert_htmlbox` con `scale_low` appropriato
4. Lasciare che `insert_htmlbox` gestisca il fitting internamente (è implementato in C, con binary search)

```python
# PRIMA (codice attuale — ~30 righe di calcoli):
avg_char_width = target_font_size * char_width_factor
estimated_width = len(plain_text) * avg_char_width
needs_wrapping = estimated_width > bbox_width * 1.5
if needs_wrapping:
    estimated_lines = max(1, estimated_width / bbox_width)
    line_height = target_font_size * 1.2
    required_height = estimated_lines * line_height
    expanded_height = min(required_height * 1.15, bbox_height * 1.8)
    # ... expand bbox ...

# DOPO (proposto — ~5 righe):
font = pymupdf.Font("helv")
real_width = font.text_length(plain_text, fontsize=target_font_size)
needs_wrapping = real_width > bbox_width
# Lasciare insert_htmlbox gestire il fitting via scale_low
result = page.insert_htmlbox(merged_bbox, formatted_html, css=css, 
                             rotate=rotation, scale_low=0.5)
```

### Alternativa più Radicale: `Story.fit_scale()`

Per un controllo totale, si potrebbe usare `Story.fit_scale()` che fa binary search C-nativo:

```python
story = pymupdf.Story(html=formatted_html, user_css=css)
result = story.fit_scale(rect, scale_min=0.5, scale_max=1.5)
if result.big_enough:
    # Write to a temp page, then overlay
    writer = pymupdf.DocumentWriter(pymupdf.open())  # memory doc
    dev = writer.begin_page(page.rect)
    story.draw(dev)
    writer.end_page()
    # ... overlay ...
```

**Tuttavia**, `Story` non può scrivere direttamente su pagine esistenti. Richiede il workaround DocumentWriter → show_pdf_page. Questo aggiunge complessità. **Raccomando l'approccio insert_htmlbox + Font.text_length()** come migliore rapporto semplicità/risultato.

### Cosa Verrebbe Sostituito

| File | Righe | Codice |
|---|---|---|
| `pdf_processor.py` L2330-2372 | ~42 righe | Font family selection + char_width estimation + wrapping logic + bbox expansion |
| `pdf_processor.py` L2975-3000 | ~25 righe | Stessa logica duplicata in `_insert_line_translation()` |

### Rischio

**MEDIO.** La logica di sizing è al cuore della qualità visiva. Il test deve essere fatto su diversi tipi di documento (contratti, tesi, articoli). Il fallback attuale (truncate + "...") va mantenuto.

---

## 5. Rilevamento Colonne

### Problema Attuale

Il rilevamento colonne è **implementato 3 volte separate** con algoritmi diversi:

| File | Righe | Algoritmo |
|---|---|---|
| `rapid_ocr.py` L280-390 | 110 righe | Istogramma gap orizzontali tra box, binning a 200 bucket, smoothing |
| `rapid_doc_engine.py` L367-510 | 145 righe | Due strategie: bounding box clustering + spazio bianco verticale |
| `pdf_processor.py` L2679-2896 | 217 righe | X-overlap 30% tra blocchi single-line, merge progressivo |

**Inoltre**, `pymupdf4llm.column_boxes()` è **già usato** nel progetto (vedi pdf_processor.py) ma solo come fallback per certi path.

### Soluzione: Unificare su `pymupdf4llm.column_boxes()`

`column_boxes()` è la funzione che il progetto già importa. Essa:
- Rileva colonne tramite analisi dei blocchi di testo di PyMuPDF
- Gestisce layout single-column e multi-column
- Restituisce liste di Rect (bounding box per colonna)
- È testata dall'ecosistema pymupdf4llm

**Approccio:**
1. Per pagine **non scansionate**: usare `column_boxes()` direttamente (già funziona)
2. Per pagine **scansionate** (dove OCR produce box): creare una pagina temporanea con testo OCR e poi usare `column_boxes()`, oppure mantenere la versione in `rapid_ocr.py` come unica implementazione per OCR
3. **Eliminare** la duplicazione in `rapid_doc_engine.py` e `pdf_processor.py`

### Cosa Verrebbe Sostituito/Eliminato

| File | Righe eliminate |
|---|---|
| `rapid_doc_engine.py` detect_column_count() | ~145 righe |
| `pdf_processor.py` _merge_single_line_blocks() | ~217 righe (parziale — contiene anche logica merge) |

### Rischio

**BASSO** per la rimozione delle duplicazioni. Richiede test attento su documenti multi-colonna reali.

---

## 6. Post-Processing OCR

### Stato Attuale

`ocr_utils.py` (274 righe) contiene:
- **87 regex di correzione** (I/l/1, O/0, S/5, legature, brand names come "Mimaki")
- Molte sono **domain-specific** per contratti legali (Article, Exhibit, Authorized Distribution)
- Pipeline: `clean_ocr_text → fix_line_breaks → remove_page_artifacts → normalize_whitespace`

### Librerie Trovate

| Libreria | Licenza | IT Support | OCR | Peso |
|---|---|---|---|---|
| **pyspellchecker** v0.9.0 | MIT | **Sì nativo** (dizionario italiano built-in) | Buono (edit distance ≤2) | ~50KB + dizionari |
| **symspellpy** v6.9.0 | MIT | Necessita dizionario esterno | **Eccellente** (1M× più veloce) | ~10MB con dizionario EN |
| **language-tool-python** v3.3.0 | **GPL-3.0** | Sì | Eccellente (grammatica+spelling) | **~200MB + Java** |
| **textblob** v0.19.0 | MIT | No | Basso | ~10MB + NLTK corpora |

### Raccomandazione

**pyspellchecker** è la scelta migliore per il vostro caso:
- MIT license (compatibile)
- Supporto italiano **built-in** (`SpellChecker(language='it')`)
- Leggero (~50KB)
- Nessuna dipendenza pesante (no Java, no NLTK)
- API semplice: `correction(word)`, `candidates(word)`, `unknown(words)`

**MA:** le regex domain-specific (Mimaki, Article, Exhibit) **non possono essere sostituite** da un correttore ortografico generico. Sono correzioni intenzionali per nomi di brand e terminologia legale.

### Approccio Ibrido Suggerito

```python
# 1. Mantenere le regex domain-specific (brand names, legal terms)
# 2. Sostituire le correzioni carattere generico (I/l/1, O/0, S/5) con pyspellchecker
# 3. Aggiungere pyspellchecker come passo DOPO le regex

from spellchecker import SpellChecker
spell_it = SpellChecker(language='it')
spell_en = SpellChecker(language='en')

def correct_ocr_word(word, language='it'):
    spell = spell_it if language == 'it' else spell_en
    if word not in spell:
        correction = spell.correction(word)
        if correction and correction != word:
            return correction
    return word
```

### Rischio

**MEDIO.** I correttori ortografici possono produrre false correzioni su nomi propri, sigle e termini tecnici. Deve essere usato con cautela (solo su parole sconosciute, con whitelist per termini tecnici).

---

## 7. Librerie Scartate

### pdfplumber
- **Motivo:** Read-only (non scrive PDF), più lento di PyMuPDF (basato su pdfminer.six), nessun rilevamento heading/paragrafi/colonne. Aggiungerebbe una dipendenza senza valore aggiunto.

### docling (IBM)
- **Motivo:** Troppo pesante per app desktop interattiva (~2GB PyTorch, secondi per pagina). AI-based layout detection eccellente ma overkill. Non scrive PDF.
- **Rivalutare se:** la qualità del layout detection diventa il problema #1 e si può tollerare la latenza.

### textblob
- **Motivo:** Spelling correction solo inglese. More un toolkit NLP generale che un correttore OCR.

### autocorrect
- **Motivo:** Abbandonato (ultimo update dicembre 2021), nessuna documentazione su PyPI.

### language-tool-python
- **Motivo:** Licenza GPL-3.0 (incompatibile con molti use case), richiede Java ≥17 runtime, download ~200MB. Eccellente per grammatica ma troppo pesante.

### Story class (per inserimento testo)
- **Motivo** dello scarto come soluzione primaria: non può scrivere direttamente su pagine esistenti (solo DocumentWriter → new pages). Il workaround (memory PDF + show_pdf_page) aggiunge complessità significativa. `insert_htmlbox` è preferibile dato che è già usato e fa la stessa cosa con API più semplice.

---

## Appendice: Mappa Funzioni Custom → Sostituzione Proposta

| Funzione | File | Righe | Sostituzione |
|---|---|---|---|
| `char_width_factor * font_size` | pdf_processor.py | ~30 | `Font.text_length()` |
| `detect_title_or_heading()` | format_utils.py L282-322 | 40 | **ELIMINARE** (dead code) |
| Check 2/3/4 in `_group_lines_into_paragraphs()` | pdf_processor.py L2510-2536 | 26 | `IdentifyHeaders.get_header_id()` |
| bbox expansion logic | pdf_processor.py L2358-2372 | 14 | Delegare a `insert_htmlbox` scale_low |
| `_detect_columns()` | rapid_ocr.py L280-390 | 110 | Unificare (mantenere solo questa per OCR) |
| `detect_column_count()` | rapid_doc_engine.py L367-510 | 145 | Eliminare, usare `column_boxes()` |
| X-overlap column detection | pdf_processor.py L2679-2896 | 217 | Eliminare, usare `column_boxes()` |
| Regex OCR generiche (I/l/1, O/0) | ocr_utils.py L25-87 | ~60 | pyspellchecker (opzionale, bassa priorità) |

**Totale righe potenzialmente sostituite/eliminate: ~640**

---

## Prossimi Passi Suggeriti

1. **Implementare A (Font.text_length)** — cambiamento minimo, massimo impatto sulla qualità sizing
2. **Implementare B (IdentifyHeaders)** — risolve il bug titolo troncato
3. **Eliminare dead code** — `detect_title_or_heading()` mai chiamata
4. **Implementare C (rimuovere pre-calcolo sizing)** — semplificare `_insert_formatted_translation()`
5. **Deduplicare colonne (D)** — refactoring strutturale
6. **(Opzionale) pyspellchecker (E)** — solo se la qualità OCR è un problema

Ogni intervento va testato **individualmente** con documenti reali prima di passare al successivo.
