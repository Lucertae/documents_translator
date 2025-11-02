#!/usr/bin/env python3
"""
Script per scaricare i modelli di traduzione Argos Translate
"""
import argostranslate.package
import argostranslate.translate

def download_and_install_models():
    """Scarica e installa i modelli di traduzione necessari"""
    
    # Aggiorna l'indice dei pacchetti
    print("[*] Aggiornamento indice pacchetti Argos Translate...")
    argostranslate.package.update_package_index()
    
    # Ottieni i pacchetti disponibili
    available_packages = argostranslate.package.get_available_packages()
    
    # Lingue da installare (inglese <-> italiano, inglese <-> spagnolo, etc.)
    language_pairs = [
        ('en', 'it'),  # English -> Italian
        ('it', 'en'),  # Italian -> English
        ('en', 'es'),  # English -> Spanish
        ('es', 'en'),  # Spanish -> English
        ('en', 'fr'),  # English -> French
        ('fr', 'en'),  # French -> English
        ('en', 'de'),  # English -> German
        ('de', 'en'),  # German -> English
    ]
    
    installed_count = 0
    
    for from_code, to_code in language_pairs:
        # Trova il pacchetto per questa coppia di lingue
        package_to_install = None
        for package in available_packages:
            if package.from_code == from_code and package.to_code == to_code:
                package_to_install = package
                break
        
        if package_to_install:
            # Controlla se è già installato
            installed_packages = argostranslate.package.get_installed_packages()
            already_installed = any(
                pkg.from_code == from_code and pkg.to_code == to_code 
                for pkg in installed_packages
            )
            
            if already_installed:
                print(f"[OK] {from_code} -> {to_code}: gia installato")
            else:
                print(f"[DOWN] Scaricamento {from_code} -> {to_code}...")
                try:
                    argostranslate.package.install_from_path(
                        package_to_install.download()
                    )
                    print(f"[OK] {from_code} -> {to_code}: installato con successo!")
                    installed_count += 1
                except Exception as e:
                    print(f"[ERR] Errore installazione {from_code} -> {to_code}: {e}")
        else:
            print(f"[WARN] Pacchetto {from_code} -> {to_code} non trovato")
    
    print(f"\n[DONE] Setup completato! {installed_count} nuovi modelli installati.")
    
    # Mostra tutti i modelli installati
    installed_packages = argostranslate.package.get_installed_packages()
    print(f"\n[INFO] Modelli installati totali: {len(installed_packages)}")
    for pkg in installed_packages:
        print(f"   - {pkg.from_name} ({pkg.from_code}) -> {pkg.to_name} ({pkg.to_code})")

if __name__ == "__main__":
    download_and_install_models()

