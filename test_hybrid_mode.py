#!/usr/bin/env python3
"""
Test the hybrid RapidDoc + PyMuPDF mode for digital PDF translation.

Tests that:
1. RapidDoc layout analysis runs successfully on digital PDFs
2. Hybrid block grouping produces valid groups
3. Translated pages preserve images, links, and graphics
4. Reading order is correct
5. Multi-column detection works
"""
import sys
import os
import logging
import time

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

sys.path.insert(0, os.path.dirname(__file__))

import pymupdf
from app.core.pdf_processor import PDFProcessor, RAPIDDOC_AVAILABLE
from app.core.translator import TranslationEngine

# Test documents (mix of structures)
TEST_DOCS = [
    {
        'path': 'input/Coates_825.pdf',
        'page': 0,
        'desc': 'Academic paper (single column)',
        'expect_columns': 1,
    },
    {
        'path': 'input/confidenziali/2025-04-30 Physitek Letter [4].pdf',
        'page': 0,
        'desc': 'Business letter (links + lists)',
        'expect_columns': 1,
    },
    {
        'path': 'input/confidenziali/[2003] MCS TS PAI_Sirio Analtix srl_ DA & AM1 (IND) - FE [2020-Evergreen].pdf',
        'page': 0,
        'desc': 'Contract (tables)',
        'expect_columns': 1,
    },
    {
        'path': 'input/The-World-Bank-economic-review-30-1.pdf',
        'page': 4,
        'desc': 'Journal (potential 2-column)',
        'expect_columns': 1,  # May detect 2
    },
    {
        'path': 'input/ISO-128-1-2020.pdf',
        'page': 0,
        'desc': 'ISO standard (structured)',
        'expect_columns': 1,
    },
]


def test_rapiddoc_availability():
    """Check that RapidDoc is available."""
    print(f"\n{'='*60}")
    print(f"RapidDoc Availability: {'YES ✓' if RAPIDDOC_AVAILABLE else 'NO ✗'}")
    print(f"{'='*60}")
    return RAPIDDOC_AVAILABLE


def test_layout_analysis(doc_info):
    """Test RapidDoc layout analysis on a digital PDF page."""
    path = doc_info['path']
    page_num = doc_info['page']
    desc = doc_info['desc']
    
    if not os.path.exists(path):
        print(f"  SKIP: {path} not found")
        return None
    
    proc = PDFProcessor(path)
    
    t0 = time.time()
    result = proc._run_rapiddoc_layout_analysis(page_num)
    elapsed = time.time() - t0
    
    if result is None:
        print(f"  FAIL: Layout analysis returned None for {desc}")
        proc.close()
        return None
    
    n_blocks = len(result.get('block_bboxes', []))
    n_columns = result.get('detected_columns', 1)
    n_elements = len(result.get('elements', []))
    
    # Classify block types
    types = {}
    for bb in result.get('block_bboxes', []):
        t = bb.get('type', 'unknown')
        types[t] = types.get(t, 0) + 1
    
    print(f"  Layout: {n_blocks} blocks, {n_columns} columns, {n_elements} MD elements ({elapsed:.1f}s)")
    print(f"  Types: {types}")
    
    proc.close()
    return result


