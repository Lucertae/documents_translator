@echo off
chcp 65001 > nul
title Verifica Installazione LAC TRANSLATE
cls
echo ======================================
echo    VERIFICA INSTALLAZIONE LAC TRANSLATE
echo ======================================
echo.
echo Questo script verifica tutti i requisiti per LAC TRANSLATE
echo.

set /a errors=0
set /a warnings=0

echo [1/8] Verifica Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ✗ Python non installato
    echo   ERRORE CRITICO: Installa Python 3.8+ da: https://www.python.org/downloads/
    set /a errors+=1
) else (
    echo ✓ Python installato
    python --version
)
echo.

echo [2/8] Verifica spazio disco...
for /f "tokens=3" %%a in ('dir /-c ^| find "bytes free"') do set free=%%a
if %free% LSS 2000000000 (
    echo ⚠ Spazio disco limitato: %free% bytes
    echo   Consigliato: almeno 2GB liberi per modelli e OCR
    set /a warnings+=1
) else (
    echo ✓ Spazio disco sufficiente: %free% bytes
)
echo.

echo [3/8] Verifica pacchetti Python base...
python -c "import pymupdf; print('✓ PyMuPDF')" 2>nul
if errorlevel 1 (
    echo ✗ PyMuPDF mancante
    echo   SOLUZIONE: pip install PyMuPDF>=1.24.0
    set /a errors+=1
) else (
    echo ✓ PyMuPDF installato
)

python -c "import PIL; print('✓ Pillow')" 2>nul
if errorlevel 1 (
    echo ✗ Pillow mancante
    echo   SOLUZIONE: pip install Pillow>=10.0.0
    set /a errors+=1
) else (
    echo ✓ Pillow installato
)

python -c "import argostranslate; print('✓ Argos Translate')" 2>nul
if errorlevel 1 (
    echo ✗ Argos Translate mancante
    echo   SOLUZIONE: pip install argostranslate>=1.9.0
    set /a errors+=1
) else (
    echo ✓ Argos Translate installato
)

python -c "import deep_translator; print('✓ Deep Translator')" 2>nul
if errorlevel 1 (
    echo ✗ Deep Translator mancante
    echo   SOLUZIONE: pip install deep-translator>=1.11.4
    set /a errors+=1
) else (
    echo ✓ Deep Translator installato
)
echo.

echo [4/8] Verifica pacchetti OCR...
python -c "import pytesseract; print('✓ pytesseract')" 2>nul
if errorlevel 1 (
    echo ✗ pytesseract mancante
    echo   SOLUZIONE: pip install pytesseract>=0.3.10
    set /a errors+=1
) else (
    echo ✓ pytesseract installato
)

python -c "import pdf2image; print('✓ pdf2image')" 2>nul
if errorlevel 1 (
    echo ✗ pdf2image mancante
    echo   SOLUZIONE: pip install pdf2image>=1.16.3
    set /a errors+=1
) else (
    echo ✓ pdf2image installato
)
echo.

echo [5/8] Verifica Tesseract OCR...
tesseract --version >nul 2>&1
if errorlevel 1 (
    echo ✗ Tesseract OCR non installato o non nel PATH
    echo   SOLUZIONE: Installa Tesseract da: https://github.com/UB-Mannheim/tesseract/wiki
    echo   Oppure: winget install UB-Mannheim.TesseractOCR
    set /a errors+=1
    
    echo   Verifica percorsi comuni...
    if exist "C:\Program Files\Tesseract-OCR\tesseract.exe" (
        echo   ✓ Tesseract trovato in: C:\Program Files\Tesseract-OCR\
        echo   ⚠ Aggiungi al PATH: C:\Program Files\Tesseract-OCR
    ) else if exist "C:\Program Files (x86)\Tesseract-OCR\tesseract.exe" (
        echo   ✓ Tesseract trovato in: C:\Program Files (x86)\Tesseract-OCR\
        echo   ⚠ Aggiungi al PATH: C:\Program Files (x86)\Tesseract-OCR
    ) else (
        echo   ✗ Tesseract non trovato nei percorsi standard
    )
) else (
    echo ✓ Tesseract OCR installato
    tesseract --version | findstr "tesseract"
)
echo.

