#!/usr/bin/env python3
"""Generate translated PDFs for visual quality inspection.

Creates output PDFs for a few key documents to verify:
1. Multi-column rendering (Economist 1881)
2. Dense page auto-scaling (contracts)
3. Table formatting
4. Heading hierarchy
"""
import os
import sys
import logging

os.environ['MINERU_DEVICE_MODE'] = 'cpu'
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

from app.core.pdf_processor import PDFProcessor

# Use a simple pass-through "translator" that adds [IT] prefix
# to make it easy to see which content was translated
class IdentityTranslator:
    """Returns the input text mostly unchanged, adds marker for visibility."""
    def translate(self, text: str) -> str:
        return text  # keep original text so we can judge formatting

class MarkingTranslator:
    """Returns text with [TR] marker for checking completeness."""
    def translate(self, text: str) -> str:
        return f"[TR] {text}"


TEST_PAGES = [
    # (pdf_path, page_0indexed, description)
    ("input/sim_economist_1881-08-06_39_1980.pdf", 2,
     "economist_p3_multicol"),
    ("input/confidenziali/Signed_FY2025_2027_Authorized_Distribution_Agreement_Distributor.pdf", 2,
     "contract_p3_dense"),
    ("input/DOC040625-04062025140056.pdf", 2,
     "doc040625_p3_dense"),
    ("input/confidenziali/Distribution Contract Trotec Bompan SRL_01062024_signed both parties.pdf", 0,
     "trotec_p1_table"),
]

os.makedirs("output/visual_check", exist_ok=True)

for pdf_path, page_idx, desc in TEST_PAGES:
    if not os.path.exists(pdf_path):
        print(f"SKIP: {pdf_path} not found")
        continue
    
    print(f"\n{'='*60}")
    print(f"Generating: {desc} (page {page_idx+1})")
    print(f"{'='*60}")
    
    output_path = f"output/visual_check/{desc}.pdf"
    
    proc = PDFProcessor(pdf_path)
    # Use identity translator for visual check
    translator = IdentityTranslator()
    
    try:
        import pymupdf
        
        # Open source PDF
        src_doc = pymupdf.open(pdf_path)
        
        # Extract just the one page into a new doc
        single_page_doc = pymupdf.open()
        single_page_doc.insert_pdf(src_doc, from_page=page_idx, to_page=page_idx)
        
        # Save the single page to a temp file
        tmp_path = f"/tmp/{desc}_src.pdf"
        single_page_doc.save(tmp_path)
        single_page_doc.close()
        src_doc.close()
        
        # Process with our pipeline
        proc2 = PDFProcessor(tmp_path)
        
        # Create output doc with same page size
        src = pymupdf.open(tmp_path)
        page = src[0]
        new_doc = pymupdf.open()
        new_doc.new_page(width=page.rect.width, height=page.rect.height)
        
        new_doc = proc2._translate_scanned_page_rapiddoc(
            new_doc, page, page_idx, translator,
            text_color=(0, 0, 0),
            ocr_language="en"
        )
        
        new_doc.save(output_path)
        new_doc.close()
        src.close()
        
        # Report
        check_doc = pymupdf.open(output_path)
        out_text = check_doc[0].get_text('text')
        check_doc.close()
        
        words = len(out_text.split())
        chars = len(out_text)
        print(f"  Output: {output_path}")
        print(f"  Text: {chars} chars, {words} words")
        print(f"  Preview: {out_text[:200]}...")
        
    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()

print(f"\n{'='*60}")
print("Visual check PDFs generated in output/visual_check/")
print("Open them in a PDF viewer to inspect formatting.")
print(f"{'='*60}")
