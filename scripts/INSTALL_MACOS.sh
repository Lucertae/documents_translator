#!/bin/bash
# LAC TRANSLATE - Installer Script per macOS

echo "======================================"
echo "  LAC TRANSLATE - Installazione macOS"
echo "======================================"
echo ""

# Verifica Python
if ! command -v python3 &> /dev/null; then
    echo "✗ Python 3 non trovato"
    echo "Installa Python 3.8+ da: https://www.python.org/downloads/"
    exit 1
fi

echo "✓ Python installato: $(python3 --version)"

# Verifica pip
if ! command -v pip3 &> /dev/null; then
    echo "✗ pip3 non trovato"
    echo "Installa pip: python3 -m ensurepip --upgrade"
    exit 1
fi

echo "✓ pip installato"

# Installa dipendenze
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
echo "Oppure usa il file .app se compilato:"
echo "  open LAC_Translate.app"
echo ""

