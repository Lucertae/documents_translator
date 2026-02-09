"""
PyInstaller hook for PaddleX

PaddleX is required by PaddleOCR v3+ for pipeline management.
"""
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules

# Collect all PaddleX submodules
hiddenimports = collect_submodules('paddlex')

# Add specific modules that are dynamically loaded
hiddenimports += [
    'paddlex.inference',
    'paddlex.inference.pipelines',
    'paddlex.inference.models',
    'paddlex.inference.models.base',
    'paddlex.modules',
    'paddlex.modules.base',
    'paddlex.repo_manager',
    'paddlex.utils',
]

# Collect all data files (pipeline configs, etc.)
datas = collect_data_files('paddlex', include_py_files=True)

# Collect dynamic libraries
binaries = collect_dynamic_libs('paddlex')
