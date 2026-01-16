# -*- mode: python ; coding: utf-8 -*-
"""
LAC Translate - PyInstaller Build Specification for Linux
"""

import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all necessary data files
datas = []

# PySide6 resources
datas += collect_data_files('PySide6', include_py_files=False)

# Transformers models (NLLB) - Note: models are downloaded at runtime
datas += collect_data_files('transformers', include_py_files=False)

# SentencePiece
datas += collect_data_files('sentencepiece', include_py_files=False)

# PaddleOCR resources
try:
    datas += collect_data_files('paddleocr', include_py_files=False)
except Exception:
    pass

# PaddleX resources (required by PaddleOCR)
try:
    datas += collect_data_files('paddlex', include_py_files=False)
except Exception:
    pass

# Include app resources
datas += [
    ('app/deep_translator', 'app/deep_translator'),
    ('logs/README.txt', 'logs'),
    ('output/README.txt', 'output'),
    ('assets/icon.png', 'assets'),
]

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
    'pdf2image',
    
    # PaddleOCR
    'paddleocr',
    'paddle',
    
    # App modules
    'app.core',
    'app.core.pdf_processor',
    'app.core.translator',
    'app.ui',
    'app.ui.main_window',
    'app.ui.pdf_viewer',
    'app.deep_translator',
]

# Collect all submodules for complex packages
hiddenimports += collect_submodules('transformers')
hiddenimports += collect_submodules('torch')
hiddenimports += collect_submodules('PySide6')

# Exclude unnecessary modules to reduce size
excludes = [
    'tkinter',
    'matplotlib',
    'numpy.testing',
    'scipy',
    'IPython',
    'jupyter',
    'notebook',
    'pytest',
]

a = Analysis(
    ['app/main_qt.py'],
    pathex=['.'],
    binaries=[],
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
    console=False,  # GUI application, no console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
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
