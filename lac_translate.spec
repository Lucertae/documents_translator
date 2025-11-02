# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file per LAC TRANSLATE
Crea eseguibile standalone Windows
"""

block_cipher = None

a = Analysis(
    ['app/pdf_translator_gui.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('app/deep_translator', 'deep_translator'),  # Include deep_translator module
        ('app/ocr_manager.py', 'app'),  # Include OCR manager
        ('security', 'security'),  # Include security module
        ('resources/icons/logo_alt.ico', '.'),  # Include icon
    ],
    hiddenimports=[
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.scrolledtext',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'pymupdf',
        'fitz',
        'argostranslate',
        'argostranslate.package',
        'argostranslate.translate',
        'deep_translator',
        'deep_translator.GoogleTranslator',
        'ocr_manager',
        'security',
        'security.security_manager',
        'cryptography',
        'cryptography.fernet',
        'license_manager',
        'license_activation',
        'settings_manager',
        'settings_dialog',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'IPython',
        'jupyter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,  # Crea archivio - codice più difficile da estrarre
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='LAC_Translate',
    debug=False,  # NO DEBUG - nasconde informazioni codice sorgente
    bootloader_ignore_signals=False,
    strip=True,  # Rimuove simboli debug
    upx=True,  # Compressione per nascondere codice
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window (GUI only) - nasconde output debug
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/icons/logo_alt.ico',  # Application icon
)

