@echo off
chcp 65001 > nul
echo ======================================
echo    INSTALLAZIONE OCR per LAC TRANSLATE
echo ======================================
echo.

echo [1/3] Installazione pacchetti Python OCR...
pip install pytesseract pdf2image
echo.

echo [2/3] Download Tesseract OCR...
echo.
echo ATTENZIONE: Devi installare Tesseract OCR manualmente!
echo.
echo 1. Scarica Tesseract da: https://github.com/UB-Mannheim/tesseract/wiki
echo 2. Installa Tesseract (consigliato: C:\Program Files\Tesseract-OCR)
echo 3. Durante l'installazione, seleziona "English" e "Italian" language packs
echo.
echo Oppure usa il comando winget (se disponibile):
echo    winget install UB-Mannheim.TesseractOCR
echo.

echo [3/3] Verifica installazione...
python -c "import pytesseract; print('✓ pytesseract installato')" 2>nul
if errorlevel 1 (
    echo ✗ pytesseract non installato
) else (
    echo ✓ pytesseract installato
)

python -c "import pdf2image; print('✓ pdf2image installato')" 2>nul
if errorlevel 1 (
    echo ✗ pdf2image non installato
) else (
    echo ✓ pdf2image installato
)

echo.
echo ======================================
echo    INSTALLAZIONE COMPLETATA!
echo ======================================
echo.
echo PROSSIMI PASSI:
echo 1. Installa Tesseract OCR dal link sopra
echo 2. Riavvia LAC TRANSLATE con AVVIA_GUI.bat
echo.
pause

