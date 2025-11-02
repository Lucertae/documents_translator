# CREA_INSTALLER.bat vs CREA_INSTALLER.exe

**Due versioni dello stesso script - scegli quella che preferisci**

---

## 📋 Entrambe le Versioni

### 1. CREA_INSTALLER.bat (Text File)
**File:** `scripts/windows/CREA_INSTALLER.bat`

**Caratteristiche:**
- ✅ Testo leggibile
- ✅ Modificabile facilmente
- ✅ Funziona subito (no compilazione)
- ✅ Standard Windows .bat

**Usa questo se:**
- Preferisci testo modificabile
- Sviluppo attivo (modifichi spesso)
- Vuoi vedere il codice

---

### 2. CREA_INSTALLER.exe (Compilato)
**File:** `scripts/windows/dist/CREA_INSTALLER.exe` (dopo compilazione)

**Caratteristiche:**
- ✅ Aspetto più professionale
- ✅ Codice meno visibile
- ✅ Icona personalizzabile
- ⚠️ Richiede compilazione prima

**Usa questo se:**
- Vuoi aspetto più professionale
- Non modifichi spesso lo script
- Preferisci eseguibile compilato

---

## 🔨 Come Creare CREA_INSTALLER.exe

### Metodo Automatico

Esegui:
```bash
scripts\windows\COMPILA_CREA_INSTALLER.bat
```

Questo:
1. Verifica PyInstaller
2. Compila `crea_installer.py` in `.exe`
3. Crea `dist\CREA_INSTALLER.exe`

### Metodo Manuale

```bash
cd scripts\windows
python -m PyInstaller --clean --onefile crea_installer.spec
```

Output: `dist\CREA_INSTALLER.exe`

---

## ⚙️ Funzionalità Identiche

**Entrambe le versioni fanno esattamente la stessa cosa:**

1. ✅ Verifica Python installato
2. ✅ Verifica/installa PyInstaller
3. ✅ Esegue build eseguibile
4. ✅ Crea installer (se InnoSetup disponibile)
5. ✅ Stesso output: installer finale

**Differenza:** Solo "aspetto" - funzionalità identica!

---

## 🎯 Quale Usare?

### Per Sviluppo
**Usa `.bat`:** Più pratico, modificabile, trasparente

### Per Distribuzione Interna
**Usa `.exe`:** Sembra più professionale se condividi con altri sviluppatori

### Per Utenti Finali
**Nessuno dei due!** Gli utenti usano l'installer finale: `LAC_Translate_v2.0.0_Setup.exe`

---

## 📝 Note Tecniche

**Il .exe è wrapper Python:**
- Script Python (`crea_installer.py`) equivalente al `.bat`
- Compilato con PyInstaller
- Include Python runtime (circa 10-15 MB)
- Funziona su Windows senza Python installato

**Il .bat:**
- Richiede Python nel PATH
- Più leggero (pochi KB)
- Modificabile con text editor

---

## ✅ Raccomandazione

**Mantieni entrambi:**
- `.bat` per sviluppo e modifiche rapide
- `.exe` per distribuzione "professionale" interna

**Entrambi creano lo stesso installer finale per utenti!**

---

**La scelta è tua - funzionalità identica, aspetto diverso.** 🎨

