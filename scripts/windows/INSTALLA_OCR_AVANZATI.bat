@echo off
chcp 65001 > nul
title Installazione OCR Avanzati - Dolphin e Chandra
cls
echo ================================================
echo    INSTALLAZIONE OCR AVANZATI
echo    Dolphin OCR e Chandra OCR
echo ================================================
echo.

cd /d "%~dp0\..\.."

REM Verifica Git installato
where git >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERRORE] Git non trovato!
    echo.
    echo Installa Git da: https://git-scm.com/download/win
    echo.
    pause
    exit /b 1
)

echo [1/4] Verifica Python...
python --version
if errorlevel 1 (
    echo [ERRORE] Python non trovato!
    pause
    exit /b 1
)
echo [OK] Python trovato
echo.

REM Installa dipendenze base per OCR avanzati
echo [2/4] Installazione dipendenze base...
python -m pip install --upgrade pip
python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
python -m pip install transformers huggingface_hub
echo [OK] Dipendenze installate
echo.

REM Installazione Dolphin OCR
echo [3/4] Installazione Dolphin OCR...
echo.

REM Verifica se già installato
if exist "Dolphin" (
    echo Dolphin già presente. Vuoi aggiornare? (S/N)
    set /p update_dolphin=
    if /i "%update_dolphin%"=="S" (
        echo Aggiornamento Dolphin...
        cd Dolphin
        git pull
        cd ..
    ) else (
        echo Salto installazione Dolphin (già presente)
        goto :chandra
    )
) else (
    echo Clonazione repository Dolphin...
    git clone https://github.com/bytedance/Dolphin.git
    if errorlevel 1 (
        echo [ERRORE] Clonazione Dolphin fallita!
        goto :chandra
    )
    
    cd Dolphin
    echo Installazione dipendenze Dolphin...
    python -m pip install -r requirements.txt
    cd ..
    
    echo [OK] Dolphin installato
)

:chandra
echo.
REM Installazione Chandra OCR
echo [4/4] Installazione Chandra OCR...
echo.

if exist "chandra" (
    echo Chandra già presente. Vuoi aggiornare? (S/N)
    set /p update_chandra=
    if /i "%update_chandra%"=="S" (
        echo Aggiornamento Chandra...
        cd chandra
        git pull
        cd ..
    ) else (
        echo Salto installazione Chandra (già presente)
        goto :download_models
    )
) else (
    echo Clonazione repository Chandra...
    git clone https://github.com/datalab-to/chandra.git
    if errorlevel 1 (
        echo [WARNING] Clonazione Chandra fallita! (potrebbe non essere disponibile)
        goto :download_models
    )
    
    cd chandra
    if exist "requirements.txt" (
        echo Installazione dipendenze Chandra...
        python -m pip install -r requirements.txt
    )
    cd ..
    
    echo [OK] Chandra installato
)

:download_models
echo.
echo ================================================
echo    DOWNLOAD MODELLI DOLPHIN
echo ================================================
echo.

if exist "Dolphin" (
    echo Download modello Dolphin-1.5 da Hugging Face...
    echo.
    echo Opzione 1: Git LFS (consigliato)
    echo   git lfs install
    echo   git clone https://huggingface.co/ByteDance/Dolphin-1.5 ./hf_model
    echo.
    echo Opzione 2: Hugging Face CLI
    echo   huggingface-cli download ByteDance/Dolphin-1.5 --local-dir ./hf_model
    echo.
    echo Vuoi scaricare il modello ora? (S/N)
    set /p download_model=
    
    if /i "%download_model%"=="S" (
        REM Verifica huggingface-cli
        where huggingface-cli >nul 2>&1
        if %ERRORLEVEL% == 0 (
            echo Download modello con huggingface-cli...
            huggingface-cli download ByteDance/Dolphin-1.5 --local-dir ./hf_model
            if errorlevel 1 (
                echo [WARNING] Download modello fallito. Puoi farlo manualmente.
            ) else (
                echo [OK] Modello Dolphin scaricato!
            )
        ) else (
            echo [INFO] huggingface-cli non trovato.
            echo Installa con: pip install huggingface_hub
            echo Poi esegui: huggingface-cli download ByteDance/Dolphin-1.5 --local-dir ./hf_model
        )
    )
)

echo.
echo ================================================
echo    INSTALLAZIONE COMPLETATA
echo ================================================
echo.
echo OCR disponibili:
echo   - Tesseract (già installato)
if exist "Dolphin" (
    echo   - Dolphin OCR [INSTALLATO]
) else (
    echo   - Dolphin OCR [NON INSTALLATO]
)
if exist "chandra" (
    echo   - Chandra OCR [INSTALLATO]
) else (
    echo   - Chandra OCR [NON INSTALLATO]
)
echo.
echo Verifica disponibilità:
echo   python app\test_ocr.py
echo.
pause

