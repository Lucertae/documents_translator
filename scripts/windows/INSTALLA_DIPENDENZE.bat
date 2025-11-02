@echo off
chcp 65001 > nul
title Installazione Dipendenze LAC TRANSLATE
cls
echo ========================================
echo    INSTALLAZIONE DIPENDENZE LAC TRANSLATE
echo ========================================
echo.
echo REQUISITI SISTEMA:
echo - Windows 10/11
echo - Python 3.8+ (obbligatorio)
echo - RAM: 4GB minimo, 8GB consigliato
echo - Spazio disco: 2GB liberi
echo - Connessione internet per download modelli
echo.

echo [1/5] Verifica Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ✗ Python non installato
    echo.
    echo ERRORE: Python 3.8+ è obbligatorio!
    echo.
    echo SOLUZIONE:
    echo 1. Scarica Python da: https://www.python.org/downloads/
    echo 2. Durante l'installazione, seleziona "Add Python to PATH"
    echo 3. Riavvia questo script dopo l'installazione
    echo.
    pause
    exit /b 1
) else (
    echo ✓ Python installato
    python --version
)
echo.

echo [2/5] Verifica spazio disco...
for /f "tokens=3" %%a in ('dir /-c ^| find "bytes free"') do set free=%%a
if %free% LSS 2000000000 (
    echo ⚠ Spazio disco limitato: %free% bytes
    echo   Consigliato: almeno 2GB liberi
) else (
    echo ✓ Spazio disco sufficiente: %free% bytes
)
echo.

echo [3/5] Installazione librerie Python...
echo Installazione pacchetti base...
pip install PyMuPDF>=1.24.0 Pillow>=10.0.0 argostranslate>=1.9.0 deep-translator>=1.11.4
if errorlevel 1 (
    echo ✗ Errore installazione pacchetti base
    echo.
    echo POSSIBILI SOLUZIONI:
    echo 1. Verifica connessione internet
    echo 2. Aggiorna pip: python -m pip install --upgrade pip
    echo 3. Usa proxy se necessario: pip install --proxy http://proxy:port package
    echo.
    pause
    exit /b 1
) else (
    echo ✓ Pacchetti base installati
)
echo.

echo [4/5] Installazione modelli Argos Translate...
echo ATTENZIONE: Download di ~800MB di modelli linguistici
echo Questo può richiedere 5-15 minuti a seconda della connessione
echo.
cd /d "%~dp0\app"
python setup_argos_models.py
if errorlevel 1 (
    echo ✗ Errore installazione modelli Argos
    echo.
    echo POSSIBILI SOLUZIONI:
    echo 1. Verifica connessione internet stabile
    echo 2. Riavvia il computer e riprova
    echo 3. Contatta il supporto tecnico
    echo.
    pause
    exit /b 1
) else (
    echo ✓ Modelli Argos installati
)
echo.

echo [5/5] Verifica installazione...
python -c "import pymupdf, PIL, argostranslate, deep_translator; print('✓ Tutte le dipendenze installate')" 2>nul
if errorlevel 1 (
    echo ✗ Verifica fallita - alcune dipendenze mancanti
    echo Esegui VERIFICA_INSTALLAZIONE.bat per diagnosi dettagliata
) else (
    echo ✓ Verifica completata con successo
)
echo.

echo ========================================
echo    INSTALLAZIONE COMPLETATA!
echo ========================================
echo.
echo PROSSIMI PASSI:
echo 1. Esegui INSTALLA_OCR.bat per funzionalità OCR
echo 2. Esegui VERIFICA_INSTALLAZIONE.bat per controllo completo
echo 3. Avvia LAC TRANSLATE con AVVIA_GUI.bat
echo.
echo LIMITAZIONI NOTA:
echo - Argos Translate: Qualità inferiore a Google, solo 7 lingue
echo - OCR: Solo inglese/italiano, 15-30 sec/pagina
echo - Installazione: Richiede competenze tecniche
echo.
pause

