#!/usr/bin/env python3
"""Quick test of column detection on the 2-column contract."""
import os
os.environ['DISABLE_MODEL_SOURCE_CHECK'] = 'True'
import logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

import time
import pymupdf
from app.core.rapid_ocr import RapidOcrEngine
from app.core.preprocess_for_ocr import preprocess_page_from_pymupdf

# Reset singleton
RapidOcrEngine._instance = None
RapidOcrEngine._engine = None
RapidOcrEngine._available = None

pdf_path = 'input/confidenziali/Signed_FY2025_2027_Authorized_Distribution_Agreement_Distributor.pdf'
doc = pymupdf.open(pdf_path)

# Test page 2 (0-indexed) - the body page with 2 columns
page = doc[2]
png_bytes, info = preprocess_page_from_pymupdf(page, dpi=300)
print(f"Image: {info['width']}x{info['height']} px, {info['file_size_kb']} KB")

engine = RapidOcrEngine()
t0 = time.time()
text, conf = engine.recognize_text(png_bytes)
elapsed = time.time() - t0

print(f"\nOCR time: {elapsed:.1f}s, confidence: {conf:.3f}")
print(f"Output: {len(text)} chars, {len(text.split())} words")
print(f"\n{'='*80}")
print("FIRST 3000 CHARS:")
print(f"{'='*80}")
print(text[:3000])
print(f"\n{'='*80}")

# Check key keywords
keywords = [
    "AUTHORIZED DISTRIBUTION AGREEMENT",
    "Authorised Distributor",
    "Article 1",
    "Definitions", 
    "Article 2",
    "Article 3",
    "Non-Competition",
    "Article 4",
    "Article 5",
    "Article 6",
    "Mimaki Europe",
    "Bompan",
    "Tradate",
    "Italy, Malta",
    "Territory",
    "Intellectual Property",
]

found = sum(1 for kw in keywords if kw.lower() in text.lower())
print(f"\nKeyword check: {found}/{len(keywords)} found")
for kw in keywords:
    status = "✅" if kw.lower() in text.lower() else "❌"
    print(f"  {status} {kw}")

doc.close()
