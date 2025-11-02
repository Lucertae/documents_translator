#!/usr/bin/env python3
"""
Test script per verificare disponibilità e funzionamento OCR engines
"""
import sys
from pathlib import Path
from PIL import Image
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Aggiungi app directory al path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from ocr_manager import get_ocr_manager, OCREngine
    
    print("=" * 60)
    print("TEST OCR ENGINES - LAC TRANSLATE")
    print("=" * 60)
    print()
    
    # Ottieni manager OCR
    ocr_manager = get_ocr_manager()
    
    # Verifica disponibilità
    print("Verifica disponibilità motori OCR:")
    print("-" * 60)
    
    engines_status = {
        OCREngine.TESSERACT: ocr_manager.is_available(OCREngine.TESSERACT),
        OCREngine.DOLPHIN: ocr_manager.is_available(OCREngine.DOLPHIN),
        OCREngine.CHANDRA: ocr_manager.is_available(OCREngine.CHANDRA),
    }
    
    for engine, available in engines_status.items():
        status = "[OK] DISPONIBILE" if available else "[NO] NON DISPONIBILE"
        print(f"  {engine.value:15s}: {status}")
    
    print()
    print("Motori disponibili:", ", ".join(ocr_manager.get_available_engines()) or "NESSUNO")
    print()
    
    # Test con immagine se disponibile
    print("-" * 60)
    print("Test estrazione testo:")
    print("-" * 60)
    
    # Crea immagine test semplice (bianco con testo nero)
    try:
        from PIL import ImageDraw, ImageFont
        
        # Crea immagine test
        img = Image.new('RGB', (400, 100), color='white')
        draw = ImageDraw.Draw(img)
        
        # Disegna testo test
        try:
            font = ImageFont.truetype("arial.ttf", 24)
        except:
            font = ImageFont.load_default()
        
        text = "LAC TRANSLATE OCR TEST"
        draw.text((10, 30), text, fill='black', font=font)
        
        # Salva immagine test
        test_image_path = Path(__file__).parent.parent / "test_ocr_image.png"
        img.save(test_image_path)
        print(f"Immagine test creata: {test_image_path}")
        
        # Test estrazione con AUTO (prova tutti i motori disponibili)
        print("\nTest estrazione testo (modalità AUTO):")
        result = ocr_manager.extract_text(img, engine=OCREngine.AUTO, lang='eng')
        
        if result:
            print(f"[OK] Testo estratto: {result[:50]}...")
            if "LAC" in result.upper() or "TRANSLATE" in result.upper():
                print("[OK] OCR funziona correttamente!")
            else:
                print("[WARNING] OCR estratto testo ma potrebbe non essere accurato")
        else:
            print("[NO] Nessun testo estratto")
        
        # Test con ogni motore disponibile
        print("\nTest per motore specifico:")
        for engine in [OCREngine.TESSERACT, OCREngine.DOLPHIN, OCREngine.CHANDRA]:
            if engines_status[engine]:
                result = ocr_manager.extract_text(img, engine=engine, lang='eng')
                if result:
                    print(f"  {engine.value}: [OK] - {result[:30]}...")
                else:
                    print(f"  {engine.value}: [NO] Nessun risultato")
        
        # Rimuovi immagine test
        if test_image_path.exists():
            test_image_path.unlink()
            print(f"\nImmagine test rimossa")
        
    except Exception as e:
        print(f"Errore durante test immagine: {e}")
        print("Test immagine saltato")
    
    print()
    print("=" * 60)
    print("TEST COMPLETATO")
    print("=" * 60)
    
except ImportError as e:
    print(f"ERRORE: Impossibile importare OCR Manager: {e}")
    print("Assicurati di avere installato tutte le dipendenze:")
    print("  pip install pytesseract pdf2image pillow")
    sys.exit(1)
except Exception as e:
    print(f"ERRORE: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

