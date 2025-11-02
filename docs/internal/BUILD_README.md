# Build LAC TRANSLATE - Istruzioni

## Prerequisiti

1. **Python 3.8+** installato
2. **PyInstaller** installato:
   ```bash
   pip install pyinstaller
   ```
3. Tutte le dipendenze del progetto:
   ```bash
   pip install -r requirements.txt
   ```

## Build Automatico

Esegui lo script di build:

```bash
python build.py
```

Lo script esegue automaticamente:
1. Pulizia build precedenti
2. Verifica dipendenze
3. Compilazione eseguibile con PyInstaller
4. Copia file aggiuntivi
5. Creazione package distribuzione
6. Riepilogo build

## Build Manuale

Se preferisci build manuale:

```bash
# Pulisci build precedenti
rm -rf build dist

# Compila con PyInstaller
pyinstaller --clean lac_translate.spec

# L'eseguibile sarà in: dist/LAC_Translate.exe
```

## Output

Dopo il build, troverai:

- `dist/LAC_Translate.exe` - Eseguibile standalone
- `release/LAC_Translate_vX.X_TIMESTAMP/` - Package distribuzione completo
- `release/LAC_Translate_vX.X_TIMESTAMP.zip` - ZIP per distribuzione

## Note

- L'eseguibile è standalone e include tutte le dipendenze Python
- Modelli Argos Translate devono essere scaricati separatamente al primo avvio
- Tesseract OCR deve essere installato separatamente per funzionalità OCR
- Dimensione eseguibile: ~50-100 MB (dipende da dipendenze incluse)

## Troubleshooting

### Errore: "PyInstaller not found"
```bash
pip install pyinstaller
```

### Errore: "Module not found"
Verifica che tutte le dipendenze siano installate:
```bash
pip install -r requirements.txt
```

### Eseguibile troppo grande
Modifica `lac_translate.spec` per escludere moduli non necessari nella sezione `excludes`.

### Antivirus segnala falso positivo
PyInstaller può generare falsi positivi. Aggiungi eccezione nell'antivirus o firma digitalmente l'eseguibile.

