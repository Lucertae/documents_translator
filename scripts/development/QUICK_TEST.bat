@echo off
chcp 65001 > nul
title LAC TRANSLATE - Quick Test
cls
echo ================================================
echo    LAC TRANSLATE v2.0 - Quick Test Avvio
echo ================================================
echo.
echo Verifica rapida funzionamento base...
echo.

echo [1/5] Verifica Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ✗ Python non trovato
    pause
    exit /b 1
) else (
    echo ✓ Python OK
    python --version
)
echo.

echo [2/5] Verifica dipendenze base...
python -c "import tkinter; print('✓ Tkinter OK')" 2>nul || echo ✗ Tkinter mancante
python -c "import pymupdf; print('✓ PyMuPDF OK')" 2>nul || echo ✗ PyMuPDF mancante
python -c "import PIL; print('✓ Pillow OK')" 2>nul || echo ✗ Pillow mancante
echo.

echo [3/5] Verifica moduli custom...
python -c "import sys; sys.path.insert(0, 'app'); from settings_manager import get_settings_manager; print('✓ Settings Manager OK')" 2>nul || echo ⚠ Settings Manager non disponibile (ok per testing)
python -c "import sys; sys.path.insert(0, 'app'); from batch_processor import BatchProcessor; print('✓ Batch Processor OK')" 2>nul || echo ⚠ Batch Processor non disponibile
echo.

echo [4/5] Avvio GUI...
echo.
echo ATTENZIONE: Il software è in modalità TESTING
echo - Licenze DISABILITATE
echo - Nessun controllo attivazione
echo.
echo L'applicazione si aprirà ora...
echo.
timeout /t 2 >nul
echo.

echo [5/5] Test Avvio Applicazione...
python app/pdf_translator_gui.py

if errorlevel 1 (
    echo.
    echo ✗ ERRORE durante avvio!
    echo.
    echo Verifica:
    echo - Tutte le dipendenze installate
    echo - Nessun errore nella console
    echo.
    pause
    exit /b 1
) else (
    echo.
    echo ✓ Applicazione chiusa correttamente
)

echo.
echo ================================================
echo    TEST COMPLETATO
echo ================================================
pause

