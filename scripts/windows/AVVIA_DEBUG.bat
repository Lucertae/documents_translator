@echo off
REM Versione DEBUG di AVVIA.bat - mostra messaggi e errori
REM Usa questo per capire cosa non funziona

cd /d "%~dp0\..\.."

echo ========================================
echo    LAC TRANSLATE - DEBUG MODE
echo ========================================
echo.
echo Verifica percorsi...
echo.

REM Verifica percorso corrente
echo Percorso corrente: %CD%
echo.

REM Verifica file
if exist "app\pdf_translator_gui.py" (
    echo [OK] File pdf_translator_gui.py trovato
) else (
    echo [ERRORE] File pdf_translator_gui.py NON trovato!
    echo Percorso cercato: %CD%\app\pdf_translator_gui.py
    pause
    exit /b 1
)

echo.
echo Verifica Python...
echo.

REM Verifica pythonw.exe
where pythonw.exe >nul 2>&1
if %ERRORLEVEL% == 0 (
    echo [OK] pythonw.exe trovato
    pythonw.exe --version
) else (
    echo [WARNING] pythonw.exe NON trovato
)

echo.
REM Verifica python.exe
where python.exe >nul 2>&1
if %ERRORLEVEL% == 0 (
    echo [OK] python.exe trovato
    python.exe --version
) else (
    echo [ERRORE] python.exe NON trovato!
    pause
    exit /b 1
)

echo.
echo ========================================
echo Avvio applicazione...
echo ========================================
echo.

REM Prova con pythonw.exe
where pythonw.exe >nul 2>&1
if %ERRORLEVEL% == 0 (
    echo Usando pythonw.exe...
    pythonw.exe app\pdf_translator_gui.py
    if errorlevel 1 (
        echo.
        echo [ERRORE] pythonw.exe fallito, provo con python.exe...
        python.exe app\pdf_translator_gui.py
    )
) else (
    echo Usando python.exe...
    python.exe app\pdf_translator_gui.py
)

if errorlevel 1 (
    echo.
    echo ========================================
    echo ERRORE durante avvio!
    echo ========================================
    echo.
    echo Controlla:
    echo - Python installato correttamente
    echo - Dipendenze installate: pip install -r requirements.txt
    echo - File pdf_translator_gui.py presente
    echo.
)

pause

