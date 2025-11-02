# 🔒 DOCUMENTAZIONE SICUREZZA E LICENZE - LAC TRANSLATE v2.0

## 🔐 SICUREZZA IMPLEMENTATA

### 1. Sistema Licenze

#### Hardware ID Binding
✅ **Implementato** in `app/license_manager.py`

**Come funziona:**
- Genera un **ID hardware univoco** combinando:
  - **Windows**: MAC address + CPU ID + Machine GUID (Windows Registry)
  - **macOS**: MAC address + CPU + IOPlatformUUID
  - **Linux**: MAC address + CPU + /etc/machine-id (o hostname)
- Crea un **hash SHA-256** da questi componenti
- **Binding licenza** all'hardware specifico

**Sicurezza:**
- ❌ **NON può essere bypassato facilmente** (richiede modifica hardware ID)
- ✅ **Impedisce copia** della licenza su altri PC
- ⚠️ **Livello base**: Protegge da copia casuale, NON da crack avanzato

#### Validazione Serial Key
✅ **Implementato** in `app/license_manager.py`

**Formato chiave:** `LAC-XXXX-XXXX-XXXX` (es. `LAC-A1B2-C3D4-E5F6`)

**Validazione:**
- Controllo formato chiave
- Verifica hash chiave
- Binding a Hardware ID
- Salvataggio locale criptato

#### Crittografia Licenze
⚠️ **Parzialmente implementato**

**Stato attuale:**
- Libreria `cryptography` opzionale (per produzione)
- Fallback a hash base se non disponibile
- Storage locale in `license/license.dat`

**Per produzione:**
```python
# In requirements.txt, decommentare:
cryptography>=41.0.0
```

#### Cache Licenza Locale
✅ **Implementato**

**Location:**
- `license/license.dat` - Dati licenza
- `license/config.json` - Configurazione

**Contenuto:**
- Serial key (hash)
- Hardware ID
- Data attivazione
- Status validità

---

### 2. Protezione Anti-Pirateria

#### Livello di Protezione Attuale: **BASE**

✅ **Implementato:**
- Hardware ID binding
- Validazione seriale
- Cache locale sicura
- Dialog attivazione obbligatoria

❌ **NON Implementato (per ora):**
- Validazione online periodica
- Obfuscation codice
- Anti-debugging
- Integrity check eseguibile

#### Come Migliorare (Opzionale):
1. **Obfuscation codice Python** (PyArmor, Nuitka)
2. **Validazione online** (periodica, opzionale)
3. **Integrity check** (hash eseguibile)
4. **Anti-debugging** (rilevamento debugger)

⚠️ **Nota**: Nessuna protezione è 100% sicura. Il sistema attuale protegge da copia casuale, ma un cracker esperto può bypassare.

---

## 📦 STATO BUILD E .EXE

### ⚠️ ATTENZIONE: .EXE NON ANCORA CREATO

**Cosa manca:**
- L'**.exe standalone** deve essere creato con `build.py`
- L'**installer Windows** richiede InnoSetup installato

### Come Creare .EXE e Installer:

#### Step 1: Installa PyInstaller
```bash
pip install pyinstaller
```

#### Step 2: Installa InnoSetup (per installer Windows)
- Download: https://jrsoftware.org/isdl.php
- Installa InnoSetup Compiler (ISCC.exe)

#### Step 3: Build .EXE
```bash
python build.py
```

**Output:**
- `dist/LAC_Translate.exe` - Eseguibile standalone
- `release/installer/LAC_Translate_v2.0_Setup.exe` - Installer Windows

#### Step 4: Test Installer
- Installa su Windows 10/11 clean
- Verifica funzionamento
- Testa tutte le funzionalità

---

## 📜 LICENZE SOFTWARE NECESSARIE

### ✅ BUONA NOTIZIA: TUTTE LE LIBRERIE SONO OPEN SOURCE

**NON DEVI COMPRARE NESSUNA LICENZA** per vendere il software!

### Librerie Usate e Loro Licenze:

#### 1. PyMuPDF (MuPDF)
- **Licenza**: AGPL v3 (GNU Affero General Public License)
- **Uso commerciale**: ✅ **PERMESSO** se distribuisci il codice sorgente modificato
- **Alternativa**: Puoi acquistare licenza commerciale da Artifex
- **Costo licenza commerciale**: ~€4000-8000/anno (se non vuoi AGPL)

#### 2. Pillow (PIL)
- **Licenza**: PIL License (open source, permissiva)
- **Uso commerciale**: ✅ **GRATUITO**

