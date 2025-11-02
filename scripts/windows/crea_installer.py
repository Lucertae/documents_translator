#!/usr/bin/env python3
"""
LAC TRANSLATE - Script Creazione Installer Windows
Versione Python per compilare in .exe
Crea eseguibile .exe e installer .exe completo per distribuzione
"""
import os
import sys
import subprocess
from pathlib import Path

# Colors per output console
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

def main():
    """Main build process"""
    print_header("LAC TRANSLATE - Creazione Installer Windows")
    
    # Base directory
    base_dir = Path(__file__).parent.parent.parent
    
    # Step 1: Verifica Python
    print_step(1, 5, "Verifica Python...")
    try:
        result = subprocess.run([sys.executable, "--version"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print_success(f"Python trovato: {result.stdout.strip()}")
        else:
            print_error("Python non trovato!")
            input("\nPremi INVIO per uscire...")
            return 1
    except Exception as e:
        print_error(f"Errore verifica Python: {e}")
        input("\nPremi INVIO per uscire...")
        return 1
    
    # Step 2: Verifica PyInstaller
    print_step(2, 5, "Verifica PyInstaller...")
    try:
        import PyInstaller
        print_success("PyInstaller pronto")
    except ImportError:
        print_warning("PyInstaller non trovato, installazione...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"],
                         check=True)
            print_success("PyInstaller installato")
        except Exception as e:
            print_error(f"Errore installazione PyInstaller: {e}")
            input("\nPremi INVIO per uscire...")
            return 1
    
    # Step 3: Build eseguibile
    print_step(3, 5, "Build eseguibile .exe...")
    try:
        # Esegui build.py
        build_script = base_dir / "build.py"
        if not build_script.exists():
            print_error(f"build.py non trovato: {build_script}")
            input("\nPremi INVIO per uscire...")
            return 1
        
        result = subprocess.run([sys.executable, str(build_script)],
                              cwd=base_dir, 
                              capture_output=False)
        
        if result.returncode != 0:
            print_error("Errore durante build eseguibile")
            input("\nPremi INVIO per uscire...")
            return 1
        
        # Verifica eseguibile creato
        exe_path = base_dir / "dist" / "LAC_Translate.exe"
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print_success(f"Eseguibile creato: {exe_path.name} ({size_mb:.1f} MB)")
        else:
            print_warning("Eseguibile non trovato dopo build")
            print_warning("Verifica errori nel processo di build")
    except Exception as e:
        print_error(f"Errore build: {e}")
        input("\nPremi INVIO per uscire...")
        return 1
    
    # Step 4: Verifica InnoSetup
    print_step(4, 5, "Verifica InnoSetup...")
    inno_paths = [
        Path(r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"),
        Path(r"C:\Program Files\Inno Setup 6\ISCC.exe"),
        Path(r"C:\Inno Setup 6\ISCC.exe"),
    ]
    
    # Cerca anche nel PATH
    try:
        result = subprocess.run(["where", "ISCC.exe"], 
                              capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            inno_paths.insert(0, Path(result.stdout.strip()))
    except:
        pass
    
    iscc_path = None
    for path in inno_paths:
        if path.exists():
            iscc_path = path
            break
    
    if not iscc_path:
        print_warning("InnoSetup non trovato!")
        print_warning("L'eseguibile è stato creato in: dist\\LAC_Translate.exe")
        print_warning("Per creare l'installer:")
        print_warning("  1. Scarica InnoSetup da: https://jrsoftware.org/isdl.php")
        print_warning("  2. Installa")
        print_warning("  3. Rilancia questo script")
        print()
        print_success("Eseguibile standalone disponibile: dist\\LAC_Translate.exe")
        input("\nPremi INVIO per uscire...")
        return 0
    
    print_success("InnoSetup trovato")
    
    # Step 5: Crea installer
    print_step(5, 5, "Creazione installer...")
    try:
        installer_script = base_dir / "installer_setup.iss"
        if not installer_script.exists():
            print_warning("installer_setup.iss non trovato")
            input("\nPremi INVIO per uscire...")
            return 1
        
        result = subprocess.run([str(iscc_path), str(installer_script)],
                              cwd=base_dir,
                              capture_output=False)
        
        if result.returncode != 0:
            print_error("Errore durante creazione installer")
            input("\nPremi INVIO per uscire...")
            return 1
        
        # Verifica installer creato
        installer_dir = base_dir / "release" / "installer"
        if installer_dir.exists():
            installers = list(installer_dir.glob("*.exe"))
            if installers:
                installer = installers[0]
                size_mb = installer.stat().st_size / (1024 * 1024)
                print_success(f"Installer creato: {installer.name} ({size_mb:.1f} MB)")
                print()
                print(f"{Colors.OKGREEN}✓ INSTALLER COMPLETATO!{Colors.ENDC}")
                print()
                print(f"Installer: {installer}")
                print()
                print("Puoi distribuire questo installer agli utenti finali.")
                print("L'utente non deve installare Python - tutto è incluso!")
                input("\nPremi INVIO per uscire...")
                return 0
            else:
                print_warning("Installer non trovato dopo compilazione")
        else:
            print_warning("Directory installer non trovata")
    except Exception as e:
        print_error(f"Errore creazione installer: {e}")
        input("\nPremi INVIO per uscire...")
        return 1
    
    input("\nPremi INVIO per uscire...")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nOperazione annullata dall'utente")
        sys.exit(1)
    except Exception as e:
        print_error(f"Errore imprevisto: {e}")
        import traceback
        traceback.print_exc()
        input("\nPremi INVIO per uscire...")
        sys.exit(1)

