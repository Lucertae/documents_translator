#!/usr/bin/env python3
"""
LAC TRANSLATE - Visualizza Licenze Vendute
CLI per visualizzare e filtrare licenze nel database
"""
import sys
from pathlib import Path
import json
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "app"))
from license_tracker import LicenseTracker

def main():
    tracker = LicenseTracker()
    
    print("=" * 60)
    print("LAC TRANSLATE - Visualizza Licenze")
    print("=" * 60)
    print()
    
    action = input("1) Lista tutte\n2) Filtra per status\n3) Report vendite\n4) Esporta JSON\nScelta: ").strip()
    
    if action == "1":
        licenses = tracker.list_licenses()
        print(f"\nTrovate {len(licenses)} licenze:\n")
        for lic in licenses:
            status_icon = "✓" if lic['status'] == 'activated' else "⏳" if lic['status'] == 'pending' else "✗"
            print(f"  {status_icon} {lic['serial_key']} | {lic['status']} | {lic['customer_name'] or 'N/A'} | €{lic['sold_price'] or 0:.2f}")
    
    elif action == "2":
        status = input("Status (pending/activated/revoked): ").strip()
        licenses = tracker.list_licenses(status=status)
        print(f"\nTrovate {len(licenses)} licenze con status '{status}':\n")
        for lic in licenses:
            print(f"  {lic['serial_key']} | {lic['customer_name'] or 'N/A'} | {lic['sold_date'] or 'N/A'}")
    
    elif action == "3":
        report = tracker.get_sales_report()
        print("\n" + "=" * 60)
        print("REPORT VENDITE")
        print("=" * 60)
        print(f"Licenze vendute: {report['total_sold']}")
        print(f"Ricavi totali: €{report['total_revenue']:.2f}")
        print(f"Attivate: {report['total_activated']}")
        print(f"Pendenti: {report['total_pending']}")
        print("=" * 60)
    
    elif action == "4":
        output = Path("license_registry.json")
        if tracker.export_to_json(output):
            print(f"\n✓ Esportato in: {output}")
        else:
            print("\n✗ Errore esportazione")
    else:
        print("Scelta non valida")

if __name__ == "__main__":
    main()

