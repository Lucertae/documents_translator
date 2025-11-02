@echo off
chcp 65001 > nul
title Aggiornamento Shortcut Desktop
cls
echo ================================================
echo    AGGIORNAMENTO SHORTCUT DESKTOP
echo ================================================
echo.

set "DESKTOP=%USERPROFILE%\Desktop"
REM Risolvi percorso assoluto progetto
for %%I in ("%~dp0\..\..") do set "PROJECT_ROOT=%%~fI"
set "SHORTCUT_NAME=Lac Translate.lnk"
set "ICON_PATH=%PROJECT_ROOT%\resources\icons\logo_alt.ico"
set "TARGET=%PROJECT_ROOT%\scripts\windows\AVVIA_GUI.bat"

cd /d "%PROJECT_ROOT%"

REM Rimuovi shortcut vecchio se esiste
if exist "%DESKTOP%\%SHORTCUT_NAME%" (
    echo Rimozione shortcut esistente...
    del /f /q "%DESKTOP%\%SHORTCUT_NAME%"
)

REM Crea nuovo shortcut usando PowerShell
echo Creazione nuovo shortcut...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
"$WshShell = New-Object -ComObject WScript.Shell; ^
$Shortcut = $WshShell.CreateShortcut('%DESKTOP%\%SHORTCUT_NAME%'); ^
$Shortcut.TargetPath = '%TARGET%'; ^
$Shortcut.WorkingDirectory = '%PROJECT_ROOT%'; ^
$Shortcut.IconLocation = '%ICON_PATH%'; ^
$Shortcut.Description = 'Lac Translate - Traduttore PDF'; ^
$Shortcut.Save()"

if exist "%DESKTOP%\%SHORTCUT_NAME%" (
    echo.
    echo ✓ Shortcut desktop aggiornato correttamente!
    echo.
    echo Percorso: %DESKTOP%\%SHORTCUT_NAME%
    echo Target: %TARGET%
    echo Icona: %ICON_PATH%
    echo.
) else (
    echo.
    echo ✗ ERRORE: Impossibile creare lo shortcut.
    echo.
)

pause

