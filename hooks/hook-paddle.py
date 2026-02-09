"""
PyInstaller hook for PaddlePaddle

Ensures all PaddlePaddle dynamic libraries and resources are collected.
Critical for Windows EXE builds.
"""
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules
import os
import sys

# Collect all PaddlePaddle submodules
hiddenimports = collect_submodules('paddle')

# Add specific modules that might be missed
hiddenimports += [
    'paddle.inference',
    'paddle.base',
    'paddle.base.core',
    'paddle.base.libpaddle',
    'paddle.fluid',
    'paddle.fluid.core',
    'paddle.framework',
    'paddle.utils',
    'paddle.device',
    'paddle.nn',
    'paddle.vision',
]

# Collect all data files (including .pyi stubs, configs)
datas = collect_data_files('paddle', include_py_files=True)

# Collect dynamic libraries (DLLs on Windows, .so on Linux)
binaries = collect_dynamic_libs('paddle')

# On Windows, try to find additional DLLs that might be in the paddle directory
try:
    import paddle
    paddle_dir = os.path.dirname(paddle.__file__)
    
    # Look for DLLs in paddle directory and subdirectories
    for root, dirs, files in os.walk(paddle_dir):
        for f in files:
            if f.endswith('.dll') or f.endswith('.pyd') or f.endswith('.so'):
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(root, os.path.dirname(paddle_dir))
                binaries.append((full_path, rel_path))
    
    # Look for libs directory specifically
    libs_dir = os.path.join(paddle_dir, 'libs')
    if os.path.exists(libs_dir):
        for f in os.listdir(libs_dir):
            if f.endswith('.dll') or f.endswith('.so'):
                binaries.append((os.path.join(libs_dir, f), 'paddle/libs'))
                
except Exception as e:
    print(f"Warning: Could not scan paddle directory for DLLs: {e}")
