#!/usr/bin/env python3
"""
LAC TRANSLATE - Multi-Platform Build Script
Crea eseguibili per Windows, macOS e Linux
"""
import os
import sys
import shutil
import subprocess
import json
import re
import platform
from pathlib import Path
from datetime import datetime

# Colors for console output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

def print_step(step_num, total, text):
    print(f"{Colors.OKCYAN}[{step_num}/{total}] {text}{Colors.ENDC}")

def print_success(text):
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")

# Paths
BASE_DIR = Path(__file__).parent
BUILD_DIR = BASE_DIR / "build"
DIST_DIR = BASE_DIR / "dist"
RELEASE_DIR = BASE_DIR / "release"

# Detect platform
CURRENT_PLATFORM = platform.system().lower()
PLATFORMS = {
    'windows': 'win',
    'darwin': 'mac',
    'linux': 'linux'
}
PLATFORM_NAME = PLATFORMS.get(CURRENT_PLATFORM, 'unknown')

def detect_platform():
    """Rileva piattaforma corrente"""
    system = platform.system().lower()
    if system == 'windows':
        return 'win', '.exe'
    elif system == 'darwin':
        return 'mac', ''
    elif system == 'linux':
        return 'linux', ''
    else:
        return 'unknown', ''

def clean_build():
    """Pulisci directory build precedenti"""
    print_step(1, 8, "Pulizia build precedenti...")
    
    dirs_to_clean = [BUILD_DIR, DIST_DIR]
    for dir_path in dirs_to_clean:
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print_success(f"Rimosso {dir_path}")

def check_dependencies():
    """Verifica dipendenze necessarie"""
    print_step(2, 8, "Verifica dipendenze...")
    
    required = ['PyInstaller']
    missing = []
    
    for module in required:
        try:
            __import__(module.lower())
            print_success(f"{module} installato")
        except ImportError:
            missing.append(module)
            print_error(f"{module} mancante - installa con: pip install {module.lower()}")
    
    if missing:
        return False
    
    return True

def create_spec_file(platform_type):
    """Crea file .spec per piattaforma specifica"""
    print_step(3, 8, f"Creazione spec file per {platform_type}...")
    
    icon_line = "('logo_alt.ico', '.')," if platform_type == 'win' else ""
    icon_param = "icon='logo_alt.ico'," if platform_type == 'win' else "icon=None,"
    bundle_section = '''
app = BUNDLE(exe,
    name='LAC_Translate.app',
    icon='logo_alt.icns',
    bundle_identifier='com.lactranslate.app',
)
''' if platform_type == 'mac' else ""
    
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file per LAC TRANSLATE - {platform_type.upper()}
"""

block_cipher = None

a = Analysis(
    ['app/pdf_translator_gui.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('app/deep_translator', 'deep_translator'),
        {icon_line}
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
        'license_manager',
        'license_activation',
        'settings_manager',
        'settings_dialog',
    ],
    hookspath=[],
    hooksconfig={{}},
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
    noarchive=False,
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
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    {icon_param}
)
{bundle_section}
'''
    
    spec_file = BASE_DIR / f"lac_translate_{platform_type}.spec"
    with open(spec_file, 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print_success(f"Spec file creato: {spec_file}")
    return spec_file

def build_exe(platform_type):
    """Compila eseguibile per piattaforma"""
    print_step(4, 8, f"Compilazione eseguibile per {platform_type}...")
    
    spec_file = BASE_DIR / f"lac_translate_{platform_type}.spec"
    if not spec_file.exists():
        spec_file = create_spec_file(platform_type)
    
    try:
        cmd = [sys.executable, "-m", "PyInstaller", "--clean", str(spec_file)]
        result = subprocess.run(cmd, cwd=BASE_DIR, capture_output=True, text=True)
        
        if result.returncode == 0:
            print_success("Compilazione completata")
            
            # Verifica eseguibile creato
            if platform_type == 'win':
                exe_path = DIST_DIR / "LAC_Translate.exe"
            elif platform_type == 'mac':
                exe_path = DIST_DIR / "LAC_Translate.app"
            else:  # linux
                exe_path = DIST_DIR / "LAC_Translate"
            
            if exe_path.exists():
                if exe_path.is_file():
                    size_mb = exe_path.stat().st_size / (1024 * 1024)
                else:  # .app bundle
                    size_mb = sum(f.stat().st_size for f in exe_path.rglob('*') if f.is_file()) / (1024 * 1024)
                print_success(f"Eseguibile creato: {exe_path} ({size_mb:.1f} MB)")
                return True, exe_path
            else:
                print_error("Eseguibile non trovato dopo compilazione")
                return False, None
        else:
            print_error("Errore durante compilazione:")
            print(result.stderr)
            return False, None
            
    except Exception as e:
        print_error(f"Errore compilazione: {e}")
        return False, None

def create_installer_linux():
    """Crea installer Linux (.deb)"""
    print_step(5, 8, "Creazione installer Linux...")
    
    # Verifica dpkg-deb disponibile
    try:
        subprocess.run(['which', 'dpkg-deb'], capture_output=True, check=True)
    except:
        print_warning("dpkg-deb non trovato - saltato creazione .deb")
        return False
    
    # Crea struttura .deb
    deb_dir = RELEASE_DIR / "lac_translate_deb"
    deb_root = deb_dir / "DEBIAN"
    deb_app = deb_dir / "usr" / "local" / "bin"
    deb_desktop = deb_dir / "usr" / "share" / "applications"
    
    for d in [deb_root, deb_app, deb_desktop]:
        d.mkdir(parents=True, exist_ok=True)
    
    # Copy executable
    exe_src = DIST_DIR / "LAC_Translate"
    if exe_src.exists():
        shutil.copy2(exe_src, deb_app / "lac-translate")
        os.chmod(deb_app / "lac-translate", 0o755)
    
    # Create control file
    control_content = f"""Package: lac-translate
