@echo off
REM LAC TRANSLATE - Script Creazione Installer Windows
REM Crea eseguibile .exe e installer .exe completo per distribuzione

echo ============================================================
echo LAC TRANSLATE - Creazione Installer Windows
echo ============================================================
echo.

REM Verifica Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRORE: Python non trovato!
    echo Installa Python da: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/5] Verifica dipendenze...
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo PyInstaller non trovato, installazione...
    pip install pyinstaller
    if errorlevel 1 (
        echo ERRORE: Impossibile installare PyInstaller
        pause
        exit /b 1
    )
)
echo ✓ PyInstaller pronto
echo.

echo [2/5] Build eseguibile .exe...
python build.py
if errorlevel 1 (
    echo ERRORE durante build eseguibile
    pause
    exit /b 1
)
echo.

echo [3/5] Verifica eseguibile creato...
if not exist "dist\LAC_Translate.exe" (
    echo ERRORE: Eseguibile non trovato dopo build
    pause
    exit /b 1
)
echo ✓ Eseguibile creato: dist\LAC_Translate.exe
echo.

echo [4/5] Verifica InnoSetup...
where ISCC.exe >nul 2>&1
if errorlevel 1 (
    REM Cerca InnoSetup in percorsi comuni
    set INNO_FOUND=0
    if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
        set "INNO_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
        set INNO_FOUND=1
    )
    if exist "C:\Program Files\Inno Setup 6\ISCC.exe" (
        set "INNO_PATH=C:\Program Files\Inno Setup 6\ISCC.exe"
        set INNO_FOUND=1
    )
    
    if %INNO_FOUND%==0 (
        echo.
        echo ⚠ ATTENZIONE: InnoSetup non trovato!
        echo.
        echo Per creare l'installer professionale, installa InnoSetup:
        echo 1. Scarica da: https://jrsoftware.org/isdl.php
        echo 2. Installa Inno Setup 6
        echo 3. Rilancia questo script
        echo.
        echo L'eseguibile e' stato creato in dist\LAC_Translate.exe
        echo Puoi distribuirlo manualmente, ma senza installer.
        echo.
        pause
        exit /b 0
    )
) else (
    set "INNO_PATH=ISCC.exe"
)

echo ✓ InnoSetup trovato
echo.

echo [5/5] Creazione installer...
"%INNO_PATH%" installer_setup.iss
if errorlevel 1 (
    echo ERRORE durante creazione installer
    pause
    exit /b 1
)
echo.

echo ============================================================
echo ✓ INSTALLER COMPLETATO!
echo ============================================================
echo.
echo Installer creato in: release\installer\
echo.
dir /b release\installer\*.exe
echo.
echo Puoi distribuire questo installer agli utenti finali.
echo L'utente non deve installare Python - tutto e' incluso!
echo.
pause

