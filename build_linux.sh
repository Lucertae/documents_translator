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
    EXEC_SIZE=$(du -sh dist/lac-translate/lac-translate | cut -f1)
    echo "📊 Total size: $SIZE (executable: $EXEC_SIZE)"
    echo ""
    
    # Ensure executable permissions
    chmod +x dist/lac-translate/lac-translate
    
    # Create run script
    cat > dist/lac-translate/run.sh << 'EOF'
#!/bin/bash
# LAC Translate - Professional PDF Translation
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
exec ./lac-translate "$@"
EOF
    chmod +x dist/lac-translate/run.sh
    
    # Generate .desktop entry with correct absolute path
    INSTALL_DIR="$(cd dist/lac-translate && pwd)"
    cat > dist/lac-translate/lac-translate.desktop << DEOF
[Desktop Entry]
Name=LAC Translate
GenericName=PDF Translator
Comment=Professional PDF translation with OCR support
Exec=${INSTALL_DIR}/lac-translate
Path=${INSTALL_DIR}
Icon=${INSTALL_DIR}/_internal/assets/icon.png
Terminal=false
Type=Application
Categories=Office;Translation;
StartupNotify=true
StartupWMClass=lac-translate
DEOF
    chmod +x dist/lac-translate/lac-translate.desktop
    
    # Create install helper
    cat > dist/lac-translate/install-desktop.sh << 'IEOF'
#!/bin/bash
# Install desktop shortcut for LAC Translate
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DESKTOP_DIR="${HOME}/.local/share/applications"
mkdir -p "$DESKTOP_DIR"
# Update paths in desktop file
sed "s|Exec=.*|Exec=${SCRIPT_DIR}/lac-translate|; s|Path=.*|Path=${SCRIPT_DIR}|; s|Icon=.*|Icon=${SCRIPT_DIR}/_internal/assets/icon.png|" \
    "${SCRIPT_DIR}/lac-translate.desktop" > "${DESKTOP_DIR}/lac-translate.desktop"
chmod +x "${DESKTOP_DIR}/lac-translate.desktop"
echo "✅ Desktop shortcut installed to ${DESKTOP_DIR}/lac-translate.desktop"
echo "   You may need to log out and back in for it to appear in your menu."
IEOF
    chmod +x dist/lac-translate/install-desktop.sh
    
    echo "💡 To install as a desktop app, run:"
    echo "   ./dist/lac-translate/install-desktop.sh"
else
    echo ""
    echo "❌ BUILD FAILED!"
    echo "Check the output above for errors."
    exit 1
fi
