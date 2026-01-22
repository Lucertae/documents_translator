@echo off
title Installazione Dipendenze
cls
echo ========================================
echo    INSTALLAZIONE DIPENDENZE
echo ========================================
echo.
echo Installazione librerie Python necessarie...
echo.

pip install PyMuPDF Pillow argostranslate

echo.
echo ========================================
echo Installazione modelli Argos Translate...
echo ========================================
echo.

cd /d "%~dp0\app"
python setup_argos_models.py

echo.
echo ========================================
echo INSTALLAZIONE COMPLETATA!
echo ========================================
echo.
echo Ora puoi avviare LAC TRANSLATE con: AVVIA_GUI.bat
echo.

pause

