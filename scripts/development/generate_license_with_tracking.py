#!/usr/bin/env python3
"""
LAC TRANSLATE - Generatore Licenze con Tracking
Versione migliorata che registra automaticamente nel database
"""
import sys
from pathlib import Path

# Aggiungi app/ al path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "app"))

from generate_license import generate_serial_key, generate_license_file
from license_tracker import LicenseTracker

def main():
    print("=" * 60)
    print("LAC TRANSLATE - Generatore Licenze con Tracking")
    print("=" * 60)
    print()
    
    tracker = LicenseTracker()
    
    mode = input("Modalità:\n1) Singola licenza\n2) Multiple licenze\nScelta (1/2): ").strip()
    
    if mode == "1":
        # Info cliente
        customer_name = input("Nome cliente: ").strip() or None
        customer_email = input("Email cliente: ").strip() or None
        customer_company = input("Azienda cliente (opzionale): ").strip() or None
        
        try:
            price_input = input("Prezzo vendita (€): ").strip()
            sold_price = float(price_input) if price_input else None
        except ValueError:
            sold_price = None
            print("⚠ Avviso: Prezzo non valido, continuo senza prezzo")
        
        notes = input("Note (opzionale): ").strip() or None
        
        # Genera chiave
        serial_key = generate_serial_key()
        
        # Registra nel database
        if tracker.add_license(serial_key, customer_name, customer_email, 
                              customer_company, sold_price, notes=notes):
            print(f"\n✓ Licenza registrata nel database")
        else:
            print(f"\n⚠ Avviso: Chiave già esistente (ma generata comunque)")
        
        # Crea file licenza (come prima)
        license_data = generate_license_file(serial_key, {
            'name': customer_name,
            'email': customer_email,
            'company': customer_company
        })
        
        # Salva file
        output_file = Path("license_keys") / f"{serial_key}.txt"
        output_file.parent.mkdir(exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("LAC TRANSLATE - Chiave Seriale\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Chiave Seriale: {serial_key}\n")
            f.write(f"Cliente: {customer_name or 'N/A'}\n")
            if customer_email:
                f.write(f"Email: {customer_email}\n")
            if customer_company:
                f.write(f"Azienda: {customer_company}\n")
            if sold_price:
                f.write(f"Prezzo: €{sold_price:.2f}\n")
            f.write(f"Data: {license_data['generated_at']}\n")
        
        print(f"✓ File licenza: {output_file}")
        print(f"\nChiave Serial: {serial_key}")
        
    elif mode == "2":
        # Bulk mode
        try:
            count = int(input("Numero licenze: ").strip())
        except ValueError:
            print("Errore: Numero non valido")
            return
        
        generated = []
        for i in range(count):
            serial_key = generate_serial_key()
            if tracker.add_license(serial_key):
                generated.append(serial_key)
                print(f"{i+1}/{count}: {serial_key}")
            else:
                print(f"{i+1}/{count}: {serial_key} (duplicata, riprovo...)")
                # Riprova fino a trovare chiave unica
                attempts = 0
                while attempts < 10:
                    serial_key = generate_serial_key()
                    if tracker.add_license(serial_key):
                        generated.append(serial_key)
                        print(f"{i+1}/{count}: {serial_key}")
                        break
                    attempts += 1
        
        print(f"\n✓ Generate {len(generated)} licenze nel database")
        print(f"File salvati in: license_keys/")
    else:
        print("Scelta non valida")

if __name__ == "__main__":
    main()

