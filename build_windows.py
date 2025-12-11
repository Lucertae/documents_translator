#!/usr/bin/env python3
"""
Build script for LAC Translate Windows executable
Creates a single .exe file with PyInstaller
"""
import PyInstaller.__main__
import sys
from pathlib import Path

def build_exe():
    """Build Windows executable with PyInstaller."""
    
    # Project root
    root = Path(__file__).parent
    app_dir = root / "app"
    main_file = app_dir / "main_qt.py"
    
    # Build arguments for PyInstaller
    args = [
        str(main_file),                      # Entry point
        '--name=LacTranslate',               # Executable name
        '--onefile',                         # Single .exe file
        '--windowed',                        # No console window (GUI mode)
        '--noconfirm',                       # Overwrite without asking
        '--clean',                           # Clean cache
        
        # Icon (if you have one)
        # '--icon=assets/icon.ico',
        
        # Hidden imports (libraries not auto-detected)
        '--hidden-import=PySide6',
        '--hidden-import=PySide6.QtCore',
        '--hidden-import=PySide6.QtWidgets',
        '--hidden-import=PySide6.QtGui',
        '--hidden-import=transformers',
        '--hidden-import=torch',
        '--hidden-import=sentencepiece',
        '--hidden-import=paddleocr',
        '--hidden-import=paddlepaddle',
        '--hidden-import=fitz',  # PyMuPDF
        '--hidden-import=PIL',
        '--hidden-import=pdf2image',
        
        # Collect all submodules
        '--collect-all=transformers',
        '--collect-all=torch',
        '--collect-all=sentencepiece',
        '--collect-all=paddleocr',
        '--collect-all=paddlepaddle',
        '--collect-all=PySide6',
        
        # Copy data files
        f'--add-data={root / "logs"};logs',
        f'--add-data={root / "input"};input',
        f'--add-data={root / "output"};output',
        
        # Exclude unnecessary modules to reduce size
        '--exclude-module=matplotlib',
        '--exclude-module=scipy',
        '--exclude-module=pandas',
        '--exclude-module=notebook',
        '--exclude-module=IPython',
    ]
    
    print("=" * 60)
    print("Building LAC Translate for Windows...")
    print("=" * 60)
    print("\nThis will take several minutes...")
    print("Final .exe will be in: dist/LacTranslate.exe")
    print("\nNote: The .exe will be ~500MB-1GB due to ML models")
    print("=" * 60)
    
    # Run PyInstaller
    PyInstaller.__main__.run(args)
    
    print("\n" + "=" * 60)
    print("✓ Build complete!")
    print("=" * 60)
    print(f"\nExecutable: dist/LacTranslate.exe")
    print("\nTo distribute:")
    print("1. Copy dist/LacTranslate.exe to target PC")
    print("2. Models will download automatically on first run")
    print("   (OPUS-MT + PaddleOCR, ~1GB)")
    print("=" * 60)

if __name__ == "__main__":
    try:
        build_exe()
    except Exception as e:
        print(f"\n❌ Build failed: {e}", file=sys.stderr)
        sys.exit(1)
