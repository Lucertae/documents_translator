@echo off
REM LAC TRANSLATE - Script Primo Versioning
REM Esegue tutti i passi per prima release con security

echo ============================================================
echo LAC TRANSLATE - Primo Versioning e Attivazione Security
echo ============================================================
echo.

REM Step 1: Verifica versione
echo [1/7] Verifica versione corrente...
python app/version.py
if errorlevel 1 (
    echo ERRORE: Verifica versione fallita
    pause
    exit /b 1
)
echo.

REM Step 2: Genera integrity manifest
echo [2/7] Genera integrity manifest...
python scripts/development/create_integrity_manifest.py
if errorlevel 1 (
    echo ERRORE: Generazione manifest fallita
    pause
    exit /b 1
)
echo.

REM Step 3: Verifica manifest creato
echo [3/7] Verifica manifest creato...
if not exist "security\file_manifest.json" (
    echo ERRORE: Manifest non creato
    pause
    exit /b 1
)
echo Manifest creato: security\file_manifest.json
echo.

REM Step 4: Test security modules
echo [4/7] Test security modules...
python -c "from security import get_security_manager; sm = get_security_manager(); print('✓ Security Manager OK')"
python -c "from app.integrity_checker import IntegrityChecker; from pathlib import Path; ic = IntegrityChecker(); result = ic.check_critical_files(); print(f'✓ Integrity Checker OK (status: {result})')"
python -c "from app.security_validator import get_security_validator; from pathlib import Path; sv = get_security_validator(); results = sv.perform_security_checks(); print(f'✓ Security Validator OK (status: {results[\"overall_status\"]})')"
echo.

REM Step 5: Chiedi conferma prima di tag
echo [5/7] Preparazione tag...
echo.
echo ATTENZIONE: Stai per creare il tag di versione!
echo.
set /p VERSION="Inserisci versione (es. 2.0.0): "
if "%VERSION%"=="" (
    echo ERRORE: Versione non specificata
    pause
    exit /b 1
)

echo.
set /p CONFIRM="Confermi creazione tag v%VERSION%? (s/n): "
if /i not "%CONFIRM%"=="s" (
    echo Operazione annullata
    pause
    exit /b 0
)

REM Step 6: Crea tag
echo [6/7] Creazione tag v%VERSION%...
git tag -a v%VERSION% -m "Release v%VERSION% - First production release with security system"
if errorlevel 1 (
    echo ERRORE: Creazione tag fallita
    pause
    exit /b 1
)
echo Tag v%VERSION% creato
echo.

REM Step 7: Push tag
echo [7/7] Push tag su GitHub...
set /p PUSH="Vuoi pusare il tag su GitHub ora? (s/n): "
if /i "%PUSH%"=="s" (
    git push origin v%VERSION%
    if errorlevel 1 (
        echo ERRORE: Push tag fallito
        pause
        exit /b 1
    )
    echo Tag v%VERSION% pushato su GitHub
    echo.
    echo ============================================================
    echo COMPLETATO!
    echo ============================================================
    echo.
    echo Il tag e' stato pushato. GitHub Actions dovrebbe:
    echo 1. Buildare automaticamente l'installer Windows
    echo 2. Creare GitHub Release automaticamente
    echo 3. Upload installer alla release
    echo.
    echo Controlla: https://github.com/Lucertae/documents_translator/actions
    echo.
) else (
    echo Tag creato localmente. Per pusare:
    echo   git push origin v%VERSION%
)

pause

