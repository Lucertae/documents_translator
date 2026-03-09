#!/usr/bin/env python3
"""
Regression test: translate one page from key PDFs and measure quality.

This script:
1. Translates page 0 of selected test documents (en → it)
2. Measures link preservation, image preservation, y-span ratio
3. Saves before/after PDFs for visual comparison
4. Prints a summary report

Usage:
    python3 test_regression_translate.py [--file PATTERN] [--page N]
"""
import sys
import os
import time
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

from pathlib import Path
import pymupdf

OUTPUT_DIR = Path("output/regression_test")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Key test files covering different features
TEST_FILES = [
    # Has links, good body text
    ("input/Coates_825.pdf", 1, "Academic paper with links"),
    # Has lists, footnotes, mixed formatting
    ("input/confidenziali/2025-04-30 Physitek Letter [4].pdf", 0, "Letter with lists and links"),
    # Has tables
    ("input/confidenziali/[2003] MCS TS PAI_Sirio Analtix srl_ DA & AM1 (IND) - FE [2020-Evergreen].pdf", 0, "Contract with tables"),
    # Complex academic layout
    ("input/The-World-Bank-economic-review-30-1.pdf", 1, "Journal with columns"),
    # ISO standard with indentation 
    ("input/ISO-128-1-2020.pdf", 0, "ISO standard with structure"),
    # Thesis with mixed formatting
    ("input/DI_PAOLO_THESIS.pdf", 1, "Thesis with body text"),
]


