#!/usr/bin/env python3
"""Check multi-column detection in RapidDoc output."""
import os
os.environ['MINERU_DEVICE_MODE'] = 'cpu'
import logging
logging.basicConfig(level=logging.WARNING)

from app.core.rapid_doc_engine import RapidDocEngine

engine = RapidDocEngine()

# Test the Economist (known multi-column)
pdf_path = 'input/sim_economist_1881-08-06_39_1980.pdf'
with open(pdf_path, 'rb') as f:
    pdf_bytes = f.read()

# Page 3 (body text, multi-column)
print("=== Economist 1881, page 3 ===")
md, meta = engine.extract_page_markdown(pdf_bytes, page_num=2)
print(f"Content length: {len(md)} chars")
print(f"Elements: {meta['num_elements']}")
print()
print("--- RAW MARKDOWN (first 3000 chars) ---")
print(md[:3000])
print("--- END ---")
print()

# Also look at the raw layout info from RapidDoc
# Check what pdf_info reveals about columns  
import json
from rapid_doc import RapidDoc

# Get the raw result from RapidDoc to inspect layout blocks
try:
    from rapid_doc import RapidDoc as RDClass
    rd = engine._rapiddoc  # Access the internal RapidDoc instance
    # Check type layout detection info
    print("\n=== Layout analysis raw data (page 3) ===")
    
    # Use the lower level to get raw pdf_info
    result = rd(pdf_bytes, page_indexes=[2])
    # result is (md_text, time, pdf_info)
    if len(result) >= 3:
        pdf_info = result[2]
        if isinstance(pdf_info, list):
            # Each element is a page's info
            for pg_info in pdf_info:
                if isinstance(pg_info, dict):
                    # Look for layout blocks with position info
                    for key in pg_info:
                        if key in ('preproc_blocks', 'para_blocks', 'layout_dets'):
                            blocks = pg_info[key]
                            if isinstance(blocks, list):
                                print(f"\n{key}: {len(blocks)} blocks")
                                for i, bl in enumerate(blocks[:10]):
                                    if isinstance(bl, dict):
                                        # Show bbox and type
                                        bbox = bl.get('bbox', bl.get('box', None))
                                        btype = bl.get('type', bl.get('category_id', '?'))
                                        text_preview = str(bl.get('text', ''))[:60]
                                        print(f"  [{i}] type={btype} bbox={bbox} text='{text_preview}'")
                                    else:
                                        print(f"  [{i}] {type(bl).__name__}: {str(bl)[:100]}")
                                if len(blocks) > 10:
                                    print(f"  ... +{len(blocks) - 10} more blocks")
                        elif key == 'page_size':
                            print(f"\npage_size: {pg_info[key]}")
                elif isinstance(pg_info, list):
                    print(f"Page info is a list with {len(pg_info)} items")
                    for i, item in enumerate(pg_info[:5]):
                        print(f"  [{i}] {type(item).__name__}: {str(item)[:200]}")
        else:
            print(f"pdf_info type: {type(pdf_info)}, repr: {str(pdf_info)[:500]}")
    else:
        print(f"Result tuple has {len(result)} elements")

except Exception as e:
    print(f"Error accessing raw layout data: {e}")
    import traceback
    traceback.print_exc()
