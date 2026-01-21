#!/usr/bin/env python3
"""
End-to-end test: Translate page 3 using the full pipeline.
"""
import sys
sys.path.insert(0, 'app')

from core.pdf_processor import PDFProcessor

# Test parameters
pdf_path = 'input/confidenziali/Signed_FY2025_2027_Authorized_Distribution_Agreement_Distributor.pdf'
output_path = '/tmp/test_translation_page3.pdf'

print("="*60)
print("END-TO-END TRANSLATION TEST - PAGE 3")
print("="*60)

# Create processor with PDF path
print(f"\nLoading: {pdf_path}")
processor = PDFProcessor(pdf_path)

# Translate page 3 only (index 2)
print("\nTranslating page 3...")
try:
    # Need to create translator first
    from core.translator import TranslationEngine
    translator = TranslationEngine('en', 'it')
    
    result_doc = processor.translate_page(
        page_num=2,  # Page 3 is index 2
        translator=translator,
        ocr_language='en'
    )
    
    # Save the result
    result_doc.save(output_path)
    result_doc.close()
    
    print(f"\n✓ Output saved to: {output_path}")
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("TEST COMPLETE")
print("="*60)
