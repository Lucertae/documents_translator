# -*- mode: python ; coding: utf-8 -*-
"""
LAC Translate - PyInstaller Build Specification (Windows & Linux)

App: Professional PDF translation with OCR (RapidDoc + RapidOCR + NLLB-200)
Version: 1.0.0
"""

import sys
import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, collect_dynamic_libs

block_cipher = None

# Collect binaries/dynamic libraries (must be before openvino section)
binaries = []

# Collect all necessary data files
datas = []

# PySide6 resources + dynamic libraries (DLL/pyd)
datas += collect_data_files('PySide6', include_py_files=False)
binaries += collect_dynamic_libs('PySide6')

# Transformers models (NLLB) - Note: models are downloaded at runtime
datas += collect_data_files('transformers', include_py_files=False)

# SentencePiece
datas += collect_data_files('sentencepiece', include_py_files=False)

# RapidOCR models (PP-OCRv5 detection + recognition)
try:
    datas += collect_data_files('rapidocr', include_py_files=False)
except Exception as e:
    print(f"Warning: Could not collect rapidocr data files: {e}")

# RapidDoc models (PP-DocLayoutV2 layout + table recognition)
try:
    datas += collect_data_files('rapid_doc', include_py_files=False)
except Exception as e:
    print(f"Warning: Could not collect rapid_doc data files: {e}")

# OpenVINO runtime (used by RapidOCR)
try:
    datas += collect_data_files('openvino', include_py_files=True)
    binaries += collect_dynamic_libs('openvino')
except Exception as e:
    print(f"Warning: Could not collect openvino data files: {e}")

# Include app resources (with existence checks for CI compatibility)
app_resources = [
    ('logs/README.txt', 'logs'),
    ('output/README.txt', 'output'),
    ('assets/icon.png', 'assets'),
    ('assets/icon.ico', 'assets'),
    ('assets/lac-translate.desktop', 'assets'),
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
    
    # OCR engines
    'rapidocr',
    'rapid_doc',
    'openvino',
    'onnxruntime',
    
    # Numpy
    'numpy',
    
    # Requests (for model downloads)
    'requests',
    'urllib3',
    'httpx',
    
    # App modules
    'app.core',
    'app.core.pdf_processor',
    'app.core.translator',
    'app.core.rapid_ocr',
    'app.core.rapid_doc_engine',
    'app.core.ocr_utils',
    'app.core.format_utils',
    'app.core.formatting',
    'app.core.config',
    'app.core.sentry_integration',
    'app.ui',
    'app.ui.main_window',
    'app.ui.pdf_viewer',
]

# Collect all submodules for complex packages
hiddenimports += collect_submodules('transformers')
hiddenimports += collect_submodules('torch')
hiddenimports += collect_submodules('PySide6')
hiddenimports += collect_submodules('rapidocr')
hiddenimports += collect_submodules('rapid_doc')
hiddenimports += collect_submodules('openvino')

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
    console=False,  # GUI application — no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[
        # UPX corrompe le DLL di Qt6 — escluderle sempre
        'Qt6*.dll',
        'Qt6*.pyd',
        'pyside6*.dll',
        'pyside6*.pyd',
        'shiboken6*.dll',
        'shiboken6*.pyd',
        # Anche OpenVINO e ONNX Runtime possono avere problemi
        'openvino*.dll',
        'onnxruntime*.dll',
    ],
    name='lac-translate',
)
