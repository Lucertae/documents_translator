"""
PyInstaller hook for PaddleOCR

Ensures all PaddleOCR resources and models are collected.
"""
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules

# Collect all PaddleOCR submodules
hiddenimports = collect_submodules('paddleocr')

# Add specific modules
hiddenimports += [
    'paddleocr.paddleocr',
    'paddleocr.tools',
    'paddleocr.ppocr',
    'paddleocr.ppstructure',
]

# Collect all data files (configs, fonts, etc.)
datas = collect_data_files('paddleocr', include_py_files=True)

# Collect dynamic libraries
binaries = collect_dynamic_libs('paddleocr')