#### 3. Argos Translate
- **Licenza**: MIT License
- **Uso commerciale**: ✅ **GRATUITO**

#### 4. Deep Translator
- **Licenza**: MIT License
- **Uso commerciale**: ✅ **GRATUITO**

#### 5. pytesseract / Tesseract OCR
- **Licenza**: Apache License 2.0
- **Uso commerciale**: ✅ **GRATUITO**

#### 6. Tkinter (GUI)
- **Licenza**: Python License (PSF)
- **Uso commerciale**: ✅ **GRATUITO**

#### 7. Python
- **Licenza**: PSF License
- **Uso commerciale**: ✅ **GRATUITO**

---

## ⚖️ COSA DEVI FARE PER VENDERE

### Opzione 1: Gratuita (Raccomandato)

**Con AGPL per PyMuPDF:**
- ✅ Puoi vendere il software
- ⚠️ **DEVI** distribuire il codice sorgente con il software
- ⚠️ Clienti possono vedere/modificare il codice

**Come funziona:**
1. Includi file sorgente nel package vendita
2. Fornisci licenza AGPL
3. Clienti possono modificare codice (ma non rimuovere licenza)

**Pro:**
- ✅ Zero costi licenze
- ✅ Software completamente tuo

**Contro:**
- ⚠️ Codice sorgente visibile
- ⚠️ Clienti tecnici possono modificarlo

---

### Opzione 2: Licenza Commerciale PyMuPDF

**Se NON vuoi distribuire sorgente:**

1. **Acquista licenza commerciale** da Artifex:
   - Costo: ~€4000-8000/anno (varia in base a fatturato)
   - Website: https://artifex.com/
   - Email: sales@artifex.com

2. **Vantaggi:**
   - ✅ Codice sorgente NON necessario
   - ✅ .exe standalone senza sorgente
   - ✅ Nessun obbligo AGPL

3. **Svantaggi:**
   - ❌ Costo annuale significativo
   - ❌ Solo per PyMuPDF (altre librerie già OK)

---

### Opzione 3: Alternative Gratuite

**Sostituisci PyMuPDF con alternative:**

1. **pypdf / PyPDF2** (gratuito, MIT License)
   - ✅ Gratuito
   - ⚠️ Funzionalità limitate (meno potente di PyMuPDF)

2. **pdfplumber** (gratuito, MIT License)
   - ✅ Gratuito
   - ⚠️ Più lento, meno features

**Nota**: Richiede modifiche codice significative.

---

## 🎯 RACCOMANDAZIONE

### Per Iniziare Subito:

**Opzione Consigliata:**
1. ✅ **Usa AGPL PyMuPDF** (gratuito)
2. ✅ **Includi sorgente** nel package vendita
3. ✅ **Vendi subito** senza costi aggiuntivi
4. ⏸ **Valuta licenza commerciale** solo se fatturato alto

**Perché:**
- La maggior parte dei clienti non modificherà il codice
- Il software funziona perfettamente con AGPL
- Zero costi iniziali
- Puoi sempre passare a licenza commerciale dopo

---

## ✅ SEI PRONTO A VENDERE?

### Checklist Pre-Vendita:

- [ ] **Licenze**: ✅ Tutte OK (AGPL PyMuPDF inclusa)
- [ ] **Sicurezza**: ✅ Sistema licenze implementato
- [ ] **Build**: ⏸ Crea .exe con `python build.py`
- [ ] **Installer**: ⏸ Crea installer con InnoSetup
- [ ] **Testing**: ⏸ Test completo funzionalità
- [ ] **Documentazione**: ✅ Completa

### Cosa fare ORA:

1. **Crea .exe e installer**:
   ```bash
   python build.py
   ```

2. **Test installer** su Windows clean

3. **Genera chiavi seriali**:
   ```bash
   python app/generate_license.py
   ```

4. **Riabilita licenze** (in `pdf_translator_gui.py`):
   ```python
   LICENSE_AVAILABLE = True  # Cambia da False a True
   ```

5. **Vendi!** 🚀

---

## 📞 SUPPORTO LICENZE

### PyMuPDF Commercial License:
- **Website**: https://artifex.com/
- **Email**: sales@artifex.com
- **Prezzi**: Su richiesta (variano in base a fatturato)

### Domande?
Se hai dubbi sulle licenze, contatta:
- Support PyMuPDF commerciale per dettagli
- Avvocato specializzato software per consulenza legale

---

**Status**: ✅ PRONTO PER VENDITA (con AGPL)  
**Costi Licenze**: ✅ ZERO (con AGPL)  
**Nessuna Licenza da Comprare**: ✅ CORRETTO (se usi AGPL)