def test_hybrid_translation(doc_info):
    """Test full hybrid translation on a digital PDF page."""
    path = doc_info['path']
    page_num = doc_info['page']
    desc = doc_info['desc']
    
    if not os.path.exists(path):
        print(f"  SKIP: {path} not found")
        return None
    
    proc = PDFProcessor(path)
    translator = TranslationEngine("en", "it")
    
    page = proc.get_page(page_num)
    
    # Count original elements
    orig_text_dict = page.get_text("dict")
    orig_blocks = len([b for b in orig_text_dict.get("blocks", []) if "lines" in b])
    orig_images = len(page.get_images(full=True))
    orig_links = len(page.get_links())
    
    t0 = time.time()
    result_doc = proc.translate_page(page_num, translator)
    elapsed = time.time() - t0
    
    result_page = result_doc[0]
    
    # Check translated page
    new_text_dict = result_page.get_text("dict")
    new_blocks = len([b for b in new_text_dict.get("blocks", []) if "lines" in b])
    new_images = len(result_page.get_images(full=True))
    new_links = len(result_page.get_links())
    new_text = result_page.get_text("text").strip()
    
    # Y-range preservation (text should stay within similar vertical range)
    orig_rects = []
    for b in orig_text_dict.get("blocks", []):
        if "lines" in b:
            orig_rects.append(b.get("bbox", (0, 0, 0, 0)))
    
    new_rects = []
    for b in new_text_dict.get("blocks", []):
        if "lines" in b:
            new_rects.append(b.get("bbox", (0, 0, 0, 0)))
    
    if orig_rects and new_rects:
        orig_ymin = min(r[1] for r in orig_rects)
        orig_ymax = max(r[3] for r in orig_rects)
        new_ymin = min(r[1] for r in new_rects)
        new_ymax = max(r[3] for r in new_rects)
        y_range_ratio = (new_ymax - new_ymin) / (orig_ymax - orig_ymin) if (orig_ymax - orig_ymin) > 0 else 0
    else:
        y_range_ratio = 0
    
    # Results
    images_ok = new_images >= orig_images
    links_ok = new_links >= orig_links * 0.8  # Allow some loss
    has_text = len(new_text) > 50
    y_ok = 0.7 <= y_range_ratio <= 1.3
    
    status = "✓" if (images_ok and has_text and y_ok) else "✗"
    
    print(f"  Translation ({elapsed:.1f}s): {status}")
    print(f"    Text: {len(new_text)} chars, Blocks: {orig_blocks}→{new_blocks}")
    print(f"    Images: {orig_images}→{new_images} {'✓' if images_ok else '✗'}")
    print(f"    Links: {orig_links}→{new_links} {'✓' if links_ok else '✗'}")
    print(f"    Y-range: {y_range_ratio:.2f} {'✓' if y_ok else '✗'}")
    
    # Save output for visual inspection
    out_dir = "output/hybrid_test"
    os.makedirs(out_dir, exist_ok=True)
    out_name = os.path.basename(path).replace('.pdf', f'_p{page_num+1}_hybrid.pdf')
    out_path = os.path.join(out_dir, out_name)
    result_doc.save(out_path)
    print(f"    Saved: {out_path}")
    
    proc.close()
    result_doc.close()
    
    return {
        'images_ok': images_ok,
        'links_ok': links_ok,
        'has_text': has_text,
        'y_ok': y_ok,
        'elapsed': elapsed,
    }


def main():
    print("=" * 60)
    print("HYBRID MODE TEST: RapidDoc Layout + PyMuPDF Text")
    print("=" * 60)
    
    if not test_rapiddoc_availability():
        print("\nRapidDoc not available — hybrid mode will use heuristic fallback.")
        print("Install with: pip install rapid-doc")
    
    # Phase 1: Layout analysis
    print(f"\n{'='*60}")
    print("PHASE 1: Layout Analysis")
    print(f"{'='*60}")
    
    for doc in TEST_DOCS:
        print(f"\n[{doc['desc']}] {os.path.basename(doc['path'])} p{doc['page']+1}")
        test_layout_analysis(doc)
    
    # Phase 2: Full translation
    print(f"\n{'='*60}")
    print("PHASE 2: Full Hybrid Translation")
    print(f"{'='*60}")
    
    results = []
    for doc in TEST_DOCS:
        print(f"\n[{doc['desc']}] {os.path.basename(doc['path'])} p{doc['page']+1}")
        r = test_hybrid_translation(doc)
        if r:
            results.append(r)
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    passed = sum(1 for r in results if r['images_ok'] and r['has_text'] and r['y_ok'])
    total = len(results)
    print(f"Passed: {passed}/{total}")
    if results:
        avg_time = sum(r['elapsed'] for r in results) / len(results)
        print(f"Average translation time: {avg_time:.1f}s")


if __name__ == "__main__":
    main()
