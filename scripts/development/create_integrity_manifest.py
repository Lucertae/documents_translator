#!/usr/bin/env python3
"""
Script per creare manifest integrità file critici
Da eseguire durante build per distribuzione
"""
import sys
from pathlib import Path

# Aggiungi app/ al path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "app"))

from integrity_checker import IntegrityChecker

def main():
    """Crea manifest integrità per file critici"""
    base_dir = Path(__file__).parent.parent.parent
    
    print("=" * 60)
    print("LAC TRANSLATE - Integrity Manifest Generator")
    print("=" * 60)
    print()
    
    # File critici da verificare
    critical_files = [
        'app/license_manager.py',
        'app/license_activation.py',
        'app/pdf_translator_gui.py',
        'app/integrity_checker.py',
        'app/security_validator.py',
    ]
    
    checker = IntegrityChecker(base_dir)
    
    print("Creating integrity manifest for critical files...")
    print()
    
    manifest = checker.create_manifest(critical_files)
    
    if manifest:
        if checker.save_manifest(manifest):
            print(f"✓ Manifest created: {checker.manifest_file}")
            print()
            print("Files in manifest:")
            for file_path, file_hash in manifest.items():
                print(f"  {file_path}: {file_hash[:16]}...")
        else:
            print("✗ Error saving manifest")
            return 1
    else:
        print("✗ Error creating manifest")
        return 1
    
    print()
    print("=" * 60)
    print("Manifest creation completed!")
    print("=" * 60)
    print()
    print("This manifest will be used to verify file integrity on startup.")
    print("If files are modified, integrity check will detect it.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

