#!/usr/bin/env python3
"""Quick check of pdf_info structure returned by RapidDoc."""
import os
os.environ['MINERU_DEVICE_MODE'] = 'cpu'
import logging
logging.basicConfig(level=logging.WARNING)

from app.core.rapid_doc_engine import RapidDocEngine, RAPIDDOC_AVAILABLE
from rapid_doc.cli.common import convert_pdf_bytes_to_bytes_by_pypdfium2
from rapid_doc.backend.pipeline.pipeline_analyze import doc_analyze as pipeline_doc_analyze
from rapid_doc.backend.pipeline.pipeline_middle_json_mkcontent import union_make as pipeline_union_make
from rapid_doc.backend.pipeline.model_json_to_middle_json import result_to_middle_json as pipeline_result_to_middle_json
from rapid_doc.data.data_reader_writer import FileBasedDataWriter
from rapid_doc.utils.enum_class import MakeMode
from rapidocr import LangRec, OCRVersion, ModelType as OCRModelType

engine = RapidDocEngine()
ocr_config = engine._ocr_config

pdf_path = 'input/sim_economist_1881-08-06_39_1980.pdf'
with open(pdf_path, 'rb') as f:
    pdf_bytes = f.read()

page_num = 2  # page 3

single_page_pdf = convert_pdf_bytes_to_bytes_by_pypdfium2(pdf_bytes, page_num, page_num)

infer_results, all_image_lists, all_page_dicts, lang_list, ocr_enabled_list = (
    pipeline_doc_analyze(
        [single_page_pdf],
        parse_method='auto',
        formula_enable=False,
        table_enable=True,
        ocr_config=ocr_config,
    )
)

model_list = infer_results[0]
images_list = all_image_lists[0]
pdf_dict = all_page_dicts[0]
_lang = lang_list[0]
_ocr_enable = ocr_enabled_list[0]

import tempfile
image_writer = FileBasedDataWriter(tempfile.mkdtemp())

middle_json = pipeline_result_to_middle_json(
    model_list, images_list, pdf_dict, image_writer,
    _lang, _ocr_enable, False,
    ocr_config=ocr_config,
)

pdf_info = middle_json["pdf_info"]

# Inspect the structure
print("=== pdf_info structure ===")
print(f"type: {type(pdf_info)}")
if isinstance(pdf_info, list):
    print(f"length: {len(pdf_info)}")
    for i, page_info in enumerate(pdf_info):
        print(f"\n--- Page {i} ---")
        if isinstance(page_info, dict):
            for key in sorted(page_info.keys()):
                val = page_info[key]
                if isinstance(val, list):
                    print(f"  {key}: list[{len(val)}]")
                    for j, item in enumerate(val[:3]):
                        if isinstance(item, dict):
                            print(f"    [{j}] keys={sorted(item.keys())}")
                            # Show bbox if present
                            for k in ('bbox', 'box', 'poly'):
                                if k in item:
                                    print(f"         {k}={item[k]}")
                            # Show type/category
                            for k in ('type', 'category_id', 'category'):
                                if k in item:
                                    print(f"         {k}={item[k]}")
                            # Show text preview
                            if 'text' in item:
                                print(f"         text='{str(item['text'])[:80]}'")
                            # Show lines if present
                            if 'lines' in item and isinstance(item['lines'], list):
                                print(f"         lines: {len(item['lines'])}")
                                for li, line in enumerate(item['lines'][:2]):
                                    if isinstance(line, dict):
                                        line_bbox = line.get('bbox', None)
                                        spans = line.get('spans', [])
                                        spans_text = ' '.join(s.get('content', s.get('text', ''))[:30] for s in spans[:3]) if isinstance(spans, list) else ''
                                        print(f"           line[{li}] bbox={line_bbox} spans={len(spans)} text='{spans_text[:60]}'")
                        else:
                            print(f"    [{j}] {type(item).__name__}: {str(item)[:100]}")
                    if len(val) > 3:
                        print(f"    ... +{len(val) - 3} more")
                elif isinstance(val, dict):
                    print(f"  {key}: dict keys={sorted(val.keys())}")
                else:
                    print(f"  {key}: {type(val).__name__} = {str(val)[:100]}")
