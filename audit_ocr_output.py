#!/usr/bin/env python3
"""
Comprehensive OCR output audit.
Runs OCR on representative pages from all available documents,
applies post-processing, and dumps full output for inspection.
"""
import sys, os, io, time
sys.path.insert(0, '/home/bracco/documents_translator')
os.environ['DISABLE_MODEL_SOURCE_CHECK'] = 'True'

import logging
logging.basicConfig(level=logging.WARNING)

import pymupdf
import numpy as np
from PIL import Image

# Reset singleton to ensure fresh params
from app.core.rapid_ocr import RapidOcrEngine
RapidOcrEngine._instance = None
RapidOcrEngine._engine = None
RapidOcrEngine._available = None

from app.core.preprocess_for_ocr import preprocess_page_from_pymupdf
from app.core.ocr_utils import post_process_ocr_text, clean_ocr_text

DOCUMENTS = [
    {
        'path': 'input/confidenziali/Signed_FY2025_2027_Authorized_Distribution_Agreement_Distributor.pdf',
        'pages': [1, 2, 3],
        'name': 'Mimaki Distribution Agreement',
    },
    {
        'path': 'input/confidenziali/Distribution Contract Trotec Bompan SRL_01062024_signed both parties.pdf',
        'pages': [0, 1, 2],
        'name': 'Trotec-Bompan Contract',
    },
    {
        'path': 'input/confidenziali/1.pdf',
        'pages': [0],
        'name': 'Studio Legale Letter',
    },
    {
        'path': 'input/confidenziali/DOC040625-04062025140056.pdf',
        'pages': [0],
        'name': 'DOC040625 Scan',
    },
    {
        'path': 'input/2015.129351.Bibliography-Of-Doctoral-Dissertations_text.pdf',
        'pages': [0, 1, 2],
        'name': 'Bibliography Doctoral Dissertations',
    },
    {
        'path': 'input/sim_economist_1881-08-06_39_1980.pdf',
        'pages': [0, 1, 2],
        'name': 'The Economist 1881',
    },
    {
        'path': 'input/sim_quarterly-journal-of-economics_1980_94_contents.pdf',
        'pages': [0, 1],
        'name': 'Quarterly Journal Economics 1980',
    },
    {
        'path': 'input/V. S. Vladimirov - Equations of mathematical physics b.pdf',
        'pages': [0, 1, 2],
        'name': 'Vladimirov Math Physics',
    },
    {
        'path': 'input/Coates_825.pdf',
        'pages': [0, 1],
        'name': 'Coates 825',
    },
]

engine = RapidOcrEngine()
total_time = 0
total_pages = 0

for doc_info in DOCUMENTS:
    path = doc_info['path']
    if not os.path.exists(path):
        print(f"\n--- SKIPPED: {doc_info['name']} (not found: {path}) ---")
        continue

    doc = pymupdf.open(path)
    print(f"\n{'#'*100}")
    print(f"# {doc_info['name']}")
    print(f"# File: {path} ({len(doc)} pages total)")
    print(f"{'#'*100}")

    for page_idx in doc_info['pages']:
        if page_idx >= len(doc):
            continue
        page = doc[page_idx]

        t0 = time.time()
        png, info = preprocess_page_from_pymupdf(page)
        text_raw, conf = engine.recognize_text(png)
        text_clean = post_process_ocr_text(text_raw)
        elapsed = time.time() - t0
        total_time += elapsed
        total_pages += 1

        print(f"\n{'='*80}")
        print(f"PAGE {page_idx} | {info['width']}x{info['height']} | {info['file_size_kb']}KB | {elapsed:.2f}s | conf={conf:.3f}")
        print(f"Raw: {len(text_raw)} chars, {len(text_raw.split())} words | Clean: {len(text_clean)} chars")
        print(f"{'='*80}")
        print(text_clean)
        print(f"{'='*80}")

    doc.close()

print(f"\n\n{'#'*100}")
print(f"# TOTALS: {total_pages} pages in {total_time:.1f}s ({total_time/max(total_pages,1):.2f}s/page)")
print(f"{'#'*100}")
