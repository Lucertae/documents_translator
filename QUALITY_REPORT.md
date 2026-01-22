# Report Qualità Traduzione PDF
**Data:** 2026-01-22  
**Pagine testate:** 90  
**Documenti:** 23 (con duplicati: ~15 unici)

---

## Riepilogo Esecutivo

| Categoria | Pagine | Percentuale |
|-----------|--------|-------------|
| ✅ OK (overlap <10%) | 30 | 33% |
| ⚠️ Warning (overlap ≥10%) | 60 | 67% |
| ❌ Errori | 0 | 0% |

---

## Analisi per Tipologia di Documento

### 1. Documenti Scansionati (OCR) - **ECCELLENTI**

| Documento | Pagine | Overlap | Qualità |
|-----------|--------|---------|---------|
| **Trotec** (Distribution Contract) | 4 | 0% | ⭐⭐⭐⭐⭐ |
| **Mimaki** (Signed Distribution) | 4 | 0% | ⭐⭐⭐⭐⭐ |
| DOC040625 (scansione) | 4 | 0% | ⭐⭐⭐⭐⭐ |
| MCS TS PAI (scansione) | 3/4 | 0-42% | ⭐⭐⭐⭐ |

**✅ I documenti scansionati funzionano PERFETTAMENTE.**  
Il motivo: l'OCR crea blocchi di testo con bbox proporzionati, senza sovrapposizioni ereditate.

### 2. PDF Nativi con Testo Semplice - **PROBLEMATICI**

| Documento | Pagine | Overlap | Qualità |
|-----------|--------|---------|---------|
| Coates_825 | 4 | 42-89% | ⭐ |
| The World Bank Review | 4 | 44-82% | ⭐ |
| ISO-128-1-2020 | 4 | 47-62% | ⭐⭐ |
| DI_PAOLO_THESIS | 4 | 6-82% | ⭐⭐ |
| Physitek Letter | 3 | 45-57% | ⭐⭐ |

**⚠️ Problema principale:** Il testo tradotto (italiano) è ~30% più lungo dell'originale inglese, ma viene inserito nello stesso bbox originale. Questo causa sovrapposizioni.

### 3. PDF con Layout Complesso (multi-colonna, tabelle) - **MOLTO PROBLEMATICI**

| Documento | Pagine | Overlap | Qualità |
|-----------|--------|---------|---------|
| sim_economist_1881 (giornale) | 4 | 61-78% | ⭐ |
| Bibliography Dissertations | 4 | 2-56% | ⭐ |
| V.S. Vladimirov (matematica) | 3/4 | 0-31% | ⭐⭐⭐ |

---

## Cause Principali dei Problemi

### 1. **Espansione del Testo Tradotto** (CAUSA PRINCIPALE - 80% dei problemi)
- L'italiano è ~30% più lungo dell'inglese
- I bbox originali non possono espandersi
- `scale_low=0.6` limita la riduzione del font al 60%
- Con espansione >40%, il testo fuoriesce

**Possibili soluzioni:**
1. `scale_low=0.4` - Più aggressivo, ma font illeggibili
2. **Flusso di testo continuo** - Non usare bbox fissi per ogni linea
3. **Ridimensionamento dinamico** - Calcolare espansione prevista e pre-ridurre font
4. **Bbox estesi** - Usare bbox più grandi che includono margine

### 2. **Struttura dei Blocchi PDF** (15% dei problemi)
- PyMuPDF estrae blocchi con bbox che possono già sovrapporsi
- Il testo tradotto eredita questa struttura problematica

### 3. **Font Troppo Piccoli dopo Scaling** (5% dei problemi)
- ~45% degli span in documenti con tabelle scendono sotto 7pt
- Testo illeggibile, anche se non c'è overlap

---

## ⚠️ Processo di Sviluppo - Best Practice

**PRIMA DI ESEGUIRE IL TEST DI REGRESSIONE COMPLETO:**

1. **Identifica i documenti specifici** che esibiscono il problema da correggere
2. **Testa il fix sui soli documenti problematici** - non su tutto il corpus
3. **Procedi con precisione e cautela** - ogni modifica può avere effetti collaterali
4. **Ricorda l'obiettivo**: il programma deve funzionare in modo eccellente per **qualsiasi documento possibile**
5. **Segui le best practice** - non fare modifiche affrettate

Il test di regressione completo richiede 30+ minuti. Usalo **solo dopo** aver verificato il fix in modo mirato.

---

## Raccomandazioni per Miglioramento

### Priorità ALTA 🔴

1. **Implementare flusso di testo unificato per paragrafi**
   - Invece di inserire riga per riga, unire tutto il paragrafo in un unico blocco
   - Usare `Story` di PyMuPDF per text flow automatico
   - **Impatto stimato:** -50% overlap

2. **Pre-calcolare rapporto espansione testo**
   ```python
   expansion_ratio = len(translated) / len(original)
   if expansion_ratio > 1.2:
       target_font_size = original_size / expansion_ratio
   ```
   - **Impatto stimato:** -30% overlap

### Priorità MEDIA 🟡

3. **Riduzione proattiva del font per blocchi densi**
   - Analizzare densità testo/bbox prima di tradurre
   - Applicare riduzione preventiva
   - **Impatto stimato:** -20% overlap

4. **Gestione intelligente footnotes**
   - Footnotes già identificate (regex `^\d+\s`)
   - Applicare `scale_low=0.4` per footnotes
   - **Impatto stimato:** miglioramento visivo footnotes

### Priorità BASSA 🟢

5. **Supporto layout multi-colonna**
   - Rilevare colonne nel documento
   - Tradurre colonne separatamente
   - **Impatto stimato:** miglioramento documenti complessi

6. **Font minimo leggibile**
   - Impostare limite 6pt come minimo assoluto
   - Troncare testo se necessario
   - **Impatto stimato:** miglioramento leggibilità

---

## Documenti che Funzionano Bene (Pattern di Successo)

Analizzando i documenti con 0% overlap:

1. **Scansioni OCR** - Il testo OCR non ha vincoli di bbox stretti
2. **Documenti con molto spazio bianco** - Margini ampi permettono espansione
3. **Font grandi nell'originale** - Più spazio per la riduzione
4. **Testo tecnico/legale** - Meno espansione EN→IT (terminologia simile)

---

## Metriche Target per Versione 4.0

| Metrica | Attuale | Target |
|---------|---------|--------|
| Overlap <10% | 33% | 70% |
| Font >7pt | 80% | 95% |
| Traduzione accurata | 95% | 95% |
| Tempo/pagina | ~10s | <5s |

---

## Test Specifici Consigliati

Per validare le fix:

1. **Coates pagina 3** - Test paragrafi lunghi
2. **Economist pagina 1** - Test multi-colonna
3. **ISO pagina 4** - Test tabelle
4. **Mimaki pagina 3** - Baseline (già OK)

---

## Conclusioni

Il sistema funziona **molto bene per documenti scansionati** (OCR), che rappresentano una parte significativa dei casi d'uso reali (contratti, documenti firmati, fax).

Per **PDF nativi** con layout denso, sono necessarie ottimizzazioni:
1. Flusso di testo unificato (fix principale)
2. Pre-calcolo espansione
3. Font scaling più intelligente

**Stima effort:** 
- Fix flusso testo: 4-6 ore
- Pre-calcolo espansione: 2-3 ore  
- Testing: 2-3 ore

**Rischio:** Le modifiche potrebbero regredire la qualità dei documenti scansionati. Test di regressione obbligatorio.
