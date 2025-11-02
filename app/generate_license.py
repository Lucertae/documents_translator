#!/usr/bin/env python3
"""
LAC TRANSLATE - License Key Generator
Script per generare chiavi seriali per vendita
"""
import random
import string
import hashlib
import json
from pathlib import Path
from datetime import datetime

def generate_serial_key():
    """Genera una chiave seriale unica nel formato LAC-XXXX-XXXX-XXXX"""
    # Genera 12 caratteri alfanumerici
    chars = string.ascii_uppercase + string.digits
    # Rimuovi caratteri ambigui (0, O, I, 1)
    chars = chars.replace('0', '').replace('O', '').replace('I', '').replace('1', '')
    
    part1 = ''.join(random.choices(chars, k=4))
    part2 = ''.join(random.choices(chars, k=4))
    part3 = ''.join(random.choices(chars, k=4))
    
    return f"LAC-{part1}-{part2}-{part3}"

def generate_license_file(serial_key, customer_info=None):
    """Genera file licenza con chiave seriale"""
    license_data = {
        'serial_key': serial_key,
        'generated_at': datetime.now().isoformat(),
        'customer': customer_info or {},
        'license_type': 'FULL'
    }
    
    # Hash della chiave per verifica
    license_hash = hashlib.sha256(serial_key.encode()).hexdigest()[:16]
    license_data['hash'] = license_hash
    
    return license_data

def main():
    """Main function per generazione chiavi"""
    print("=" * 60)
    print("LAC TRANSLATE - Generatore Chiavi Seriali")
    print("=" * 60)
    print()
    
    mode = input("Modalità:\n1) Singola chiave\n2) Multiple chiavi (bulk)\nScelta (1/2): ").strip()
    
    if mode == "1":
        # Genera una singola chiave
        customer_name = input("Nome cliente (opzionale): ").strip()
        customer_email = input("Email cliente (opzionale): ").strip()
        
        serial_key = generate_serial_key()
        license_data = generate_license_file(
            serial_key,
            {
                'name': customer_name or None,
                'email': customer_email or None
            }
        )
        
        print()
        print("=" * 60)
        print("CHIAVE SERIALE GENERATA")
        print("=" * 60)
        print(f"Chiave: {serial_key}")
        print(f"Hash: {license_data['hash']}")
        print(f"Generata il: {license_data['generated_at']}")
        if customer_name:
            print(f"Cliente: {customer_name}")
        print()
        
        # Salva in file
        output_file = Path("license_keys") / f"{serial_key}.txt"
        output_file.parent.mkdir(exist_ok=True)
        
        with open(output_file, 'w') as f:
            f.write("LAC TRANSLATE - Chiave Seriale\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Chiave Seriale: {serial_key}\n")
            f.write(f"Tipo Licenza: FULL\n")
            f.write(f"Generata il: {license_data['generated_at']}\n")
            if customer_name:
                f.write(f"Cliente: {customer_name}\n")
            if customer_email:
                f.write(f"Email: {customer_email}\n")
            f.write("\n" + "=" * 50 + "\n")
            f.write("Istruzioni:\n")
            f.write("1. Invia questa chiave seriale al cliente\n")
            f.write("2. Il cliente deve inserirla nel software all'avvio\n")
            f.write("3. La licenza è legata all'hardware del cliente\n")
        
        print(f"✓ Chiave salvata in: {output_file}")
        
    elif mode == "2":
        # Genera multiple chiavi
        try:
            count = int(input("Numero di chiavi da generare: ").strip())
        except ValueError:
            print("Errore: Inserisci un numero valido")
            return
        
        print(f"\nGenerazione di {count} chiavi seriali...")
        
        licenses = []
        for i in range(count):
            serial_key = generate_serial_key()
            license_data = generate_license_file(serial_key)
            licenses.append(license_data)
            print(f"{i+1}/{count}: {serial_key}")
        
        # Salva tutte le chiavi
        output_file = Path("license_keys") / f"bulk_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        output_file.parent.mkdir(exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(licenses, f, indent=2)
        
        # Salva anche in formato testo
        txt_file = output_file.with_suffix('.txt')
        with open(txt_file, 'w') as f:
            f.write("LAC TRANSLATE - Chiavi Seriali Bulk\n")
            f.write("=" * 60 + "\n\n")
            for i, lic in enumerate(licenses, 1):
                f.write(f"{i}. {lic['serial_key']}\n")
            f.write(f"\nTotale: {len(licenses)} chiavi\n")
            f.write(f"Generato il: {datetime.now().isoformat()}\n")
        
        print()
        print(f"✓ Salvate {count} chiavi in:")
        print(f"  - JSON: {output_file}")
        print(f"  - TXT: {txt_file}")
        
    else:
        print("Scelta non valida")
        return
    
    print()
    print("=" * 60)
    print("Generazione completata!")
    print("=" * 60)

if __name__ == "__main__":
    main()

