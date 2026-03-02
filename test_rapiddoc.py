#!/usr/bin/env python3
"""Test RapidDoc on sample documents to evaluate quality."""

import os
import sys
import time
import copy
import json
from pathlib import Path

# CPU mode
os.environ['MINERU_DEVICE_MODE'] = "cpu"

from rapid_doc.cli.common import convert_pdf_bytes_to_bytes_by_pypdfium2
from rapid_doc.backend.pipeline.pipeline_analyze import doc_analyze as pipeline_doc_analyze
from rapid_doc.backend.pipeline.pipeline_middle_json_mkcontent import union_make as pipeline_union_make
from rapid_doc.backend.pipeline.model_json_to_middle_json import result_to_middle_json as pipeline_result_to_middle_json
from rapid_doc.data.data_reader_writer import FileBasedDataWriter
from rapid_doc.utils.enum_class import MakeMode


def test_single_page(pdf_path: str, page_num: int = 0):
    """Test RapidDoc on a single page of a PDF."""
    print(f"\n{'='*70}")
    print(f"Testing: {os.path.basename(pdf_path)}")
    print(f"Page: {page_num + 1}")
    print(f"{'='*70}")
    
    with open(pdf_path, 'rb') as f:
        pdf_bytes = f.read()
    
    # Extract single page
    new_pdf_bytes = convert_pdf_bytes_to_bytes_by_pypdfium2(pdf_bytes, page_num, page_num)
    
    t0 = time.time()
    
    # Run the pipeline
    infer_results, all_image_lists, all_page_dicts, lang_list, ocr_enabled_list = pipeline_doc_analyze(
        [new_pdf_bytes],
        parse_method='auto',
        formula_enable=False,   # Skip formulas for speed
        table_enable=True,
    )
    
    t_analyze = time.time() - t0
    
    # Convert to middle JSON
    model_list = infer_results[0]
    images_list = all_image_lists[0]
    pdf_dict = all_page_dicts[0]
    _lang = lang_list[0]
    _ocr_enable = ocr_enabled_list[0]
    
    # Use a temporary dir for images
    output_dir = "/tmp/rapiddoc_test"
    os.makedirs(output_dir, exist_ok=True)
    image_writer = FileBasedDataWriter(output_dir)
    
    middle_json = pipeline_result_to_middle_json(
        model_list, images_list, pdf_dict, image_writer,
        _lang, _ocr_enable, False
    )
    
    pdf_info = middle_json["pdf_info"]
    
    # Generate Markdown
    md_content = pipeline_union_make(pdf_info, MakeMode.MM_MD, "images")
    
    # Also generate content list for structured inspection
    content_list = pipeline_union_make(pdf_info, MakeMode.CONTENT_LIST, "images")
    
    t_total = time.time() - t0
    
    print(f"\nLanguage detected: {_lang}")
    print(f"OCR enabled: {_ocr_enable}")
    print(f"Analysis time: {t_analyze:.1f}s")
    print(f"Total time: {t_total:.1f}s")
    print(f"\n--- MARKDOWN OUTPUT ({len(md_content)} chars) ---")
    # Print first 3000 chars
    print(md_content[:3000])
    if len(md_content) > 3000:
        print(f"\n... [{len(md_content) - 3000} more chars] ...")
    
    # Show content structure
    if isinstance(content_list, list):
        print(f"\n--- CONTENT STRUCTURE ({len(content_list)} elements) ---")
        for item in content_list[:20]:
            if isinstance(item, dict):
                ctype = item.get('type', '?')
                text = str(item.get('text', ''))[:80]
                print(f"  [{ctype}] {text}")
    
    return md_content, t_total


def main():
    base = "/home/bracco/documents_translator/input"
    
    tests = [
        # Contract (text-based PDF with tables/structure)
        (f"{base}/confidenziali/Signed_FY2025_2027_Authorized_Distribution_Agreement_Distributor.pdf", 0),
        (f"{base}/confidenziali/Signed_FY2025_2027_Authorized_Distribution_Agreement_Distributor.pdf", 2),
        # Scanned document
        (f"{base}/confidenziali/DOC040625-04062025140056.pdf", 0),
        # Academic/structured document
        (f"{base}/sim_quarterly-journal-of-economics_1980_94_contents.pdf", 0),
    ]
    
    results = []
    for pdf_path, page in tests:
        try:
            md, elapsed = test_single_page(pdf_path, page)
            results.append((os.path.basename(pdf_path), page, len(md), elapsed, "OK"))
        except Exception as e:
            print(f"\nERROR: {e}")
            import traceback
            traceback.print_exc()
            results.append((os.path.basename(pdf_path), page, 0, 0, str(e)[:60]))
    
    print(f"\n\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"{'Document':<50} {'Pg':>3} {'Chars':>6} {'Time':>6} {'Status'}")
    print("-" * 80)
    for name, page, chars, t, status in results:
        print(f"{name[:50]:<50} {page+1:>3} {chars:>6} {t:>5.1f}s {status}")


if __name__ == '__main__':
    main()
