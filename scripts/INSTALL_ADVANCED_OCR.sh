#!/bin/bash
# Installazione OCR Avanzati - Dolphin e Chandra
# Per macOS e Linux

set -e

echo "================================================"
echo "   INSTALLAZIONE OCR AVANZATI"
echo "   Dolphin OCR e Chandra OCR"
echo "================================================"
echo

cd "$(dirname "$0")/.."

# Verifica Git
if ! command -v git &> /dev/null; then
    echo "[ERRORE] Git non trovato!"
    echo "Installa Git: sudo apt install git  # Debian/Ubuntu"
    echo "            brew install git        # macOS"
    exit 1
fi

# Verifica Python
if ! command -v python3 &> /dev/null; then
    echo "[ERRORE] Python3 non trovato!"
    exit 1
fi

echo "[1/4] Verifica Python..."
python3 --version
echo "[OK] Python trovato"
echo

# Installa dipendenze base
echo "[2/4] Installazione dipendenze base..."
python3 -m pip install --upgrade pip
python3 -m pip install torch torchvision transformers huggingface_hub
echo "[OK] Dipendenze installate"
echo

# Dolphin OCR
echo "[3/4] Installazione Dolphin OCR..."
if [ -d "Dolphin" ]; then
    echo "Dolphin già presente. Vuoi aggiornare? (s/n)"
    read -r update_dolphin
    if [ "$update_dolphin" = "s" ] || [ "$update_dolphin" = "S" ]; then
        cd Dolphin
        git pull
        cd ..
    else
        echo "Salto installazione Dolphin (già presente)"
    fi
else
    echo "Clonazione repository Dolphin..."
    git clone https://github.com/bytedance/Dolphin.git
    if [ $? -eq 0 ]; then
        cd Dolphin
        if [ -f "requirements.txt" ]; then
            echo "Installazione dipendenze Dolphin..."
            python3 -m pip install -r requirements.txt
        fi
        cd ..
        echo "[OK] Dolphin installato"
    else
        echo "[ERRORE] Clonazione Dolphin fallita!"
    fi
fi

echo
# Chandra OCR
echo "[4/4] Installazione Chandra OCR..."
if [ -d "chandra" ]; then
    echo "Chandra già presente. Vuoi aggiornare? (s/n)"
    read -r update_chandra
    if [ "$update_chandra" = "s" ] || [ "$update_chandra" = "S" ]; then
        cd chandra
        git pull
        cd ..
    else
        echo "Salto installazione Chandra (già presente)"
    fi
else
    echo "Clonazione repository Chandra..."
    git clone https://github.com/datalab-to/chandra.git
    if [ $? -eq 0 ]; then
        cd chandra
        if [ -f "requirements.txt" ]; then
            echo "Installazione dipendenze Chandra..."
            python3 -m pip install -r requirements.txt
        fi
        cd ..
        echo "[OK] Chandra installato"
    else
        echo "[WARNING] Clonazione Chandra fallita! (potrebbe non essere disponibile)"
    fi
fi

echo
echo "================================================"
echo "   DOWNLOAD MODELLI DOLPHIN"
echo "================================================"
echo

if [ -d "Dolphin" ]; then
    echo "Vuoi scaricare il modello Dolphin-1.5? (s/n)"
    read -r download_model
    
    if [ "$download_model" = "s" ] || [ "$download_model" = "S" ]; then
        if command -v huggingface-cli &> /dev/null; then
            echo "Download modello con huggingface-cli..."
            huggingface-cli download ByteDance/Dolphin-1.5 --local-dir ./hf_model
            if [ $? -eq 0 ]; then
                echo "[OK] Modello Dolphin scaricato!"
            else
                echo "[WARNING] Download modello fallito"
            fi
        else
            echo "[INFO] huggingface-cli non trovato"
            echo "Installa con: pip install huggingface_hub"
            echo "Poi esegui: huggingface-cli download ByteDance/Dolphin-1.5 --local-dir ./hf_model"
        fi
    fi
fi

echo
echo "================================================"
echo "   INSTALLAZIONE COMPLETATA"
echo "================================================"
echo
echo "OCR disponibili:"
echo "  - Tesseract (già installato)"
if [ -d "Dolphin" ]; then
    echo "  - Dolphin OCR [INSTALLATO]"
else
    echo "  - Dolphin OCR [NON INSTALLATO]"
fi
if [ -d "chandra" ]; then
    echo "  - Chandra OCR [INSTALLATO]"
else
    echo "  - Chandra OCR [NON INSTALLATO]"
fi
echo
echo "Verifica disponibilità:"
echo "  python3 app/test_ocr.py"
echo
   
