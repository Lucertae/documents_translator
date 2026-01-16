"""
Test full translation of DI_PAOLO_THESIS.pdf page 2 with new cross-block merging.
"""
import sys
sys.path.insert(0, '.')

import logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

from app.core.pdf_processor import PDFProcessor
from app.core.translator import TranslationEngine

PDF_PATH = "input/DI_PAOLO_THESIS.pdf"
OUTPUT_PATH = "output/test_page2_translated.pdf"
PAGE_NUM = 1  # 0-indexed, page 2

def test_translation():
    """Test translation with cross-block merging."""
    print("=" * 80)
    print("Testing translation on DI_PAOLO_THESIS.pdf page 2")
    print("=" * 80)
    
    # Create translator (Italian to English)
    print("\nInitializing translator...")
    translator = TranslationEngine(source_lang='it', target_lang='en')
    
    # Create processor
    print("Loading PDF...")
    processor = PDFProcessor(PDF_PATH)
    
    # Translate page 2
    print(f"\nTranslating page {PAGE_NUM + 1}...")
    translated_doc = processor.translate_page(
        page_num=PAGE_NUM,
        translator=translator,
        preserve_line_breaks=True
    )
    
    # Save the result
    print(f"\nSaving to {OUTPUT_PATH}...")
    translated_doc.save(OUTPUT_PATH)
    translated_doc.close()
    
    print(f"\n✓ Done! Check {OUTPUT_PATH}")

if __name__ == "__main__":
    test_translation()
