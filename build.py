#!/usr/bin/env python3
"""
LAC TRANSLATE - Build Script
Script automatico per build e packaging distribuzione
"""
import os
import sys
import shutil
import subprocess
import json
import re
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

def clean_build():
    """Pulisce directory build precedenti"""
    print_step(1, 6, "Pulizia build precedenti...")
    
    dirs_to_clean = [BUILD_DIR, DIST_DIR]
    for dir_path in dirs_to_clean:
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print_success(f"Rimosso {dir_path}")
    
    # Mantieni release ma pulisci
    if RELEASE_DIR.exists():
        for item in RELEASE_DIR.iterdir():
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)

def check_dependencies():
    """Verifica dipendenze necessarie"""
    print_step(2, 6, "Verifica dipendenze...")
    
    required = {
        'PyInstaller': 'pyinstaller',
        'Python': 'python'
    }
    
    missing = []
    for name, module in required.items():
        try:
            if module == 'python':
                result = subprocess.run([module, '--version'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    print_success(f"{name} installato")
                else:
                    missing.append(name)
            else:
                __import__(module)
                print_success(f"{name} installato")
        except ImportError:
            missing.append(name)
            print_error(f"{name} mancante - installa con: pip install {module}")
        except Exception as e:
            print_warning(f"Errore verifica {name}: {e}")
    
    if missing:
        print_error(f"Dipendenze mancanti: {', '.join(missing)}")
        return False
    
    return True

def build_exe():
    """Compila eseguibile con PyInstaller"""
    print_step(3, 6, "Compilazione eseguibile...")
    
    spec_file = BASE_DIR / "lac_translate.spec"
    if not spec_file.exists():
        print_error(f"File spec non trovato: {spec_file}")
        return False
    
    try:
        cmd = [sys.executable, "-m", "PyInstaller", "--clean", str(spec_file)]
        result = subprocess.run(cmd, cwd=BASE_DIR, capture_output=True, text=True)
        
        if result.returncode == 0:
            print_success("Compilazione completata")
            
            # Verifica eseguibile creato
            exe_path = DIST_DIR / "LAC_Translate.exe"
            if exe_path.exists():
                size_mb = exe_path.stat().st_size / (1024 * 1024)
                print_success(f"Eseguibile creato: {exe_path} ({size_mb:.1f} MB)")
                return True
            else:
                print_error("Eseguibile non trovato dopo compilazione")
                return False
        else:
            print_error("Errore durante compilazione:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print_error(f"Errore compilazione: {e}")
        return False

def copy_additional_files():
    """Copia file aggiuntivi necessari"""
    print_step(4, 6, "Copia file aggiuntivi...")
    
    # File da copiare nella distribuzione
    files_to_copy = [
        'README.md',
        'requirements.txt',
    ]
    
    dirs_to_copy = [
        ('docs', 'docs'),
    ]
    
    # Copia file
    for file_name in files_to_copy:
        src = BASE_DIR / file_name
        if src.exists():
            dst = DIST_DIR / file_name
            shutil.copy2(src, dst)
            print_success(f"Copiato {file_name}")
        else:
            print_warning(f"File non trovato: {file_name}")
    
    # Copia directory
    for src_dir, dst_dir in dirs_to_copy:
        src = BASE_DIR / src_dir
        if src.exists():
            dst = DIST_DIR / dst_dir
            shutil.copytree(src, dst, dirs_exist_ok=True)
            print_success(f"Copiata directory {src_dir}")

def create_release_package():
    """Crea package distribuzione finale"""
    print_step(5, 6, "Creazione package distribuzione...")
    
    RELEASE_DIR.mkdir(exist_ok=True)
    
    # Crea versione con timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    version = "2.0"
    package_name = f"LAC_Translate_v{version}_{timestamp}"
    package_dir = RELEASE_DIR / package_name
    package_dir.mkdir(exist_ok=True)
    
    # Copia eseguibile
    exe_src = DIST_DIR / "LAC_Translate.exe"
    if exe_src.exists():
        exe_dst = package_dir / "LAC_Translate.exe"
        shutil.copy2(exe_src, exe_dst)
        print_success(f"Copiato eseguibile in {package_name}")
    
    # Copia file necessari
    additional_files = [
        ('README.md', 'README.md'),
        ('requirements.txt', 'REQUIREMENTS.txt'),
    ]
    
    for src_name, dst_name in additional_files:
        src = BASE_DIR / src_name
        if src.exists():
            dst = package_dir / dst_name
            shutil.copy2(src, dst)
    
    # Crea README installazione
    readme_content = f"""LAC TRANSLATE v{version}
=============================

INSTALLAZIONE:
1. Esegui LAC_Translate.exe
2. All'avvio, inserisci la chiave seriale fornita
3. Il software è pronto all'uso

REQUISITI:
- Windows 10/11
- 4GB RAM minimo
- 2GB spazio disco libero

NOTA: Per funzionalità OCR, installa Tesseract separatamente.

Supporto: info@lucertae.com
"""
    
    readme_file = package_dir / "INSTALLAZIONE.txt"
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print_success(f"Package creato: {package_dir}")
    
    # Crea ZIP (opzionale)
    zip_name = f"{package_name}.zip"
    zip_path = RELEASE_DIR / zip_name
    shutil.make_archive(str(zip_path).replace('.zip', ''), 'zip', package_dir)
    print_success(f"ZIP creato: {zip_path}")

def build_installer():
    """Crea installer Windows con InnoSetup"""
    print_step(4, 7, "Creazione installer Windows...")
    
    spec_file = BASE_DIR / "installer_setup.iss"
    if not spec_file.exists():
        print_warning("File installer_setup.iss non trovato - saltato")
        return False
    
    # Cerca InnoSetup
    inno_paths = [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
        r"C:\Inno Setup 6\ISCC.exe",
    ]
    
    iscc_path = None
    for path in inno_paths:
        if Path(path).exists():
            iscc_path = path
            break
    
    if not iscc_path:
        print_warning("InnoSetup non trovato - installer non creato")
        print_warning("Installa InnoSetup da: https://jrsoftware.org/isdl.php")
        return False
    
    try:
        cmd = [iscc_path, str(spec_file)]
        result = subprocess.run(cmd, cwd=BASE_DIR, capture_output=True, text=True)
        
        if result.returncode == 0:
            # Cerca installer creato
            installer_dir = BASE_DIR / "release" / "installer"
            if installer_dir.exists():
                installers = list(installer_dir.glob("*.exe"))
                if installers:
                    installer = installers[0]
                    size_mb = installer.stat().st_size / (1024 * 1024)
                    print_success(f"Installer creato: {installer.name} ({size_mb:.1f} MB)")
                    return True
            
            print_warning("Installer compilato ma non trovato in release/installer")
            return False
        else:
            print_error("Errore durante creazione installer:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print_error(f"Errore creazione installer: {e}")
        return False

def print_summary():
    """Stampa riepilogo build"""
    print_step(7, 7, "Riepilogo build")
    print_header("BUILD COMPLETATO")
    
    print(f"\n{Colors.OKGREEN}File creati:{Colors.ENDC}")
    exe_path = DIST_DIR / "LAC_Translate.exe"
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"  - Eseguibile: {exe_path} ({size_mb:.1f} MB)")
    
    # Check installer
    installer_dir = BASE_DIR / "release" / "installer"
    if installer_dir.exists():
        installers = list(installer_dir.glob("*.exe"))
        if installers:
            print(f"\n{Colors.OKGREEN}Installer:{Colors.ENDC}")
            for installer in installers:
                size_mb = installer.stat().st_size / (1024 * 1024)
                print(f"  - {installer.name} ({size_mb:.1f} MB)")
    
    if RELEASE_DIR.exists():
        packages = list(RELEASE_DIR.glob("LAC_Translate_*"))
        if packages:
            print(f"\n{Colors.OKGREEN}Package distribuzione:{Colors.ENDC}")
            for pkg in packages:
                if pkg.is_dir():
                    print(f"  - {pkg.name}")
                elif pkg.suffix == '.zip':
                    size_mb = pkg.stat().st_size / (1024 * 1024)
                    print(f"  - {pkg.name} ({size_mb:.1f} MB)")

def update_version():
    """Aggiorna version file e build number"""
    version_file = BASE_DIR / "app" / "version.py"
    version_json = BASE_DIR / "VERSION.json"
    
    # Load current version
    try:
        if version_json.exists():
            with open(version_json, 'r') as f:
                version_data = json.load(f)
                current_build = version_data.get('build_number', 0)
        else:
            current_build = 0
    except:
        current_build = 0
    
    # Increment build
    new_build = current_build + 1
    
    # Update version.py
    if version_file.exists():
        with open(version_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Update build number
        content = re.sub(
            r'BUILD_NUMBER = \d+',
            f'BUILD_NUMBER = {new_build}',
            content
        )
        
        with open(version_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print_success(f"Build number aggiornato: {new_build}")
    
    # Update VERSION.json
    from app.version import get_build_info, save_version
    save_version()
    
    return new_build

def main():
    """Main build function"""
    print_header("LAC TRANSLATE - Build Script")
    
    print(f"Directory base: {BASE_DIR}")
    print(f"Python: {sys.executable}")
    print(f"Versione Python: {sys.version}")
    
    # Aggiorna build number
    build_num = update_version()
    print()
    
    # Esegui build steps
    clean_build()
    
    if not check_dependencies():
        print_error("Build fallito: dipendenze mancanti")
        return 1
    
    if not build_exe():
        print_error("Build fallito: errore compilazione")
        return 1
    
    copy_additional_files()
    
    # Crea installer (opzionale - non blocca build)
    build_installer()
    
    create_release_package()
    print_summary()
    
    print(f"\n{Colors.OKGREEN}{Colors.BOLD}✓ Build completato con successo!{Colors.ENDC}")
    print(f"{Colors.OKGREEN}Build Number: {build_num}{Colors.ENDC}\n")
    return 0

if __name__ == "__main__":
    sys.exit(main())

