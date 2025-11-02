@echo off
REM Script per compilare CREA_INSTALLER.py in .exe
REM Crea CREA_INSTALLER.exe dalla versione Python

echo ============================================================
echo LAC TRANSLATE - Compilazione CREA_INSTALLER.exe
echo ============================================================
echo.

REM Verifica Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRORE: Python non trovato!
    pause
    exit /b 1
)

REM Verifica PyInstaller
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

echo Compilazione CREA_INSTALLER.exe...
cd /d "%~dp0"
python -m PyInstaller --clean --onefile crea_installer.spec

if errorlevel 1 (
    echo ERRORE durante compilazione
    pause
    exit /b 1
)

REM Verifica eseguibile creato
if exist "dist\CREA_INSTALLER.exe" (
    echo.
    echo ============================================================
    echo ✓ CREA_INSTALLER.exe CREATO!
    echo ============================================================
    echo.
    echo File: dist\CREA_INSTALLER.exe
    echo.
    echo Puoi usare questo .exe invece del .bat
    echo Funzionalità identica, aspetto più professionale.
    echo.
) else (
    echo ERRORE: Eseguibile non trovato dopo compilazione
    pause
    exit /b 1
)

pause

