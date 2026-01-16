#!/bin/bash
# ===========================================
# LAC Translate - Linux Build Script
# ===========================================

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "  LAC Translate - Linux Build"
echo "=========================================="
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Create it first with:"
    echo "   python3 -m venv .venv"
    echo "   source .venv/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Check PyInstaller
if ! command -v pyinstaller &> /dev/null; then
    echo "📦 Installing PyInstaller..."
    pip install pyinstaller
fi

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build/ dist/

# Run PyInstaller
echo ""
echo "🔨 Building application with PyInstaller..."
echo "   This may take several minutes..."
echo ""

pyinstaller lac_translate.spec --clean --noconfirm

# Check if build succeeded
if [ -d "dist/lac-translate" ]; then
    echo ""
    echo "=========================================="
    echo "✅ BUILD SUCCESSFUL!"
    echo "=========================================="
    echo ""
    echo "📁 Output location: dist/lac-translate/"
    echo ""
    echo "To run the application:"
    echo "   ./dist/lac-translate/lac-translate"
    echo ""
    
    # Show size
    SIZE=$(du -sh dist/lac-translate | cut -f1)
    echo "📊 Total size: $SIZE"
    echo ""
    
    # Create run script
    cat > dist/lac-translate/run.sh << 'EOF'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
./lac-translate "$@"
EOF
    chmod +x dist/lac-translate/run.sh
    chmod +x dist/lac-translate/lac-translate
    
    echo "💡 You can also create a desktop shortcut or add to PATH"
else
    echo ""
    echo "❌ BUILD FAILED!"
    echo "Check the output above for errors."
    exit 1
fi
