# Report Qualità Traduzione PDF
**Data:** 2026-01-30 (Benchmark Reale)  
**Pagine testate:** 52  
**Documenti:** 14  
**Tempo totale test:** 24 min 25s

---

## Riepilogo Esecutivo

| Categoria | Documenti | Percentuale |
|-----------|-----------|-------------|
| OK (overlap <10%) | 6 | **43%** |
| Warning (overlap >=10%) | 8 | 57% |
| Errori | 0 | 0% |

### Metriche Aggregate

| Metrica | Valore |
|---------|--------|
| **Tempo medio/pagina** | 28.17s |
| **Overlap medio** | 27.4% |
| **Font <7pt medio** | 10.5% |

---

## Analisi per Tipologia di Documento

### 1. Documenti Scansionati (OCR) - **ECCELLENTI**

| Documento | Pagine Tot. | Tempo/pag | Overlap | Qualità |
|-----------|-------------|-----------|---------|---------|
| **1.pdf** (scansione) | 1 | 23.47s | **0.0%** | Eccellente |
| **Signed Mimaki Agreement** | 13 | 77.23s | **2.2%** | Eccellente |
| **DOC040625** (scansione) | 40 | 33.80s | **2.4%** | Eccellente |
| **Distribution Contract Trotec** | 21 | 24.80s | **6.4%** | Eccellente |
| MCS TS PAI (scansione) | 18 | 22.22s | 10.2% | Buono |

I documenti scansionati funzionano PERFETTAMENTE (0-6% overlap).  
Il motivo: l'OCR crea blocchi di testo con bbox proporzionati, senza sovrapposizioni ereditate.

### 2. PDF Nativi con Testo Semplice - **DA MIGLIORARE**

| Documento | Pagine Tot. | Tempo/pag | Overlap | Qualità |
|-----------|-------------|-----------|---------|---------|
| V.S. Vladimirov (matematica) | 427 | 13.29s | **3.7%** | Buono |
| Quarterly Journal Economics | 5 | 26.36s | **8.9%** | Buono |
| The World Bank Review | 207 | 25.18s | 38.3% | Sufficiente |
| Coates_825 | 36 | 16.61s | 43.8% | Sufficiente |
| ISO-128-1-2020 | 9 | 12.66s | 50.1% | Sufficiente |
| Physitek Letter | 3 | 18.19s | 51.7% | Sufficiente |
| DI_PAOLO_THESIS | 54 | 11.52s | 61.8% | Scarso |

**Problema principale:** Il testo tradotto (italiano) è ~30% più lungo dell'originale inglese, ma viene inserito nello stesso bbox originale. Questo causa sovrapposizioni.

### 3. PDF con Layout Complesso (multi-colonna, tabelle) - **MOLTO PROBLEMATICI**

| Documento | Pagine Tot. | Tempo/pag | Overlap | Qualità |
|-----------|-------------|-----------|---------|---------|
| Bibliography Dissertations | 472 | 16.71s | 47.0% | Sufficiente |
| sim_economist_1881 (giornale) | 32 | 66.31s | 56.7% | Scarso |

---

## Performance Tempo

| Categoria | Tempo medio/pagina | Range |
|-----------|-------------------|-------|
| **PDF nativi semplici** | 13-26s | Più veloce |
| **Scansioni OCR** | 23-77s | OCR + traduzione |
| **Layout complesso** | 17-66s | Variabile |

