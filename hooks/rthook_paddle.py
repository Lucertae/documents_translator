"""
Runtime hook for PaddlePaddle on Windows

Sets up environment variables and paths needed for paddle to work
in a PyInstaller frozen environment.
"""
import os
import sys

# Set environment variables before paddle is imported
os.environ['PADDLE_HOME'] = os.path.join(os.path.dirname(sys.executable), 'paddle_models')
os.environ['PADDLEOCR_HOME'] = os.path.join(os.path.dirname(sys.executable), 'paddle_models')
os.environ['PADDLE_DOWNLOAD_TIMEOUT'] = '120'

# Disable MKLDNN verbose logging (causes issues on some systems)
os.environ['MKLDNN_VERBOSE'] = '0'
os.environ['FLAGS_use_mkldnn'] = '1'

# Disable model source check (we pre-download models)
os.environ['DISABLE_MODEL_SOURCE_CHECK'] = 'True'

# Set OpenMP threads to avoid oversubscription
os.environ['OMP_NUM_THREADS'] = '4'
os.environ['MKL_NUM_THREADS'] = '4'

# Add the application directory to PATH for DLL lookup on Windows
if sys.platform == 'win32':
    app_dir = os.path.dirname(sys.executable)
    paddle_libs = os.path.join(app_dir, 'paddle', 'libs')
    
    # Add directories to PATH
    current_path = os.environ.get('PATH', '')
    new_paths = [app_dir, paddle_libs]
    
    for p in new_paths:
        if os.path.exists(p) and p not in current_path:
            os.environ['PATH'] = p + os.pathsep + current_path
            current_path = os.environ['PATH']
    
    # Also need to set DLL search directory on Windows 10+
    try:
        import ctypes
        kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel32.SetDllDirectoryW(app_dir)
    except Exception:
        pass