Version: 2.0.0
Section: utils
Priority: optional
Architecture: amd64
Depends: python3, python3-tk
Maintainer: LAC Software <info@lucertae.com>
Description: LAC TRANSLATE - Professional PDF Translator
 Professional PDF translation tool with OCR support.
 Translates PDF documents while preserving layout.
"""
    with open(deb_root / "control", 'w') as f:
        f.write(control_content)
    
    # Create desktop file
    desktop_content = """[Desktop Entry]
Version=1.0
Type=Application
Name=LAC TRANSLATE
Comment=Professional PDF Translator
Exec=lac-translate
Icon=lac-translate
Terminal=false
Categories=Utility;Office;
"""
    with open(deb_desktop / "lac-translate.desktop", 'w') as f:
        f.write(desktop_content)
    
    # Build .deb
    try:
        cmd = ['dpkg-deb', '--build', str(deb_dir), str(RELEASE_DIR / 'lac-translate_2.0.0_amd64.deb')]
        subprocess.run(cmd, check=True)
        print_success("Installer .deb creato")
        return True
    except Exception as e:
        print_warning(f"Errore creazione .deb: {e}")
        return False

def create_installer_mac():
    """Crea installer macOS (.dmg)"""
    print_step(5, 8, "Creazione installer macOS...")
    
    # Verifica hdiutil disponibile
    if CURRENT_PLATFORM != 'darwin':
        print_warning("Creazione .dmg richiede macOS - saltato")
        return False
    
    try:
        app_path = DIST_DIR / "LAC_Translate.app"
        if not app_path.exists():
            print_error("App bundle non trovato")
            return False
        
        # Create DMG
        dmg_path = RELEASE_DIR / "LAC_Translate_v2.0.0_macOS.dmg"
        
        # Create temporary directory for DMG contents
        dmg_temp = RELEASE_DIR / "dmg_temp"
        if dmg_temp.exists():
            shutil.rmtree(dmg_temp)
        dmg_temp.mkdir()
        
        # Copy app to temp
        shutil.copytree(app_path, dmg_temp / "LAC_Translate.app")
        
        # Create Applications symlink
        os.symlink("/Applications", dmg_temp / "Applications")
        
        # Create DMG
        cmd = [
            'hdiutil', 'create',
            '-volname', 'LAC TRANSLATE',
            '-srcfolder', str(dmg_temp),
            '-ov',
            '-format', 'UDZO',
            str(dmg_path)
        ]
        subprocess.run(cmd, check=True)
        
        # Cleanup
        shutil.rmtree(dmg_temp)
        
        print_success(f"Installer .dmg creato: {dmg_path}")
        return True
    except Exception as e:
        print_warning(f"Errore creazione .dmg: {e}")
        return False

def create_installer_win():
    """Crea installer Windows con InnoSetup"""
    from build import build_installer
    return build_installer()

def create_installer(platform_type):
    """Crea installer per piattaforma specifica"""
    if platform_type == 'win':
        return create_installer_win()
    elif platform_type == 'mac':
        return create_installer_mac()
    elif platform_type == 'linux':
        return create_installer_linux()
    return False

def create_release_package(platform_type, exe_path):
    """Crea package distribuzione finale"""
    print_step(6, 8, "Creazione package distribuzione...")
    
    RELEASE_DIR.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    version = "2.0.0"
    package_name = f"LAC_Translate_v{version}_{platform_type}_{timestamp}"
    package_dir = RELEASE_DIR / package_name
    package_dir.mkdir(exist_ok=True)
    
    # Copy executable
    if exe_path and exe_path.exists():
        if exe_path.is_file():
            shutil.copy2(exe_path, package_dir / exe_path.name)
        else:  # .app bundle
            shutil.copytree(exe_path, package_dir / exe_path.name)
        print_success(f"Copiato eseguibile in {package_name}")
    
    # Copy documentation
    docs_to_copy = [
        ('README.md', 'README.md'),
        ('LICENSE.txt', 'LICENSE.txt'),
        ('CHANGELOG.md', 'CHANGELOG.txt'),
        ('docs/README_DISTRIBUZIONE.md', 'README_INSTALLAZIONE.md'),
        ('guides/QUICK_START.txt', 'QUICK_START.txt'),
    ]
    
    for src_name, dst_name in docs_to_copy:
        src = BASE_DIR / src_name
        if src.exists():
            dst = package_dir / dst_name
            if src.is_dir():
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)
    
    # Create platform-specific README
    readme_platform = package_dir / "INSTALLAZIONE.txt"
    readme_content = f"""LAC TRANSLATE v{version} - {platform_type.upper()}
{'='*50}