def translate_page(pdf_path: str, page_num: int) -> tuple:
    """
    Translate a page using the current pipeline.
    Returns (orig_page_bytes, translated_page_bytes, stats_dict) or (None, None, None).
    """
    from app.core.pdf_processor import PDFProcessor
    from app.core.translator import TranslationEngine
    
    try:
        processor = PDFProcessor(pdf_path)
        if page_num >= processor.page_count:
            print(f"  ⚠️  Page {page_num} out of range (max {processor.page_count - 1})")
            processor.close()
            return None, None, None
        
        translator = TranslationEngine("en", "it")
        
        t0 = time.time()
        translated_doc = processor.translate_page(
            page_num,
            translator,
            text_color=(0, 0, 0),
            use_original_color=True,
            preserve_font_style=True,
            preserve_line_breaks=True,
            ocr_language="en"
        )
        elapsed = time.time() - t0
        
        if not translated_doc:
            processor.close()
            return None, None, None
        
        translated_bytes = translated_doc.tobytes()
        
        # Get original page
        orig_doc = pymupdf.open()
        orig_doc.insert_pdf(processor.document, from_page=page_num, to_page=page_num)
        orig_bytes = orig_doc.tobytes()
        
        # Compare
        orig_page = orig_doc[0]
        trans_page = translated_doc[0]
        
        orig_links = orig_page.get_links()
        trans_links = trans_page.get_links()
        orig_images = orig_page.get_images()
        trans_images = trans_page.get_images()
        
        # y-span analysis
        def get_y_stats(page):
            d = page.get_text("dict")
            y_positions = []
            for b in d.get("blocks", []):
                if "lines" not in b:
                    continue
                for line in b.get("lines", []):
                    for span in line.get("spans", []):
                        if span.get("text", "").strip():
                            y_positions.append(span["bbox"][1])
            if y_positions:
                return min(y_positions), max(y_positions), len(y_positions)
            return 0, 0, 0
        
        orig_ymin, orig_ymax, orig_spans = get_y_stats(orig_page)
        trans_ymin, trans_ymax, trans_spans = get_y_stats(trans_page)
        
        stats = {
            'elapsed': elapsed,
            'links_orig': len(orig_links),
            'links_trans': len(trans_links),
            'images_orig': len(orig_images),
            'images_trans': len(trans_images),
            'orig_y_range': (orig_ymin, orig_ymax),
            'trans_y_range': (trans_ymin, trans_ymax),
            'orig_span_count': orig_spans,
            'trans_span_count': trans_spans,
        }
        
        orig_doc.close()
        translated_doc.close()
        processor.close()
        
        return orig_bytes, translated_bytes, stats
        
    except Exception as e:
        logging.error(f"Translation failed: {e}", exc_info=True)
        return None, None, None


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=str, default=None)
    parser.add_argument("--page", type=int, default=None)
    args = parser.parse_args()
    
    results = []
    
    for pdf_path, default_page, description in TEST_FILES:
        if args.file and args.file not in pdf_path:
            continue
        
        page_num = args.page if args.page is not None else default_page
        
        if not os.path.exists(pdf_path):
            print(f"❌ SKIP {pdf_path} (not found)")
            continue
        
        print(f"\n{'─'*60}")
        print(f"📄 {description}")
        print(f"   {pdf_path} [page {page_num}]")
        
        orig_bytes, trans_bytes, stats = translate_page(pdf_path, page_num)
        
        if orig_bytes and trans_bytes and stats:
            stem = Path(pdf_path).stem
            out_orig = OUTPUT_DIR / f"{stem}_p{page_num}_orig.pdf"
            out_trans = OUTPUT_DIR / f"{stem}_p{page_num}_trans.pdf"
            out_orig.write_bytes(orig_bytes)
            out_trans.write_bytes(trans_bytes)
            
            # Report
            print(f"   ⏱️  Time: {stats['elapsed']:.1f}s")
            print(f"   🔗 Links: {stats['links_orig']} → {stats['links_trans']} {'✅' if stats['links_trans'] >= stats['links_orig'] else '⚠️  LOST ' + str(stats['links_orig'] - stats['links_trans'])}")
            print(f"   🖼️  Images: {stats['images_orig']} → {stats['images_trans']} {'✅' if stats['images_trans'] >= stats['images_orig'] else '⚠️  LOST ' + str(stats['images_orig'] - stats['images_trans'])}")
            
            orig_y_range = stats['orig_y_range'][1] - stats['orig_y_range'][0]
            trans_y_range = stats['trans_y_range'][1] - stats['trans_y_range'][0]
            y_ratio = trans_y_range / orig_y_range if orig_y_range > 0 else 0
            print(f"   📐 Y-range: {orig_y_range:.0f} → {trans_y_range:.0f} (ratio: {y_ratio:.2f}) {'✅' if 0.8 <= y_ratio <= 1.3 else '⚠️  BAD'}")
            print(f"   💾 Saved: {out_orig.name}, {out_trans.name}")
            
            results.append({
                'file': description,
                'links_ok': stats['links_trans'] >= stats['links_orig'],
                'images_ok': stats['images_trans'] >= stats['images_orig'],
                'y_ratio': y_ratio,
                'time': stats['elapsed'],
            })
        else:
            print(f"   ❌ Translation failed")
            results.append({'file': description, 'links_ok': False, 'images_ok': False, 'y_ratio': 0, 'time': 0})
    
    # Summary
    print(f"\n{'='*60}")
    print("REGRESSION SUMMARY")
    print(f"{'='*60}")
    
    total = len(results)
    links_pass = sum(1 for r in results if r['links_ok'])
    images_pass = sum(1 for r in results if r['images_ok'])
    y_pass = sum(1 for r in results if 0.8 <= r['y_ratio'] <= 1.3)
    
    print(f"  Links preserved:  {links_pass}/{total}")
    print(f"  Images preserved: {images_pass}/{total}")
    print(f"  Y-range OK:       {y_pass}/{total}")
    print(f"  Avg time:         {sum(r['time'] for r in results)/total:.1f}s" if total else "")
    
    for r in results:
        status = "✅" if r['links_ok'] and r['images_ok'] and 0.8 <= r['y_ratio'] <= 1.3 else "⚠️ "
        print(f"  {status} {r['file']}: y_ratio={r['y_ratio']:.2f}, time={r['time']:.1f}s")


if __name__ == "__main__":
    main()
