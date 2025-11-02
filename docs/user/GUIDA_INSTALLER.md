# Guida Installer Windows - Per Utenti Finali

**Come creare l'installer Windows per distribuire LAC TRANSLATE agli utenti**

---

## 🎯 Obiettivo

Creare un installer Windows (.exe) che gli utenti possono eseguire senza installare Python manualmente. Tutto è incluso nell'installer.

---

## 📋 Requisiti

Per creare l'installer, hai bisogno di:

1. **Python 3.8+** installato
2. **PyInstaller** (si installa automaticamente)
3. **InnoSetup 6** (opzionale ma raccomandato per installer professionale)

---

## 🚀 Metodo Rapido (Script Automatico)

### Windows

Esegui semplicemente:

```bash
scripts\windows\CREA_INSTALLER.bat
```

Lo script fa tutto automaticamente:
1. ✅ Verifica dipendenze
2. ✅ Installa PyInstaller se necessario
3. ✅ Crea eseguibile .exe
4. ✅ Crea installer .exe (se InnoSetup installato)

**Output:**
- Eseguibile: `dist\LAC_Translate.exe`
- Installer: `release\installer\LAC_Translate_v2.0.0_Setup.exe`

---

## 🔧 Metodo Manuale

### Step 1: Installa Dipendenze

```bash
pip install pyinstaller
```

### Step 2: Crea Eseguibile

```bash
python build.py
```

Questo crea:
- `dist/LAC_Translate.exe` - Eseguibile standalone (tutto incluso)

### Step 3: Crea Installer (Opzionale)

Se hai InnoSetup installato:

1. Installa InnoSetup da: https://jrsoftware.org/isdl.php
2. Esegui:
   ```bash
   ISCC.exe installer_setup.iss
   ```

Oppure usa il comando integrato in `build.py`:
```bash
python build.py
```
(Crea installer automaticamente se InnoSetup trovato)

---

## 📦 Cosa Contiene l'Installer

L'installer Windows include:

- ✅ **Eseguibile standalone** - Non serve Python installato
- ✅ **Tutte le librerie** - Tutte le dipendenze incluse
- ✅ **Moduli Python** - Tutto quello che serve
- ✅ **Icona applicazione**
- ✅ **Documentazione** (README, LICENSE)
- ✅ **Shortcut desktop** (opzionale)
- ✅ **Menu Start** (opzionale)

**Dimensione installer:** ~100-150 MB (tutto incluso)

---

## 🎁 Distribuzione

### Per Utenti Finali

Gli utenti devono solo:

1. **Scarica** `LAC_Translate_v2.0.0_Setup.exe`
2. **Esegui** l'installer (doppio click)
3. **Segui** il wizard di installazione
4. **Avvia** il software dal desktop o menu Start
5. **Inserisci** la chiave seriale all'avvio

**Non serve:**
- ❌ Installare Python
- ❌ Installare dipendenze
- ❌ Configurare nulla
- ❌ Sapere programmare

Tutto è incluso nell'installer!

---

## 🔍 Verifica Build

### Verifica Eseguibile

Dopo il build, verifica:

1. **Eseguibile esiste:**
   ```
   dist\LAC_Translate.exe
   ```

2. **Dimensione ragionevole:**
   - Dovrebbe essere ~80-120 MB
   - Se troppo piccolo, potrebbero mancare moduli

3. **Test esecuzione:**
   - Esegui `dist\LAC_Translate.exe`
   - Dovrebbe aprire la GUI senza errori

### Verifica Installer

Dopo creazione installer:

1. **Installer esiste:**
   ```
   release\installer\LAC_Translate_v2.0.0_Setup.exe
   ```

2. **Test installazione:**
   - Installa su un PC di test (diverso da quello di sviluppo)
   - Verifica che funzioni senza Python installato
   - Verifica che la licenza funzioni

---

## ⚠️ Problemi Comuni

### "PyInstaller non trovato"

**Soluzione:**
```bash
pip install pyinstaller
```

### "InnoSetup non trovato"

**Opzioni:**
1. **Installa InnoSetup** (raccomandato):
   - Scarica: https://jrsoftware.org/isdl.php
   - Installa
   - Rilancia script

2. **Usa solo eseguibile:**
   - L'eseguibile `dist\LAC_Translate.exe` funziona comunque
   - Puoi distribuirlo manualmente (senza installer)

### "Eseguibile troppo grande"

**Normale:**
- L'eseguibile include tutto (Python, librerie, moduli)
- ~100-150 MB è normale
- PyInstaller comprime tutto in un unico file

### "Errore durante build"

**Controlla:**
1. Tutti i moduli sono importabili?
2. Tutte le dipendenze sono in `requirements.txt`?
3. Il file `.spec` include tutti i moduli necessari?

---

## 📝 Personalizzazione Installer

### Modifica Versione

Edita `installer_setup.iss`:
```iss
#define MyAppVersion "2.0.0"
```

### Modifica Nome Installer

Edita `installer_setup.iss`:
```iss
OutputBaseFilename=LAC_Translate_v{#MyAppVersion}_Setup
```

### Aggiungi File

Edita sezione `[Files]` in `installer_setup.iss`:
```iss
Source: "path\to\file.txt"; DestDir: "{app}"; Flags: ignoreversion
```

---

## 🎯 Workflow Completo

### Per Sviluppatore

1. **Modifica codice**
2. **Testa localmente:**
   ```bash
   python app/pdf_translator_gui.py
   ```
3. **Crea installer:**
   ```bash
   scripts\windows\CREA_INSTALLER.bat
   ```
4. **Testa installer** su PC pulito
5. **Distribuisci** `release\installer\*.exe`

### Per CI/CD (GitHub Actions)

Il build è automatizzato:
- Push tag `v2.0.0` → Build automatico
- Installer creato automaticamente
- Upload a GitHub Release

---

## ✅ Checklist Pre-Distribuzione

Prima di distribuire l'installer:

- [ ] Eseguibile creato senza errori
- [ ] Installer creato (se usando InnoSetup)
- [ ] Test su PC pulito (senza Python)
- [ ] Licenza funziona correttamente
- [ ] Icona desktop funziona
- [ ] Documentazione inclusa
- [ ] Versione corretta nell'installer
- [ ] Installer testato installazione/uninstall

---

## 📞 Supporto

Se hai problemi:

1. **Verifica log build:** `build.log` (se disponibile)
2. **Verifica dipendenze:** `pip list`
3. **Testa moduli:** `python -c "import [modulo]"`

---

**L'installer è pronto per distribuzione professionale!** 🚀

Gli utenti finali possono installare con un semplice doppio click, senza configurazioni tecniche.

