# -*- mode: python ; coding: utf-8 -*-
"""
LAC Translate - PyInstaller Build Specification (Windows & Linux)

OCR Engine: GLM-OCR via Ollama (external server, not bundled)
Ollama must be installed separately on the target system.
"""

import sys
import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, collect_dynamic_libs

block_cipher = None

# Collect all necessary data files
datas = []

# PySide6 resources
datas += collect_data_files('PySide6', include_py_files=False)

# Transformers models (NLLB) - Note: models are downloaded at runtime
datas += collect_data_files('transformers', include_py_files=False)

# SentencePiece
datas += collect_data_files('sentencepiece', include_py_files=False)

# Ollama Python client
try:
    datas += collect_data_files('ollama', include_py_files=False)
except Exception as e:
    print(f"Warning: Could not collect ollama data files: {e}")

# Collect binaries/dynamic libraries
binaries = []

# Include app resources (with existence checks for CI compatibility)
app_resources = [
    ('logs/README.txt', 'logs'),
    ('output/README.txt', 'output'),
    ('assets/icon.png', 'assets'),
    ('assets/icon.ico', 'assets'),
    ('.env', '.'),  # Include .env for Sentry configuration
]
for src, dst in app_resources:
    if os.path.exists(src):
        datas.append((src, dst))

# Hidden imports for dynamic loading
hiddenimports = [
    # PySide6
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'PySide6.QtPrintSupport',
    
    # Transformers & ML
    'transformers',
    'transformers.models.nllb',
    'transformers.models.m2m_100',
    'sentencepiece',
    'sacremoses',
    'torch',
    'torch.nn',
    'torch.nn.functional',
    
    # PDF processing
    'fitz',
    'pymupdf',
    
    # Image processing
    'PIL',
    'PIL.Image',
    
    # Ollama client
    'ollama',
    
    # Numpy
    'numpy',
    
    # Requests (for model downloads & Ollama API)
    'requests',
    'urllib3',
    'httpx',
    
    # App modules
    'app.core',
    'app.core.pdf_processor',
    'app.core.translator',
    'app.core.glm_ocr',
    'app.ui',
    'app.ui.main_window',
    'app.ui.pdf_viewer',
]

# Collect all submodules for complex packages
hiddenimports += collect_submodules('transformers')
hiddenimports += collect_submodules('torch')
hiddenimports += collect_submodules('PySide6')

# Exclude unnecessary modules to reduce size
excludes = [
    'tkinter',
    'matplotlib',
    'IPython',
    'jupyter',
    'notebook',
    'pytest',
]

a = Analysis(
    ['app/main_qt.py'],
    pathex=['.'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Icona per Windows (se esiste)
import os
icon_path = 'assets/icon.ico' if os.path.exists('assets/icon.ico') else None

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='lac-translate',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Abilitato per vedere errori di avvio - cambiare a False per release
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,  # Icona Windows (.ico)
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='lac-translate',
)
