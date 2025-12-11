@echo off
chcp 65001 > nul
echo ======================================
echo    VERIFICA INSTALLAZIONE LAC TRANSLATE
echo ======================================
echo.

echo [1/6] Verifica Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ✗ Python non installato
    echo   Installa Python 3.11+ da: https://www.python.org/downloads/
) else (
    echo ✓ Python installato
    python --version
)
echo.

echo [2/6] Verifica pacchetti Python...
python -c "import pymupdf; print('✓ PyMuPDF')" 2>nul
if errorlevel 1 echo ✗ PyMuPDF mancante

python -c "import PIL; print('✓ Pillow')" 2>nul
if errorlevel 1 echo ✗ Pillow mancante

python -c "import argostranslate; print('✓ Argos Translate')" 2>nul
if errorlevel 1 echo ✗ Argos Translate mancante

python -c "import pytesseract; print('✓ pytesseract')" 2>nul
if errorlevel 1 echo ✗ pytesseract mancante

python -c "import pdf2image; print('✓ pdf2image')" 2>nul
if errorlevel 1 echo ✗ pdf2image mancante
echo.

echo [3/6] Verifica Tesseract OCR...
tesseract --version >nul 2>&1
if errorlevel 1 (
    echo ✗ Tesseract OCR non installato
    echo   Esegui: INSTALLA_OCR.bat
) else (
    echo ✓ Tesseract OCR installato
    tesseract --version | findstr "tesseract"
)
echo.

echo [4/6] Verifica modelli Argos...
python -c "import argostranslate.package; packages = argostranslate.package.get_installed_packages(); print(f'✓ {len(packages)} modelli Argos installati')" 2>nul
if errorlevel 1 echo ✗ Modelli Argos non installati
echo.

echo [5/6] Verifica file applicazione...
if exist "app\pdf_translator_gui.py" (
    echo ✓ GUI principale presente
) else (
    echo ✗ GUI principale mancante
)

if exist "app\setup_argos_models.py" (
    echo ✓ Setup Argos presente
) else (
    echo ✗ Setup Argos mancante
)
echo.

echo [6/6] Verifica cartelle...
if exist "output\" (
    echo ✓ Cartella output presente
) else (
    echo ✗ Cartella output mancante
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
