#!/usr/bin/env python3
"""
Script rapido per generare licenza di test per sviluppo
"""
import sys
from pathlib import Path

# Aggiungi app/ al path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "app"))

from generate_license import generate_serial_key

def main():
    """Genera rapidamente una licenza di test"""
    print("=" * 60)
    print("LAC TRANSLATE - Generazione Licenza Test")
    print("=" * 60)
    print()
    
    # Genera chiave seriale
    serial_key = generate_serial_key()
    
    print(f"✓ Chiave Serial generata: {serial_key}")
    print()
    print("=" * 60)
    print("COPIA QUESTA CHIAVE NELL'APPLICAZIONE:")
    print("=" * 60)
    print()
    print(f"  {serial_key}")
    print()
    print("=" * 60)
    print()
    print("Istruzioni:")
    print("1. Apri l'applicazione LAC TRANSLATE")
    print("2. Quando ti chiede la licenza, incolla questa chiave:")
    print(f"   {serial_key}")
    print("3. Clicca 'Attiva'")
    print()
    print("⚠ NOTA: Questa è una licenza di test/sviluppo.")
    print("   Per licenze produzione, usa generate_license_with_tracking.py")
    print()
    
    return serial_key

if __name__ == "__main__":
    serial_key = main()
    # Salva anche in file per riferimento
    test_key_file = Path(__file__).parent.parent.parent / "TEST_LICENSE_KEY.txt"
    with open(test_key_file, 'w') as f:
        f.write(f"TEST LICENSE KEY\n")
        f.write(f"===============\n\n")
        f.write(f"Serial Key: {serial_key}\n")
        f.write(f"\nGenerated for development/testing purposes\n")
    print(f"✓ Chiave salvata anche in: {test_key_file}")
    print()

