#!/bin/bash
# LAC TRANSLATE - Installer Script per Linux

echo "======================================"
echo "  LAC TRANSLATE - Installazione Linux"
echo "======================================"
echo ""

# Detect package manager
if command -v apt-get &> /dev/null; then
    PKG_MANAGER="apt-get"
    PKG_INSTALL="sudo apt-get install -y"
elif command -v yum &> /dev/null; then
    PKG_MANAGER="yum"
    PKG_INSTALL="sudo yum install -y"
elif command -v dnf &> /dev/null; then
    PKG_MANAGER="dnf"
    PKG_INSTALL="sudo dnf install -y"
else
    echo "⚠ Package manager non riconosciuto - installazione manuale richiesta"
fi

# Verifica Python
if ! command -v python3 &> /dev/null; then
    echo "✗ Python 3 non trovato"
    if [ ! -z "$PKG_INSTALL" ]; then
        echo "Installazione Python 3..."
        $PKG_INSTALL python3 python3-pip python3-tk
    else
        echo "Installa Python 3.8+ manualmente"
        exit 1
    fi
fi

echo "✓ Python installato: $(python3 --version)"

# Verifica pip
if ! command -v pip3 &> /dev/null; then
    echo "✗ pip3 non trovato"
    if [ ! -z "$PKG_INSTALL" ]; then
        $PKG_INSTALL python3-pip
    else
        echo "Installa pip3 manualmente"
        exit 1
    fi
fi

echo "✓ pip installato"

# Installa Tesseract OCR (opzionale ma consigliato)
echo ""
echo "Installazione Tesseract OCR (opzionale)..."
if [ ! -z "$PKG_INSTALL" ]; then
    if command -v tesseract &> /dev/null; then
        echo "✓ Tesseract già installato"
    else
        echo "Installazione Tesseract..."
        $PKG_INSTALL tesseract-ocr
    fi
else
    echo "⚠ Installa Tesseract manualmente se necessario"
fi

# Installa dipendenze Python
echo ""
echo "Installazione dipendenze Python..."
pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "✗ Errore installazione dipendenze"
    exit 1
fi

echo "✓ Dipendenze installate"

# Installa modelli Argos
echo ""
echo "Installazione modelli Argos Translate..."
cd app
python3 setup_argos_models.py

if [ $? -ne 0 ]; then
    echo "⚠ Errore installazione modelli Argos (opzionale)"
fi

cd ..

echo ""
echo "======================================"
echo "  INSTALLAZIONE COMPLETATA!"
echo "======================================"
echo ""
echo "Per avviare LAC TRANSLATE:"
echo "  python3 app/pdf_translator_gui.py"
echo ""
echo "Oppure usa l'eseguibile se compilato:"
echo "  ./LAC_Translate"
echo ""