echo [6/8] Verifica modelli Argos...
python -c "import argostranslate.package; packages = argostranslate.package.get_installed_packages(); print(f'✓ {len(packages)} modelli Argos installati')" 2>nul
if errorlevel 1 (
    echo ✗ Modelli Argos non installati
    echo   SOLUZIONE: Esegui INSTALLA_DIPENDENZE.bat
    set /a errors+=1
) else (
    python -c "import argostranslate.package; packages = argostranslate.package.get_installed_packages(); print(f'✓ {len(packages)} modelli Argos installati')"
    if %errorlevel% neq 0 (
        echo ⚠ Modelli Argos installati ma verifica fallita
        set /a warnings+=1
    )
)
echo.

echo [7/8] Verifica file applicazione...
if exist "app\pdf_translator_gui.py" (
    echo ✓ GUI principale presente
) else (
    echo ✗ GUI principale mancante
    echo   ERRORE CRITICO: File app\pdf_translator_gui.py non trovato
    set /a errors+=1
)

if exist "app\setup_argos_models.py" (
    echo ✓ Setup Argos presente
) else (
    echo ✗ Setup Argos mancante
    echo   ERRORE CRITICO: File app\setup_argos_models.py non trovato
    set /a errors+=1
)

if exist "requirements.txt" (
    echo ✓ Requirements.txt presente
) else (
    echo ✗ Requirements.txt mancante
    set /a warnings+=1
)
echo.

echo [8/8] Verifica cartelle...
if exist "output\" (
    echo ✓ Cartella output presente
) else (
    echo ⚠ Cartella output mancante (verrà creata automaticamente)
    set /a warnings+=1
)

if exist "logs\" (
    echo ✓ Cartella logs presente
) else (
    echo ⚠ Cartella logs mancante (verrà creata automaticamente)
    set /a warnings+=1
)

if exist "docs\" (
    echo ✓ Cartella docs presente
) else (
    echo ⚠ Cartella docs mancante
    set /a warnings+=1
)
echo.

echo ======================================
echo    RISULTATO VERIFICA
echo ======================================
echo.

if %errors% equ 0 (
    if %warnings% equ 0 (
        echo ✅ INSTALLAZIONE COMPLETA E PERFETTA!
        echo.
        echo Tutti i componenti sono installati correttamente.
        echo Puoi avviare LAC TRANSLATE con AVVIA_GUI.bat
    ) else (
        echo ✅ INSTALLAZIONE FUNZIONALE CON AVVISI
        echo.
        echo Tutti i componenti essenziali sono installati.
        echo Ci sono %warnings% avvisi minori (vedi sopra).
        echo Puoi avviare LAC TRANSLATE con AVVIA_GUI.bat
    )
) else (
    echo ❌ INSTALLAZIONE INCOMPLETA
    echo.
    echo Ci sono %errors% errori critici che impediscono il funzionamento.
    echo Risolvi gli errori sopra prima di usare LAC TRANSLATE.
    echo.
    echo SOLUZIONI RAPIDE:
    echo 1. Esegui INSTALLA_DIPENDENZE.bat
    echo 2. Esegui INSTALLA_OCR.bat
    echo 3. Riavvia il computer
    echo 4. Contatta il supporto tecnico
)

echo.
echo ======================================
echo    INFORMAZIONI SISTEMA
echo ======================================
echo.
echo Sistema operativo: %OS%
echo Architettura: %PROCESSOR_ARCHITECTURE%
echo Spazio libero: %free% bytes
echo Errori: %errors%
echo Avvisi: %warnings%
echo.

echo LIMITAZIONI NOTA:
echo - Argos Translate: Qualità inferiore a Google, solo 7 lingue
echo - OCR: Solo inglese/italiano, 15-30 sec/pagina
echo - Installazione: Richiede competenze tecniche
echo - Windows: Script batch solo per Windows
echo.

pauseecho ✗ Cartella output mancante
)

if exist "logs\" (
    echo ✓ Cartella logs presente
) else (
    echo ✗ Cartella logs mancante
)
echo.

echo ======================================
echo    VERIFICA COMPLETATA!
echo ======================================
echo.

echo PROSSIMI PASSI:
echo 1. Se ci sono errori, esegui INSTALLA_DIPENDENZE.bat
echo 2. Per OCR, esegui INSTALLA_OCR.bat
echo 3. Avvia con AVVIA_GUI.bat
echo.

pause
