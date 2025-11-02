# Installer LAC TRANSLATE - Istruzioni

## Prerequisiti

Per creare l'installer Windows è necessario:

1. **InnoSetup** installato (versione 6.x)
   - Download: https://jrsoftware.org/isdl.php
   - Versione consigliata: 6.2.2 o superiore

2. **File compilati**
   - Eseguibile `LAC_Translate.exe` in `dist/`
   - Creato tramite PyInstaller (`python build.py`)

## Creazione Installer

### Metodo 1: GUI InnoSetup

1. Apri InnoSetup Compiler
2. File → Apri → Seleziona `installer_setup.iss`
3. Build → Compile (F9)
4. L'installer sarà creato in `release/installer/LAC_Translate_v2.0_Setup.exe`

### Metodo 2: Script Automatico

Esegui lo script di build che include anche la creazione dell'installer:

```bash
python build.py
```

Lo script verificherà se InnoSetup è installato e creerà automaticamente l'installer.

### Metodo 3: Command Line

```bash
# Path InnoSetup (tipico su Windows)
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer_setup.iss
```

## Struttura Installer

L'installer creato include:

- Eseguibile principale `LAC_Translate.exe`
- README e LICENSE
- Shortcut desktop (opzionale)
- Shortcut menu Start
- Disinstallatore completo
- Wizard di installazione professionale

## Personalizzazione

### Modificare versione

Edita `installer_setup.iss`:
```
#define MyAppVersion "2.0"
```

### Aggiungere file aggiuntivi

Aggiungi nella sezione `[Files]`:
```
Source: "path\to\file"; DestDir: "{app}"; Flags: ignoreversion
```

### Modificare percorso installazione

Modifica `DefaultDirName`:
```
DefaultDirName={autopf}\{#MyAppName}  ; Program Files
DefaultDirName={localappdata}\{#MyAppName}  ; AppData Local
```

## Testing Installer

Prima di distribuire:

1. **Test installazione pulita**
   - Disinstalla versione precedente
   - Installa nuova versione
   - Verifica funzionamento

2. **Test disinstallazione**
   - Installa software
   - Usa disinstallatore
   - Verifica rimozione completa

3. **Test su Windows pulito**
   - Installa su VM Windows 10/11 clean
   - Verifica prerequisiti installati correttamente

4. **Test privilegi**
   - Installa senza privilegi admin
   - Installa con privilegi admin
   - Verifica funzionamento in entrambi i casi

## Problemi Comuni

### Errore: "ISCC.exe not found"
- Verifica che InnoSetup sia installato
- Aggiungi path InnoSetup al PATH di sistema
- Oppure usa path completo nel comando

### Installer troppo grande
- Compressione già configurata (lzma)
- Rimuovi file non necessari dalla sezione `[Files]`
- Considera installer separato per modelli Argos

### Falsi positivi antivirus
- Firma digitalmente l'installer con certificato
- Aggiungi installer a whitelist antivirus durante testing
- Comunicare agli utenti che è un falso positivo

## Distribuzione

File da distribuire:

1. **LAC_Translate_v2.0_Setup.exe** - Installer principale
2. **README_UTENTE_FINALE.pdf** - Guida installazione
3. **LICENSE.txt** - Licenza software
4. **CHANGELOG.txt** - Modifiche versione

## Note

- L'installer NON include modelli Argos Translate (da scaricare al primo avvio)
- L'installer NON include Tesseract OCR (installazione separata consigliata)
- Le directory `config`, `license`, `logs`, `output` vengono create al primo avvio