INSTALLAZIONE:

"""
    
    if platform_type == 'win':
        readme_content += """1. Esegui LAC_Translate_v2.0_Setup.exe
2. Segui le istruzioni del wizard di installazione
3. All'avvio, inserisci la chiave seriale fornita
"""
    elif platform_type == 'mac':
        readme_content += """1. Apri il file .dmg
2. Trascina LAC_Translate.app nella cartella Applications
3. Esegui l'applicazione
4. All'avvio, inserisci la chiave seriale fornita
"""
    else:  # linux
        readme_content += """1. Installa il pacchetto .deb:
   sudo dpkg -i lac-translate_2.0.0_amd64.deb
   
   Se ci sono dipendenze mancanti:
   sudo apt-get install -f

2. Oppure esegui direttamente l'eseguibile:
   ./LAC_Translate

3. All'avvio, inserisci la chiave seriale fornita
"""
    
    readme_content += f"""
REQUISITI:
- {platform_type.upper()}: Compatibile con versioni moderne
- 4GB RAM minimo
- 2GB spazio disco libero

NOTA: Per funzionalità OCR, installa Tesseract separatamente.

Supporto: info@lucertae.com
"""
    
    with open(readme_platform, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print_success(f"Package creato: {package_dir}")
    
    # Create ZIP
    zip_name = f"{package_name}.zip"
    zip_path = RELEASE_DIR / zip_name
    shutil.make_archive(str(zip_path).replace('.zip', ''), 'zip', package_dir)
    print_success(f"ZIP creato: {zip_path}")

def update_version():
    """Aggiorna version file e build number"""
    version_file = BASE_DIR / "app" / "version.py"
    version_json = BASE_DIR / "VERSION.json"
    
    try:
        if version_json.exists():
            with open(version_json, 'r') as f:
                version_data = json.load(f)
                current_build = version_data.get('build_number', 0)
        else:
            current_build = 0
    except:
        current_build = 0
    
    new_build = current_build + 1
    
    if version_file.exists():
        with open(version_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        content = re.sub(
            r'BUILD_NUMBER = \d+',
            f'BUILD_NUMBER = {new_build}',
            content
        )
        
        with open(version_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print_success(f"Build number aggiornato: {new_build}")
    
    from app.version import save_version
    save_version()
    
    return new_build

def print_summary(platform_type, exe_path):
    """Stampa riepilogo build"""
    print_step(8, 8, "Riepilogo build")
    print_header("BUILD COMPLETATO")
    
    print(f"\n{Colors.OKGREEN}Piattaforma: {platform_type.upper()}{Colors.ENDC}")
    
    if exe_path and exe_path.exists():
        if exe_path.is_file():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"{Colors.OKGREEN}Eseguibile: {exe_path} ({size_mb:.1f} MB){Colors.ENDC}")
        else:
            size_mb = sum(f.stat().st_size for f in exe_path.rglob('*') if f.is_file()) / (1024 * 1024)
            print(f"{Colors.OKGREEN}App Bundle: {exe_path} ({size_mb:.1f} MB){Colors.ENDC}")
    
    # Check installer
    if RELEASE_DIR.exists():
        installers = list(RELEASE_DIR.glob("*installer*")) + list(RELEASE_DIR.glob("*.dmg")) + list(RELEASE_DIR.glob("*.deb"))
        if installers:
            print(f"\n{Colors.OKGREEN}Installer:{Colors.ENDC}")
            for installer in installers:
                if installer.is_file():
                    size_mb = installer.stat().st_size / (1024 * 1024)
                    print(f"  - {installer.name} ({size_mb:.1f} MB)")
        
        packages = list(RELEASE_DIR.glob("LAC_Translate_*"))
        if packages:
            print(f"\n{Colors.OKGREEN}Package distribuzione:{Colors.ENDC}")
            for pkg in packages:
                if pkg.is_dir():
                    print(f"  - {pkg.name}")
                elif pkg.suffix == '.zip':
                    size_mb = pkg.stat().st_size / (1024 * 1024)
                    print(f"  - {pkg.name} ({size_mb:.1f} MB)")

def main():
    """Main build function"""
    print_header("LAC TRANSLATE - Multi-Platform Build")
    
    platform_type, ext = detect_platform()
    print(f"Piattaforma rilevata: {platform_type.upper()}")
    print(f"Directory base: {BASE_DIR}")
    print(f"Python: {sys.executable}")
    print(f"Versione Python: {sys.version}")
    
    # Update version
    build_num = update_version()
    print()
    
    # Build steps
    clean_build()
    
    if not check_dependencies():
        print_error("Build fallito: dipendenze mancanti")
        return 1
    
    success, exe_path = build_exe(platform_type)
    if not success:
        print_error("Build fallito: errore compilazione")
        return 1
    
    # Create installer
    create_installer(platform_type)
    
    # Create release package
    create_release_package(platform_type, exe_path)
    
    print_summary(platform_type, exe_path)
    
    print(f"\n{Colors.OKGREEN}{Colors.BOLD}✓ Build completato con successo!{Colors.ENDC}")
    print(f"{Colors.OKGREEN}Piattaforma: {platform_type.upper()}{Colors.ENDC}")
    print(f"{Colors.OKGREEN}Build Number: {build_num}{Colors.ENDC}\n")
    return 0

if __name__ == "__main__":
    sys.exit(main())

