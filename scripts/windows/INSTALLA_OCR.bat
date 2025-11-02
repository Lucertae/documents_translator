@echo off
chcp 65001 > nul
title Installazione OCR LAC TRANSLATE
cls
echo ========================================
echo    INSTALLAZIONE OCR LAC TRANSLATE
echo ========================================
echo.
echo REQUISITI OCR:
echo - Tesseract OCR 5.0+ (obbligatorio)
echo - Language packs: Inglese + Italiano
echo - Spazio aggiuntivo: ~70MB
echo - Connessione internet per download
echo.

echo [1/4] Verifica prerequisiti...
python --version >nul 2>&1
if errorlevel 1 (
    echo ✗ Python non installato
    echo Esegui prima INSTALLA_DIPENDENZE.bat
    pause
    exit /b 1
) else (
    echo ✓ Python installato
)
echo.

echo [2/4] Installazione pacchetti Python OCR...
echo Installazione pytesseract e pdf2image...
pip install pytesseract>=0.3.10 pdf2image>=1.16.3
if errorlevel 1 (
    echo ✗ Errore installazione pacchetti OCR
    echo.
    echo POSSIBILI SOLUZIONI:
    echo 1. Verifica connessione internet
    echo 2. Aggiorna pip: python -m pip install --upgrade pip
    echo 3. Installa Visual C++ Redistributable
    echo.
    pause
    exit /b 1
) else (
    echo ✓ Pacchetti OCR installati
)
echo.

echo [3/4] Installazione Tesseract OCR...
echo.
echo METODO 1 - Installazione automatica (consigliato):
echo Tentativo installazione con winget...
winget install --id UB-Mannheim.TesseractOCR -e --silent >nul 2>&1
if errorlevel 1 (
    echo ✗ Installazione automatica fallita
    echo.
    echo METODO 2 - Installazione manuale:
    echo.
    echo ATTENZIONE: Devi installare Tesseract OCR manualmente!
    echo.
    echo PASSI:
    echo 1. Scarica Tesseract da: https://github.com/UB-Mannheim/tesseract/wiki
    echo 2. Installa Tesseract (consigliato: C:\Program Files\Tesseract-OCR)
    echo 3. Durante l'installazione, seleziona "English" e "Italian" language packs
    echo 4. Riavvia questo script dopo l'installazione
    echo.
    echo Apertura automatica del browser...
    timeout /t 3 >nul
    start https://github.com/UB-Mannheim/tesseract/wiki
    echo.
    pause
    exit /b 1
) else (
    echo ✓ Tesseract installato automaticamente
)
echo.

echo [4/4] Verifica installazione OCR...
echo Verifica Tesseract...
tesseract --version >nul 2>&1
if errorlevel 1 (
    echo ✗ Tesseract non trovato nel PATH
    echo.
    echo SOLUZIONE:
    echo 1. Riavvia il computer per aggiornare il PATH
    echo 2. Oppure aggiungi manualmente al PATH:
    echo    C:\Program Files\Tesseract-OCR
    echo.
    echo Verifica percorsi comuni...
    if exist "C:\Program Files\Tesseract-OCR\tesseract.exe" (
        echo ✓ Tesseract trovato in: C:\Program Files\Tesseract-OCR\
    ) else if exist "C:\Program Files (x86)\Tesseract-OCR\tesseract.exe" (
        echo ✓ Tesseract trovato in: C:\Program Files (x86)\Tesseract-OCR\
    ) else (
        echo ✗ Tesseract non trovato nei percorsi standard
    )
) else (
    echo ✓ Tesseract installato e funzionante
    tesseract --version | findstr "tesseract"
)
echo.

echo Verifica pacchetti Python...
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

echo ========================================
echo    INSTALLAZIONE OCR COMPLETATA!
echo ========================================
echo.
echo PROSSIMI PASSI:
echo 1. Esegui VERIFICA_INSTALLAZIONE.bat per controllo completo
echo 2. Avvia LAC TRANSLATE con AVVIA_GUI.bat
echo.
echo LIMITAZIONI OCR:
echo - Solo inglese/italiano di default
echo - Performance: 15-30 sec/pagina per OCR
echo - Qualità dipendente dalla risoluzione PDF
echo - Possibili errori di riconoscimento
echo.
pause

