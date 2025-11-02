# ✅ CHECKLIST TESTING LAC TRANSLATE v2.0

**Data Testing**: Gennaio 2024  
**Versione**: 2.0 (Testing Mode - Licenze Disabilitate)

---

## 🧪 TEST RAPIDI (10 minuti)

### ✅ Test 1: Avvio Applicazione
- [ ] L'applicazione si avvia senza errori
- [ ] Interfaccia grafica si carica correttamente
- [ ] Nessun dialog di licenza appare
- [ ] Menu bar visibile e funzionante

**Risultato**: ___________________

### ✅ Test 2: Apertura PDF
- [ ] File → Apri PDF... funziona (Ctrl+O)
- [ ] PDF normale si apre correttamente
- [ ] Pagine visibili nella vista laterale
- [ ] Navigazione pagine funziona (◀ Prec / Succ ▶)

**Risultato**: ___________________

### ✅ Test 3: Traduzione Base
- [ ] Seleziona lingue (da → a)
- [ ] Traduci Pagina (F5) funziona
- [ ] Traduzione appare nella vista destra
- [ ] Traduzione Tutto (F6) funziona per PDF multi-pagina

**Risultato**: ___________________

### ✅ Test 4: Salvataggio
- [ ] File → Salva PDF... funziona (Ctrl+S)
- [ ] PDF tradotto viene salvato correttamente
- [ ] PDF salvato è apribile e leggibile

**Risultato**: ___________________

---

## 🔧 TEST FUNZIONALITÀ (20 minuti)

### ✅ Test 5: Impostazioni
- [ ] Modifica → Impostazioni... apre dialog
- [ ] Cambio traduttore (Google ↔ Argos) funziona
- [ ] Cambio lingue viene salvato
- [ ] Settings persistono dopo chiusura/riapertura

**Risultato**: ___________________

### ✅ Test 6: Zoom
- [ ] Zoom In (🔍+) aumenta zoom
- [ ] Zoom Out (🔍-) diminuisce zoom
- [ ] "Adatta" ridimensiona correttamente
- [ ] Zoom viene salvato nelle settings

**Risultato**: ___________________

### ✅ Test 7: Menu e Shortcuts
- [ ] Ctrl+O: Apri file ✓
- [ ] Ctrl+S: Salva PDF ✓
- [ ] F5: Traduci pagina ✓
- [ ] F6: Traduci tutto ✓
- [ ] Ctrl++: Zoom in ✓
- [ ] Ctrl+-: Zoom out ✓
- [ ] Ctrl+0: Zoom adatta ✓

**Risultato**: ___________________

### ✅ Test 8: Recent Files
- [ ] File → File Recenti mostra PDF aperti
- [ ] Clic su file recente lo apre correttamente
- [ ] "Pulisci Lista" funziona

**Risultato**: ___________________

### ✅ Test 9: About e Info
- [ ] Aiuto → Informazioni mostra versione
- [ ] Dialog About funziona correttamente

**Risultato**: ___________________

---

## 📄 TEST PDF REALI (30 minuti)

### ✅ Test 10: PDF Normale (con testo)
- [ ] PDF con testo nativo si apre
- [ ] Testo viene estratto correttamente
- [ ] Traduzione funziona
- [ ] Layout preservato

**File Testato**: ___________________
**Risultato**: ___________________

### ✅ Test 11: PDF Scansionato (solo immagini)
- [ ] PDF scansionato viene rilevato
- [ ] OCR funziona (se Tesseract installato)
- [ ] Traduzione OCR funziona

**File Testato**: ___________________
**Risultato**: ___________________

### ✅ Test 12: PDF Grande (10+ pagine)
- [ ] PDF grande si carica senza errori
- [ ] Navigazione funziona
- [ ] Traduzione Tutto funziona senza crash
- [ ] Salvataggio funziona

**File Testato**: ___________________
**Risultato**: ___________________

### ✅ Test 13: PDF Multi-lingua
- [ ] PDF in inglese → traduzione italiana
- [ ] PDF in spagnolo → traduzione italiana
- [ ] Qualità traduzione verificata

**File Testato**: ___________________
**Risultato**: ___________________

---

## 🌐 TEST TRADUTTORI (15 minuti)

### ✅ Test 14: Google Translate
- [ ] Google Translate selezionato funziona
- [ ] Traduzione online completa
- [ ] Gestione errori connessione (se offline)

**Risultato**: ___________________

### ✅ Test 15: Argos Translate
- [ ] Argos Translate selezionato funziona
- [ ] Traduzione offline completa
- [ ] Modelli Argos installati correttamente

**Risultato**: ___________________

---

## ⚠️ TEST ERRORI E EDGE CASES (20 minuti)

### ✅ Test 16: Gestione Errori
- [ ] Apertura file non PDF → messaggio errore chiaro
- [ ] PDF corrotto → messaggio errore chiaro
- [ ] File protetto → messaggio errore chiaro
- [ ] Connessione internet assente (Google) → messaggio chiaro

**Risultato**: ___________________

### ✅ Test 17: Stress Test
- [ ] PDF molto grande (50+ pagine) → no crash
- [ ] Traduzione lunga → progress bar funziona
- [ ] Multiple aperture rapide → no errori

**Risultato**: ___________________

---

## 💾 TEST PERSISTENZA (10 minuti)

### ✅ Test 18: Settings Persistenza
- [ ] Cambia settings → chiudi app
- [ ] Riapri app → settings salvati correttamente
- [ ] Recent files persistono

**Risultato**: ___________________

---

## 📊 RISULTATO FINALE

### Statistiche
- **Test Eseguiti**: ___ / 18
- **Test Passati**: ___ / 18
- **Test Falliti**: ___ / 18
- **Bug Trovati**: ___

### Bug Critici Trovati
1. _________________________________________________
2. _________________________________________________
3. _________________________________________________

### Bug Minori Trovati
1. _________________________________________________
2. _________________________________________________

### Note Finali
_________________________________________________
_________________________________________________
_________________________________________________

---

## ✅ FIRMA TESTING

**Testato da**: ___________________  
**Data**: ___________________  
**Versione Software**: 2.0  
**OS**: Windows ___ / macOS ___ / Linux ___

**Stato Finale**: 
- [ ] ✅ PRONTO PER PRODUZIONE
- [ ] ⚠️ BUG DA FIXARE PRIMA DI RILASCIO
- [ ] ❌ NON PRONTO - RICHIEDE LAVORO

