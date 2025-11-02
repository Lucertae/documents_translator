@echo off
chcp 65001 > nul
title Riorganizzazione Progetto LAC TRANSLATE
cls
echo ================================================
echo    RIORGANIZZAZIONE PROGETTO LAC TRANSLATE
echo ================================================
echo.
echo Creazione struttura cartelle professionale...
echo.

REM Crea cartelle
echo [1/6] Creazione cartelle...
if not exist "scripts" mkdir scripts
if not exist "scripts\windows" mkdir scripts\windows
if not exist "scripts\development" mkdir scripts\development
if not exist "docs\internal" mkdir docs\internal
if not exist "docs\legal" mkdir docs\legal
if not exist "docs\user" mkdir docs\user
if not exist "dev" mkdir dev
if not exist "dev\status" mkdir dev\status
if not exist "build" mkdir build
if not exist "resources" mkdir resources
if not exist "resources\icons" mkdir resources\icons
echo ✓ Cartelle create
echo.

echo [2/6] Spostamento script Windows...
move AVVIA_GUI.bat scripts\windows\ 2>nul
move INSTALLA_DIPENDENZE.bat scripts\windows\ 2>nul
move INSTALLA_OCR.bat scripts\windows\ 2>nul
move VERIFICA_INSTALLAZIONE.bat scripts\windows\ 2>nul
move CREA_SHORTCUT_DESKTOP.bat scripts\windows\ 2>nul
move AGGIORNA_ICONA_DESKTOP.bat scripts\windows\ 2>nul
move RISOLVI_ICONA_DESKTOP.bat scripts\windows\ 2>nul
move QUICK_TEST.bat scripts\development\ 2>nul
move REORGANIZZA_PROGETTO.bat scripts\development\ 2>nul
echo ✓ Script Windows spostati
echo.

echo [3/6] Spostamento script PowerShell...
move *.ps1 scripts\windows\ 2>nul
echo ✓ Script PowerShell spostati
echo.

echo [4/6] Spostamento script installazione...
move INSTALL_MACOS.sh scripts\ 2>nul
move INSTALL_LINUX.sh scripts\ 2>nul
echo ✓ Script installazione spostati
echo.

echo [5/6] Spostamento documentazione...
move DOCUMENTAZIONE_SICUREZZA_E_LICENZE.md docs\internal\ 2>nul
move STATO_BUILD_E_GIU.md docs\internal\ 2>nul
move COSA_MANCA.md docs\internal\ 2>nul
move COSA_MANCA_RIEPILOGO.md docs\internal\ 2>nul
move COMPLETAMENTO_FINALE.md docs\internal\ 2>nul
move BUILD_COMPLETE.md docs\internal\ 2>nul
move STATO_COMPLETAMENTO.md docs\internal\ 2>nul
move RIEPILOGO_FINALE_COMPLETAMENTO.md docs\internal\ 2>nul
move README_MULTIPIATTAFORMA.md docs\internal\ 2>nul
move TESTING_CHECKLIST.md docs\internal\ 2>nul
move TESTING_MODE_README.md docs\internal\ 2>nul
move BUILD_README.md docs\internal\ 2>nul
move INSTALLER_README.md docs\internal\ 2>nul
move LICENSE_KEY_GENERATOR_README.md docs\internal\ 2>nul
move LICENSE.txt docs\legal\ 2>nul
move docs\PRIVACY_POLICY.md docs\legal\ 2>nul
move docs\TERMS_OF_SERVICE.md docs\legal\ 2>nul
move docs\README_DISTRIBUZIONE.md docs\user\ 2>nul
move docs\INSTALLAZIONE_MULTIPIATTAFORMA.md docs\user\ 2>nul
move guides\QUICK_START.txt docs\user\ 2>nul
echo ✓ Documentazione organizzata
echo.

echo [6/6] Spostamento file temporanei e risorse...
move status\*.* dev\status\ 2>nul
move logo_alt.ico resources\icons\ 2>nul
move application.log dev\ 2>nul
echo ✓ File temporanei spostati
echo.

echo.
echo ================================================
echo    RIORGANIZZAZIONE COMPLETATA!
echo ================================================
echo.
echo Nuova struttura:
echo   scripts\           - Script Windows/PowerShell
echo   docs\internal\     - Documentazione sviluppo
echo   docs\legal\        - Documenti legali
echo   docs\user\         - Documentazione utente
echo   dev\               - File sviluppo/temporanei
echo   resources\         - Risorse (icone, immagini)
echo   build\             - Build output (da creare)
echo.
echo PULIZIA VECCHIE CARTELLE...
if exist "status" rmdir /s /q status
echo.
pause

