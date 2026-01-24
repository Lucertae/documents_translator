@echo off
title Installazione Dipendenze
cls
echo ========================================
echo    INSTALLAZIONE DIPENDENZE
echo ========================================
echo.
echo Installazione librerie Python necessarie...
echo.

cd /d "%~dp0"
pip install -r requirements.txt

echo.
echo ========================================
echo INSTALLAZIONE COMPLETATA!
echo ========================================
echo.
echo I modelli di traduzione OPUS-MT verranno scaricati automaticamente
echo al primo avvio dell'applicazione.
echo.
echo Ora puoi avviare LAC TRANSLATE con: AVVIA_GUI.bat
echo.

pause

