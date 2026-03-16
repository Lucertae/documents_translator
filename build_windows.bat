@echo off
REM ===========================================
REM LAC Translate - Windows Complete Build Script
REM Gestisce tutto: Python, venv, dipendenze, build
REM ===========================================

setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo ==========================================
echo   LAC Translate - Windows Build
echo ==========================================
echo.
echo Directory: %CD%
echo.

REM ==========================================
REM STEP 1: Verifica Python
REM ==========================================
echo [1/5] Verifico Python...

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [ERRORE] Python non trovato!
    echo.
    echo Scarica Python da: https://www.python.org/downloads/
    echo IMPORTANTE: Durante l'installazione seleziona "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

python --version
echo.

REM ==========================================
REM STEP 2: Crea/Aggiorna Virtual Environment
REM ==========================================
echo [2/5] Configuro virtual environment...

if exist ".venv\Scripts\python.exe" (
    echo     Virtual environment esistente, lo uso.
) else (
    echo     Creo nuovo virtual environment...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [ERRORE] Impossibile creare virtual environment
        pause
        exit /b 1
    )
)

REM Attiva il venv
call .venv\Scripts\activate.bat
echo     Attivato: %VIRTUAL_ENV%
echo.

REM ==========================================
REM STEP 3: Installa/Aggiorna dipendenze
REM ==========================================
echo [3/5] Installo dipendenze (questo puo' richiedere alcuni minuti)...
echo.

REM Aggiorna pip
python -m pip install --upgrade pip --quiet

REM Installa requirements
pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo [ERRORE] Errore installando le dipendenze
    echo Provo senza --quiet per vedere l'errore:
    pip install -r requirements.txt
    pause
    exit /b 1
)

REM Installa PyInstaller se non presente
pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo     Installo PyInstaller...
    pip install pyinstaller --quiet
)

echo     Dipendenze installate correttamente.
echo.

REM ==========================================
REM STEP 4: Verifica che PySide6 sia installato
REM ==========================================
echo [4/7] Verifico PySide6...

python -c "import PySide6; print(f'    PySide6 versione: {PySide6.__version__}')" 2>nul
if %errorlevel% neq 0 (
    echo     PySide6 non trovato, lo installo...
    pip install PySide6
)

python -c "import torch; print(f'    PyTorch versione: {torch.__version__}')" 2>nul
if %errorlevel% neq 0 (
    echo     [AVVISO] PyTorch non installato - la traduzione potrebbe non funzionare
)

echo.

REM ==========================================
REM STEP 5: Build con PyInstaller
REM ==========================================
echo [5/7] Avvio build con PyInstaller...
echo     Questo puo' richiedere 5-10 minuti...
echo.

REM Pulisce build precedenti
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist

REM Esegue PyInstaller
pyinstaller lac_translate.spec --clean --noconfirm

if %errorlevel% neq 0 (
    echo.
    echo [ERRORE] Build fallita!
    echo.
    pause
    exit /b 1
)

REM ==========================================
REM STEP 6: Verifica risultato
REM ==========================================
if not exist "dist\lac-translate\lac-translate.exe" (
    echo.
    echo [ERRORE] Build fallita - eseguibile non trovato
    echo Controlla i messaggi di errore sopra.
    echo.
    pause
    exit /b 1
)

echo.
echo ==========================================
echo   BUILD PYINSTALLER COMPLETATA
echo ==========================================
echo.
echo   dist\lac-translate\lac-translate.exe
echo.

REM Crea script di avvio (utile anche dentro l'installer)
echo @echo off > "dist\lac-translate\Avvia LAC Translate.bat"
echo cd /d "%%~dp0" >> "dist\lac-translate\Avvia LAC Translate.bat"
echo start "" lac-translate.exe >> "dist\lac-translate\Avvia LAC Translate.bat"

REM ==========================================
REM STEP 7: Crea installer con Inno Setup
REM ==========================================
echo [7/7] Creo l'installer con Inno Setup...
echo.

set "ISCC="
REM Cerca Inno Setup nelle posizioni standard
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
)
if exist "C:\Program Files\Inno Setup 6\ISCC.exe" (
    set "ISCC=C:\Program Files\Inno Setup 6\ISCC.exe"
)

if defined ISCC (
    echo     Trovato Inno Setup: %ISCC%
    "%ISCC%" installer.iss
    if !errorlevel! equ 0 (
        echo.
        echo ==========================================
        echo   INSTALLER CREATO CON SUCCESSO!
        echo ==========================================
        echo.
        echo   dist\LAC-Translate-Setup-*.exe
        echo.
    ) else (
        echo.
        echo [AVVISO] Compilazione Inno Setup fallita.
        echo L'exe standalone e' comunque disponibile in dist\lac-translate\
        echo.
    )
) else (
    echo     [INFO] Inno Setup non trovato — skip creazione installer.
    echo     Installa Inno Setup 6 da https://jrsoftware.org/isinfo.php
    echo     per generare automaticamente un Setup.exe
    echo.
    echo     L'applicazione standalone e' comunque pronta in:
    echo       dist\lac-translate\lac-translate.exe
    echo.
)

pause
