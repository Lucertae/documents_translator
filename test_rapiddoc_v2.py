#!/usr/bin/env python3
"""Test RapidDoc with optimized OCR config for English/Italian documents."""

import os
import sys
import time
import copy
import json
from pathlib import Path

os.environ['MINERU_DEVICE_MODE'] = "cpu"

from rapid_doc.cli.common import convert_pdf_bytes_to_bytes_by_pypdfium2
from rapid_doc.backend.pipeline.pipeline_analyze import doc_analyze as pipeline_doc_analyze
from rapid_doc.backend.pipeline.pipeline_middle_json_mkcontent import union_make as pipeline_union_make
from rapid_doc.backend.pipeline.model_json_to_middle_json import result_to_middle_json as pipeline_result_to_middle_json
from rapid_doc.data.data_reader_writer import FileBasedDataWriter
from rapid_doc.utils.enum_class import MakeMode
from rapidocr import LangRec, OCRVersion, ModelType as OCRModelType


def extract_page_markdown(pdf_path: str, page_num: int = 0, parse_method: str = 'auto') -> tuple:
    """
    Extract markdown from a single PDF page using RapidDoc.
    
    Returns: (markdown_str, content_list, elapsed_seconds)
    """
    with open(pdf_path, 'rb') as f:
        pdf_bytes = f.read()
    
    new_pdf_bytes = convert_pdf_bytes_to_bytes_by_pypdfium2(pdf_bytes, page_num, page_num)
    
    # Optimized OCR config for English/Italian documents
    ocr_config = {
        # Use LATIN recognition for proper English/Italian text
        "Rec.lang_type": LangRec.LATIN,
        "Rec.ocr_version": OCRVersion.PPOCRV4,
        "Rec.model_type": OCRModelType.SERVER,
        # Detection: keep PP-OCRv5 CH mobile (best general-purpose det)
        "Det.box_thresh": 0.6,  # Our tuned threshold
    }
    
    t0 = time.time()
    
    infer_results, all_image_lists, all_page_dicts, lang_list, ocr_enabled_list = pipeline_doc_analyze(
        [new_pdf_bytes],
        parse_method=parse_method,
        formula_enable=False,
        table_enable=True,
        ocr_config=ocr_config,
    )
    
    model_list = infer_results[0]
    images_list = all_image_lists[0]
    pdf_dict = all_page_dicts[0]
    _lang = lang_list[0]
    _ocr_enable = ocr_enabled_list[0]
    
    output_dir = "/tmp/rapiddoc_test"
    os.makedirs(output_dir, exist_ok=True)
    image_writer = FileBasedDataWriter(output_dir)
    
    middle_json = pipeline_result_to_middle_json(
        model_list, images_list, pdf_dict, image_writer,
        _lang, _ocr_enable, False
    )
    
    pdf_info = middle_json["pdf_info"]
    md_content = pipeline_union_make(pdf_info, MakeMode.MM_MD, "images")
    content_list = pipeline_union_make(pdf_info, MakeMode.CONTENT_LIST, "images")
    
    elapsed = time.time() - t0
    return md_content, content_list, elapsed, _lang, _ocr_enable


def test_page(pdf_path, page, desc=""):
    print(f"\n{'='*70}")
    print(f"[{desc}] {os.path.basename(pdf_path)} p{page+1}")
    print(f"{'='*70}")
    
    try:
        md, content, elapsed, lang, ocr_en = extract_page_markdown(pdf_path, page)
        print(f"Lang={lang} OCR={ocr_en} Time={elapsed:.1f}s Chars={len(md)}")
        print(f"\n--- MARKDOWN ---")
        print(md[:2000])
        if len(md) > 2000:
            print(f"\n... [{len(md)-2000} more chars]")
        return md, elapsed
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return "", 0


def main():
    base = "/home/bracco/documents_translator/input"
    conf = f"{base}/confidenziali"
    
    tests = [
        (f"{conf}/Signed_FY2025_2027_Authorized_Distribution_Agreement_Distributor.pdf", 2, "Contract body"),
        (f"{conf}/Signed_FY2025_2027_Authorized_Distribution_Agreement_Distributor.pdf", 0, "Contract cover"),
        (f"{conf}/DOC040625-04062025140056.pdf", 0, "Scanned cover"),
        (f"{base}/sim_quarterly-journal-of-economics_1980_94_contents.pdf", 0, "Academic TOC"),
        (f"{conf}/Distribution Contract Trotec Bompan SRL_01062024_signed both parties.pdf", 1, "Trotec contract body"),
    ]
    
    results = []
    for path, page, desc in tests:
        md, t = test_page(path, page, desc)
        results.append((desc, len(md), t))
    
    print(f"\n\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    for desc, chars, t in results:
        print(f"  {desc:<30} {chars:>6} chars  {t:>5.1f}s")


if __name__ == '__main__':
    main()
