# 🏗️ Creare Eseguibile Windows per LAC Translate

## 📋 Prerequisiti

1. **Windows 10/11** o **Linux con Wine**
2. **Python 3.10+** installato
3. **Ambiente virtuale** attivo con tutte le dipendenze

---

## 🚀 Metodo 1: PyInstaller (Consigliato)

### Step 1: Installa PyInstaller

```bash
pip install pyinstaller
```

### Step 2: Esegui lo script di build

```bash
python build_windows.py
```

### Step 3: Trova l'eseguibile

L'eseguibile sarà creato in:
```
dist/LacTranslate.exe
```

### Dimensione Finale
- **~500MB-1GB** - Include Python, Qt6, Torch, e dipendenze ML
- **Primo avvio**: Scarica modelli OPUS-MT + PaddleOCR (~1GB addizionale)

---

## 🎯 Metodo 2: Build Manuale con PyInstaller

Se preferisci controllare manualmente:

```bash
pyinstaller --name=LacTranslate \
    --onefile \
    --windowed \
    --noconfirm \
    --clean \
    --hidden-import=PySide6 \
    --hidden-import=transformers \
    --hidden-import=torch \
    --hidden-import=paddleocr \
    --collect-all=transformers \
    --collect-all=torch \
    --collect-all=PySide6 \
    --collect-all=paddleocr \
    --exclude-module=matplotlib \
    --exclude-module=scipy \
    app/main_qt.py
```

---

## 🛠️ Metodo 3: Nuitka (Più veloce, più complesso)

### Vantaggi
- Eseguibile **più veloce** (compilato a C++)
- **Dimensioni ridotte** (~30% meno)
- **Migliore performance**

### Svantaggi
- Setup **più complesso**
- Richiede **compilatore C** (MSVC su Windows)

### Installazione

```bash
pip install nuitka
```

### Build

```bash
python -m nuitka --standalone \
    --onefile \
    --windows-disable-console \
    --enable-plugin=pyside6 \
    --include-package=transformers \
    --include-package=torch \
    --include-package=paddleocr \
    --output-dir=dist \
    app/main_qt.py
```

---

## 📦 Distribuzione

### Opzione A: Solo .exe (Semplice)
1. Copia `dist/LacTranslate.exe` su target PC
2. Al primo avvio scarica automaticamente modelli (~1GB)
3. **Richiede connessione internet** al primo avvio

### Opzione B: .exe + Modelli (Completo, offline)
1. Dopo primo avvio, i modelli sono in:
   - Windows: `C:\Users\<user>\.cache\huggingface\`
   - Linux: `~/.cache/huggingface/`
2. Copia cartella `huggingface/` insieme all'exe
3. Imposta variabile ambiente: `TRANSFORMERS_CACHE=.\huggingface`
4. **Nessuna connessione richiesta**

### Opzione C: Installer con Inno Setup (Professionale)

Crea un installer wizard con:
1. **Inno Setup** (gratuito): https://jrsoftware.org/isinfo.php
2. Include `.exe` + modelli + shortcuts
3. Registro di Windows, uninstaller automatico

---

## 🧪 Testing

### Test su Windows Clean
1. **VM Windows 10/11** senza Python
2. Avvia `LacTranslate.exe`
3. Verifica funzionalità:
   - Apri PDF
   - Traduci pagina
   - Salva PDF tradotto
4. Controlla uso RAM < 1GB

### Test Offline
1. Disconnetti internet
2. Avvia app con modelli pre-scaricati
3. Verifica traduzione funziona

---

## ⚙️ Configurazioni Avanzate

### Ridurre Dimensioni

Nel file `build_windows.py`, aggiungi:
```python
'--exclude-module=matplotlib',
'--exclude-module=scipy',
'--exclude-module=pandas',
'--exclude-module=notebook',
```

### Aggiungere Icona

1. Crea/trova un file `.ico` (icona Windows)
2. Aggiungi in `build_windows.py`:
```python
'--icon=assets/icon.ico',
```

### Firma Digitale (Opzionale)

Per evitare warning "Unknown Publisher":
1. Acquista certificato code signing (~€100-300/anno)
2. Firma con `signtool.exe` (Windows SDK)

```bash
signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com dist/LacTranslate.exe
```

---

## 🐛 Troubleshooting

### ❌ "ModuleNotFoundError"
→ Aggiungi `--hidden-import=<modulo>` in build script

### ❌ ".exe troppo grande" (>2GB)
→ Usa `--exclude-module` per rimuovere librerie non usate

### ❌ "Torch non trovato"
→ Aggiungi `--collect-all=torch` in build script

### ❌ "PaddleOCR crash"
→ Verifica inclusione di tutti i file `.dll` con `--collect-all=paddlepaddle`

### ❌ "Finestra si chiude subito"
→ Rimuovi `--windowed` per vedere errori console

---

## 📊 Comparazione Metodi

| Metodo | Difficoltà | Dimensione | Velocità | Compatibilità |
|--------|-----------|-----------|----------|---------------|
| PyInstaller | ⭐ Facile | ~800MB | Normale | ✅ Ottima |
| Nuitka | ⭐⭐⭐ Medio | ~600MB | ⚡ Veloce | ⚠️ Richiede MSVC |
| cx_Freeze | ⭐⭐ Medio | ~750MB | Normale | ✅ Buona |

---

## 🎯 Raccomandazione

Per questo progetto, **PyInstaller** è la scelta migliore:
- ✅ Setup semplice (1 comando)
- ✅ Ottima compatibilità Qt6
- ✅ Supporto transformers/torch
- ✅ Build stabile e testata

**Command rapido:**
```bash
pip install pyinstaller
python build_windows.py
```

**Risultato:** `dist/LacTranslate.exe` pronto per distribuzione! 🎉
