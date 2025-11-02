# 🧪 LAC TRANSLATE - MODALITÀ TESTING

## ⚠️ IMPORTANTE

Il software è attualmente in **MODALITÀ TESTING**.

### Cosa significa:
- ✅ **Sistema licenze DISABILITATO**
- ✅ **Nessun controllo attivazione**
- ✅ **Nessun dialog EULA**
- ✅ **Funziona completamente senza chiavi seriali**

### Dove è disabilitato:
File: `app/pdf_translator_gui.py`  
Riga 24: `LICENSE_AVAILABLE = False`

---

## 🔄 RIABILITARE LICENZE PER PRODUZIONE

Quando sei pronto per distribuire, modifica:

```python
# app/pdf_translator_gui.py (riga 24)
LICENSE_AVAILABLE = False  # ← Cambia in True
```

Poi:
1. Testa che il sistema licenze funzioni
2. Genera chiavi seriali: `python app/generate_license.py`
3. Build per distribuzione: `python build.py`

---

## ✅ TESTING RAPIDO

### Test 1: Avvio Base
```bash
python app/pdf_translator_gui.py
```
**Verifica**:
- L'app si apre senza errori
- Nessun dialog licenza
- Interfaccia funziona

### Test 2: Funzionalità Core
1. **Apri PDF**: File → Apri PDF (Ctrl+O)
2. **Traduci**: Seleziona lingue → Traduci Pagina (F5)
3. **Salva**: File → Salva PDF (Ctrl+S)

### Test 3: Settings
- Modifica → Impostazioni
- Cambia traduttore/lingue
- Verifica persistenza

### Test 4: PDF Real
- Apri PDF reale (non di test)
- Verifica traduzione corretta
- Verifica layout preservato

---

## 📋 CHECKLIST TESTING COMPLETA

Vedi file: `TESTING_CHECKLIST.md`

---

## 🐛 TROVATO UN BUG?

### Segnala:
1. **Cosa** hai fatto (steps)
2. **Cosa** è successo (errore)
3. **Cosa** ti aspettavi
4. **Screenshot** (se possibile)

### Dove:
- Log: `logs/pdf_translator.log`
- Console output
- Error dialog

---

## ✅ TESTING PRIORITÀ

### Must-Test (Prima di distribuire):
1. ✅ Avvio applicazione
2. ✅ Apertura PDF normale
3. ✅ Traduzione pagina
4. ✅ Salvataggio PDF
5. ✅ Settings persistenza

### Should-Test (Raccomandato):
6. ✅ PDF scansionato (OCR)
7. ✅ PDF grandi (10+ pagine)
8. ✅ Traduzione tutto (F6)
9. ✅ Zoom e navigazione
10. ✅ Error handling

### Nice-to-Test (Opzionale):
11. ⏸ Batch processing
12. ⏸ Drag & drop (se tkinterdnd2 installato)
13. ⏸ Stress test (100+ pagine)

---

## 🚀 PROSSIMI PASSI

### Dopo Testing Completo:
1. **Fix bug** trovati
2. **Riabilita licenze** (se tutto OK)
3. **Build finale** per distribuzione
4. **Testing installer** su macchina clean
5. **Distribuzione** ai clienti

---

**Status Attuale**: 🧪 MODALITÀ TESTING  
**Licenze**: ❌ DISABILITATE  
**Pronto per**: ✅ TESTING FUNZIONALITÀ

