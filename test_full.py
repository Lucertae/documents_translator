#!/usr/bin/env python3
"""
Full document translation test - 13 pages.
"""
import sys
import time
sys.path.insert(0, 'app')

from core.pdf_processor import PDFProcessor
from core.translator import TranslationEngine

# Test parameters
pdf_path = 'input/confidenziali/Signed_FY2025_2027_Authorized_Distribution_Agreement_Distributor.pdf'
output_path = 'output/test_full_translation.pdf'

print("="*60)
print("FULL DOCUMENT TRANSLATION TEST")
print("="*60)

# Create processor with PDF path
print(f"\nLoading: {pdf_path}")
processor = PDFProcessor(pdf_path)
print(f"Pages: {processor.page_count}")

# Create translator
print("\nInitializing translator...")
translator = TranslationEngine('en', 'it')

# Translate all pages
import fitz
final_doc = fitz.open()

start_time = time.time()
for page_num in range(processor.page_count):
    page_start = time.time()
    print(f"\n--- Page {page_num + 1}/{processor.page_count} ---")
    
    try:
        result_doc = processor.translate_page(
            page_num=page_num,
            translator=translator,
            ocr_language='en'
        )
        
        # Append to final document
        final_doc.insert_pdf(result_doc)
        result_doc.close()
        
        elapsed = time.time() - page_start
        print(f"✓ Page {page_num + 1} completed ({elapsed:.1f}s)")
        
    except Exception as e:
        print(f"✗ Page {page_num + 1} failed: {e}")
        import traceback
        traceback.print_exc()

# Save final document
final_doc.save(output_path)
final_doc.close()

total_time = time.time() - start_time
print(f"\n{'='*60}")
print(f"TRANSLATION COMPLETE")
print(f"Total time: {total_time:.1f}s ({total_time/processor.page_count:.1f}s/page)")
print(f"Output: {output_path}")
print("="*60)
