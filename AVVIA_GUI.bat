@echo off
title Lac Translate - PDF Translator
cls
echo ========================================
echo    LAC TRANSLATE - PDF Translator
echo ========================================
echo.
echo Avvio interfaccia grafica...
echo.

cd /d "%~dp0"
python -m app.main_qt

if errorlevel 1 (
    echo.
    echo ERRORE: Impossibile avviare l'applicazione.
    echo.
    echo Verifica:
    echo - Python installato
    echo - Dipendenze installate: pip install -r requirements.txt
    echo.
)

pause

