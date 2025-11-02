@echo off
REM Avvia LAC TRANSLATE senza mostrare terminale
REM Usa pythonw.exe o python con launcher migliorato

cd /d "%~dp0\..\.."

REM Verifica che i file esistano
if not exist "app\launcher.py" (
    if not exist "app\pdf_translator_gui.py" (
        mshta "javascript:alert('ERRORE: File applicazione non trovato!');close();"
        exit /b 1
    )
    set LAUNCH_FILE=app\pdf_translator_gui.py
) else (
    set LAUNCH_FILE=app\launcher.py
)

REM Cerca pythonw.exe (migliore - no console)
where pythonw.exe >nul 2>&1
if %ERRORLEVEL% == 0 (
    start "" pythonw.exe %LAUNCH_FILE%
    exit /b 0
)

REM Fallback: python.exe
where python.exe >nul 2>&1
if %ERRORLEVEL% == 0 (
    start "" /min python %LAUNCH_FILE%
    exit /b 0
)

REM Python non trovato
mshta "javascript:alert('ERRORE: Python non trovato!');close();"
exit /b 1


