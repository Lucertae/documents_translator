#!/usr/bin/env python3
"""Translate Mimaki contract - page by page with progress saving."""
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

import fitz
import time
import sys

from app.core.pdf_processor import PDFProcessor
from app.core.translator import TranslationEngine

def main():
    pdf_path = 'input/confidenziali/Signed_FY2025_2027_Authorized_Distribution_Agreement_Distributor.pdf'
    output_path = 'output/mimaki_translated_full.pdf'
    
    print("="*60)
    print("TRADUZIONE CONTRATTO MIMAKI")
    print("="*60)
    
    # Carica PDF
    pdf = PDFProcessor(pdf_path)
    print(f"PDF caricato: {pdf.page_count} pagine")
    
    # Inizializza traduttore (una sola volta)
    translator = TranslationEngine('en', 'it')
    
    # Documento finale
    final_doc = fitz.open()
    
    # Traduci pagina per pagina
    start_time = time.time()
    
    for page_num in range(pdf.page_count):
        page_start = time.time()
        print(f"\n{'='*40}")
        print(f"Traduzione pagina {page_num + 1}/{pdf.page_count}")
        print(f"{'='*40}")
        
        try:
            translated = pdf.translate_page(page_num, translator)
            final_doc.insert_pdf(translated)
            translated.close()
            
            page_time = time.time() - page_start
            print(f"✅ Pagina {page_num + 1} completata in {page_time:.1f}s")
            
            # Salva progresso ogni 3 pagine
            if (page_num + 1) % 3 == 0:
                progress_path = f'output/mimaki_progress_p{page_num+1}.pdf'
                final_doc.save(progress_path)
                print(f"💾 Progresso salvato: {progress_path}")
                
        except Exception as e:
            print(f"❌ Errore pagina {page_num + 1}: {e}")
            # Continua con la prossima pagina
            continue
    
    # Salva documento finale
    final_doc.save(output_path)
    total_time = time.time() - start_time
    
    print(f"\n{'='*60}")
    print(f"✅ TRADUZIONE COMPLETATA!")
    print(f"   Pagine: {final_doc.page_count}")
    print(f"   Tempo: {total_time/60:.1f} minuti")
    print(f"   Output: {output_path}")
    print(f"{'='*60}")
    
    final_doc.close()
    pdf.close()

if __name__ == "__main__":
    main()
