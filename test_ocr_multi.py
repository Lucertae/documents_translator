#!/usr/bin/env python3
"""Test OCR corrections on multiple pages."""
import sys
sys.path.insert(0, 'app')
import fitz
from paddleocr import PaddleOCR
import importlib
import core.ocr_utils
importlib.reload(core.ocr_utils)
from core.ocr_utils import clean_ocr_text, post_process_ocr_text

print("Initializing OCR...")
ocr = PaddleOCR(
    lang='en',
    text_det_thresh=0.3,
    text_det_box_thresh=0.5
)

pdf_path = 'input/confidenziali/Signed_FY2025_2027_Authorized_Distribution_Agreement_Distributor.pdf'
doc = fitz.open(pdf_path)

for page_num in [1, 2, 3]:  # Pages 1-3 (index 0-2)
    page = doc[page_num - 1]
    print(f"\n{'='*60}")
    print(f"PAGE {page_num}")
    print('='*60)
    
    # Convert to image
    mat = fitz.Matrix(2.0, 2.0)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    img_path = f'/tmp/test_page{page_num}.png'
    pix.save(img_path)
    
    # OCR
    result = ocr.predict(img_path)
    print(f'Text regions: {len(result[0]["rec_texts"])}')
    
    # Build text
    raw_text = ' '.join(result[0]['rec_texts'])
    cleaned = clean_ocr_text(raw_text)
    processed = post_process_ocr_text(cleaned)
    
    # Check for issues
    issues = []
    if 'MimakI' in processed or 'MimaKI' in processed:
        issues.append('MimakI/MimaKI')
    if 'Mimakl' in processed:
        issues.append('Mimakl')
    if 'nibit' in processed.lower():
        issues.append('nibit')
    if 'ICE ' in processed and 'Article' not in processed[:500]:
        issues.append('ICE (should be Article)')
    
    print(f'Issues: {issues if issues else "None"}')
    
    # First 500 chars
    print(f'\nSample: {processed[:400]}...')

doc.close()
print("\n" + "="*60)
print("TEST COMPLETE")
print("="*60)
