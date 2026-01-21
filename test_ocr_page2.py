#!/usr/bin/env python3
"""Test OCR corrections on page 2."""
import sys
import io

# Redirect stdout to file and console
class Tee:
    def __init__(self, *files):
        self.files = files
    def write(self, obj):
        for f in self.files:
            f.write(obj)
            f.flush()
    def flush(self):
        for f in self.files:
            f.flush()

output_file = open('/tmp/ocr_test_output.txt', 'w')
sys.stdout = Tee(sys.stdout, output_file)

sys.path.insert(0, 'app')
import fitz
from paddleocr import PaddleOCR
import importlib
import core.ocr_utils
importlib.reload(core.ocr_utils)
from core.ocr_utils import clean_ocr_text, post_process_ocr_text

print("Starting OCR test...")

# Init OCR (same params as in pdf_processor.py)
ocr = PaddleOCR(
    lang='en',
    text_det_thresh=0.3,
    text_det_box_thresh=0.5
)

# Load PDF page 2
pdf_path = 'input/confidenziali/Signed_FY2025_2027_Authorized_Distribution_Agreement_Distributor.pdf'
doc = fitz.open(pdf_path)
page = doc[1]

# Convert to image
mat = fitz.Matrix(2.0, 2.0)
pix = page.get_pixmap(matrix=mat, alpha=False)
img_path = '/tmp/test_page2.png'
pix.save(img_path)

# OCR
result = ocr.predict(img_path)
print(f'Found {len(result[0]["rec_texts"])} text regions')

# Build text
raw_text = ' '.join(result[0]['rec_texts'])
cleaned = clean_ocr_text(raw_text)
processed = post_process_ocr_text(cleaned)

print('\n=== Sample of Cleaned Text ===')
print(processed[:1500])

# Check for remaining issues
issues = []
if 'MimakI' in processed or 'MimaKI' in processed:
    issues.append('Mimaki variations')
if 'nibit' in processed.lower():
    issues.append('nibit/Exhibit')
if 'ICE ' in processed:
    issues.append('ICE/Article')

print(f'\n=== Issues found: {issues if issues else "None!"} ===')
doc.close()
output_file.close()
