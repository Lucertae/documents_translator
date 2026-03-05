#!/usr/bin/env python3
"""
Test OCR quality on the two-column Authorized Distribution Agreement.
Dumps raw RapidOCR output with box coordinates for analysis.
"""
import os
os.environ['DISABLE_MODEL_SOURCE_CHECK'] = 'True'

import logging
logging.basicConfig(level=logging.WARNING)

import numpy as np
from PIL import Image
import io
import pymupdf

from app.core.rapid_ocr import RapidOcrEngine
from app.core.preprocess_for_ocr import preprocess_page_from_pymupdf


def dump_ocr_boxes(png_bytes, page_idx):
    """Run OCR and dump all detected boxes with coordinates."""
    engine = RapidOcrEngine()
    
    img = Image.open(io.BytesIO(png_bytes))
    img_np = np.array(img.convert("RGB"))
    
    result = engine._engine(img_np)
    
    if result is None or result.txts is None:
        print(f"  Page {page_idx}: No text detected")
        return
    
    print(f"\n{'='*80}")
    print(f"Page {page_idx} - {len(result.txts)} text boxes detected")
    print(f"Elapsed: {result.elapse:.3f}s")
    print(f"{'='*80}")
    
    # Print all boxes with coordinates
    boxes = result.boxes
    txts = result.txts
    scores = result.scores
    
    entries = []
    for i, (box, txt, score) in enumerate(zip(boxes, txts, scores)):
        y_center = float(np.mean(box[:, 1]))
        x_min = float(np.min(box[:, 0]))
        x_max = float(np.max(box[:, 0]))
        y_min = float(np.min(box[:, 1]))
        y_max = float(np.max(box[:, 1]))
        box_h = y_max - y_min
        box_w = x_max - x_min
        entries.append({
            'idx': i, 'txt': txt, 'score': score,
            'x_min': x_min, 'x_max': x_max,
            'y_min': y_min, 'y_max': y_max,
            'y_center': y_center, 'box_h': box_h, 'box_w': box_w
        })
    
    # Sort by y then x
    entries.sort(key=lambda e: (e['y_center'], e['x_min']))
    
    print(f"\n{'Idx':>4} {'X_min':>7} {'X_max':>7} {'Y_min':>7} {'Y_max':>7} {'Score':>6} Text")
    print("-" * 120)
    for e in entries:
        print(f"{e['idx']:>4} {e['x_min']:>7.1f} {e['x_max']:>7.1f} {e['y_min']:>7.1f} {e['y_max']:>7.1f} {e['score']:>6.3f} {e['txt'][:70]}")
    
    # Also show the reconstructed text
    text = engine._reconstruct_text(result)
    print(f"\n--- Reconstructed text ({len(text)} chars) ---")
    print(text[:3000])
    
    # Analyze column structure
    x_mins = [e['x_min'] for e in entries]
    page_width = max(e['x_max'] for e in entries)
    midpoint = page_width / 2
    
    left_count = sum(1 for x in x_mins if x < midpoint)
    right_count = sum(1 for x in x_mins if x >= midpoint)
    
    print(f"\n--- Column Analysis ---")
    print(f"Page width: {page_width:.0f}")
    print(f"Midpoint: {midpoint:.0f}")
    print(f"Left boxes: {left_count}, Right boxes: {right_count}")
    
    if right_count > 3 and left_count > 3:
        print("=> MULTI-COLUMN layout detected!")
    else:
        print("=> Single column layout")


def main():
    pdf_path = 'input/confidenziali/Signed_FY2025_2027_Authorized_Distribution_Agreement_Distributor.pdf'
    doc = pymupdf.open(pdf_path)
    print(f'Total pages: {len(doc)}')
    
    # Test the TOC page (page 1, 0-indexed) and first content page
    for page_idx in [1, 2, 3]:
        page = doc[page_idx]
        png_bytes, info = preprocess_page_from_pymupdf(page, dpi=150)
        print(f"\nPreprocessed: {info['width']}x{info['height']} px, {info['file_size_kb']} KB")
        dump_ocr_boxes(png_bytes, page_idx)
    
    doc.close()


if __name__ == "__main__":
    main()
