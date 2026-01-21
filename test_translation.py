#!/usr/bin/env python3
"""Test translation quality on page 3."""
import sys
sys.path.insert(0, 'app')
import fitz
from paddleocr import PaddleOCR

# Import modules  
from core.ocr_utils import clean_ocr_text, post_process_ocr_text
from core.translator import TranslationEngine

print("Initializing OCR and Translator...")
ocr = PaddleOCR(lang='en', text_det_thresh=0.3, text_det_box_thresh=0.5)
engine = TranslationEngine('en', 'it')

pdf_path = 'input/confidenziali/Signed_FY2025_2027_Authorized_Distribution_Agreement_Distributor.pdf'
doc = fitz.open(pdf_path)
page = doc[2]  # Page 3 (index 2)

# Convert to image and OCR
mat = fitz.Matrix(2.0, 2.0)
pix = page.get_pixmap(matrix=mat, alpha=False)
img_path = '/tmp/test_page3.png'
pix.save(img_path)

result = ocr.predict(img_path)
raw_text = ' '.join(result[0]['rec_texts'])
cleaned = clean_ocr_text(raw_text)
processed = post_process_ocr_text(cleaned)

print(f"\n{'='*60}")
print("ORIGINAL (after OCR cleanup):")
print('='*60)
# Take first 1000 chars
sample = processed[:1500]
print(sample)

print(f"\n{'='*60}")
print("TRANSLATED (EN -> IT):")
print('='*60)
# Translate in chunks
sentences = sample.split('. ')
translated_parts = []
for sentence in sentences[:15]:  # First 15 sentences
    if sentence.strip():
        try:
            trans = engine.translate(sentence.strip())
            translated_parts.append(trans)
        except Exception as e:
            translated_parts.append(f"[ERROR: {e}]")

print('. '.join(translated_parts))

doc.close()
print(f"\n{'='*60}")
print("Translation test complete")
print('='*60)
