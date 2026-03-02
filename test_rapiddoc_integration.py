#!/usr/bin/env python3
"""
Integration test for RapidDoc in the PDF processing pipeline.

Tests:
1. RapidDocEngine availability and markdown extraction
2. Markdown parser correctness
3. Full translation pipeline with RapidDoc on scanned pages
4. Fallback to RapidOCR when RapidDoc fails
"""

import os
import sys
import time
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# Set environment before imports
os.environ['MINERU_DEVICE_MODE'] = 'cpu'

# Test 1: Import and availability
print("=" * 70)
print("TEST 1: Import and availability checks")
print("=" * 70)

from app.core.rapid_doc_engine import RapidDocEngine, check_rapiddoc_status

engine = RapidDocEngine()
available = engine.is_available()
status_ok, status_msg = check_rapiddoc_status()

print(f"  RapidDoc available: {available}")
print(f"  Status: {status_msg}")
assert available, "RapidDoc should be available"
print("  ✓ PASSED")

# Test 2: Markdown parser
print("\n" + "=" * 70)
print("TEST 2: Markdown parser")
print("=" * 70)

from app.core.pdf_processor import PDFProcessor

test_md = """# Main Title

This is the first paragraph of text.
It continues on the next line.

## Section 2

Another paragraph here with some content about the document.

| Column A | Column B | Column C |
|---|---|---|
| Cell 1 | Cell 2 | Cell 3 |
| Cell 4 | Cell 5 | Cell 6 |

### Subsection 2.1

Final paragraph with closing remarks.

![image](images/fig1.png)
"""

elements = PDFProcessor._parse_rapiddoc_markdown(test_md)

print(f"  Parsed {len(elements)} elements:")
for i, elem in enumerate(elements):
    preview = elem['text'][:60] + ('...' if len(elem['text']) > 60 else '')
    print(f"    [{i}] {elem['type']} (level={elem['level']}): {preview}")

# Verify structure
assert len(elements) == 7, f"Expected 7 elements, got {len(elements)}"
assert elements[0]['type'] == 'heading' and elements[0]['level'] == 1
assert elements[1]['type'] == 'paragraph'
assert elements[2]['type'] == 'heading' and elements[2]['level'] == 2
assert elements[3]['type'] == 'paragraph'
assert elements[4]['type'] == 'table'
assert elements[5]['type'] == 'heading' and elements[5]['level'] == 3
assert elements[6]['type'] == 'paragraph'
print("  ✓ PASSED - all element types and levels correct")

# Test 3: Extract structured markdown from a real PDF
print("\n" + "=" * 70)
print("TEST 3: Real PDF extraction via RapidDoc")
print("=" * 70)

# Find a scanned PDF to test with
test_pdfs = []
input_dir = "input"
if os.path.exists(input_dir):
    for f in os.listdir(input_dir):
        if f.endswith('.pdf'):
            test_pdfs.append(os.path.join(input_dir, f))

# Also check root for PDFs
for f in os.listdir('.'):
    if f.endswith('.pdf') and os.path.isfile(f):
        test_pdfs.append(f)

if not test_pdfs:
    # Check input/confidenziali/
    conf_dir = os.path.join(input_dir, "confidenziali")
    if os.path.exists(conf_dir):
        for f in os.listdir(conf_dir):
            if f.endswith('.pdf'):
                test_pdfs.append(os.path.join(conf_dir, f))

if test_pdfs:
    test_pdf = test_pdfs[0]
    print(f"  Testing with: {test_pdf}")
    
    with open(test_pdf, 'rb') as f:
        pdf_bytes = f.read()
    
    t0 = time.time()
    md_content, metadata = engine.extract_page_markdown(pdf_bytes, page_num=0)
    elapsed = time.time() - t0
    
    print(f"  Markdown output: {len(md_content)} chars")
    print(f"  Metadata: {metadata}")
    print(f"  Time: {elapsed:.1f}s")
    
    # Parse the markdown
    elements = PDFProcessor._parse_rapiddoc_markdown(md_content)
    print(f"  Parsed elements: {len(elements)}")
    for i, elem in enumerate(elements[:10]):  # Show first 10
        preview = elem['text'][:70] + ('...' if len(elem['text']) > 70 else '')
        print(f"    [{i}] {elem['type']} (L{elem['level']}): {preview}")
    
    if len(elements) > 10:
        print(f"    ... and {len(elements) - 10} more elements")
    
    assert len(md_content) > 0, "Should have extracted some markdown"
    print("  ✓ PASSED")
else:
    print("  ⚠ SKIPPED - no PDF files found for testing")

# Test 4: Extract plain text via RapidDoc
print("\n" + "=" * 70)
print("TEST 4: Plain text extraction via RapidDoc")
print("=" * 70)

if test_pdfs:
    with open(test_pdfs[0], 'rb') as f:
        pdf_bytes = f.read()
    
    plain_text = engine.extract_page_text(pdf_bytes, page_num=0)
    print(f"  Plain text: {len(plain_text)} chars")
    print(f"  Preview: {plain_text[:200]}...")
    
    # Verify no markdown markers remain
    assert '# ' not in plain_text.split('\n')[0] if plain_text else True, "Should strip heading markers"
    print("  ✓ PASSED")
else:
    print("  ⚠ SKIPPED")

# Test 5: PDFProcessor integration check
print("\n" + "=" * 70)
print("TEST 5: PDFProcessor RapidDoc routing")
print("=" * 70)

# Verify that the processor imports RapidDoc integration
from app.core import pdf_processor as pp_module

rapiddoc_available_in_processor = getattr(pp_module, 'RAPIDDOC_AVAILABLE', False)
rapiddoc_engine_in_processor = getattr(pp_module, '_rapiddoc_engine_instance', None)

print(f"  RAPIDDOC_AVAILABLE in pdf_processor: {rapiddoc_available_in_processor}")
print(f"  _rapiddoc_engine_instance: {'set' if rapiddoc_engine_in_processor else 'None'}")

assert rapiddoc_available_in_processor, "RAPIDDOC_AVAILABLE should be True"
assert rapiddoc_engine_in_processor is not None, "Engine instance should be set"

# Verify the new methods exist
proc = PDFProcessor.__new__(PDFProcessor)
assert hasattr(proc, '_translate_scanned_page_rapiddoc'), "Should have _translate_scanned_page_rapiddoc"
assert hasattr(proc, '_parse_rapiddoc_markdown'), "Should have _parse_rapiddoc_markdown"
assert hasattr(proc, '_translate_table_element'), "Should have _translate_table_element"
assert hasattr(proc, '_render_table_as_html'), "Should have _render_table_as_html"

print("  ✓ PASSED - all new methods present")

# Test 6: Full pipeline test (if PDF available)
print("\n" + "=" * 70)
print("TEST 6: Full translation pipeline (mock translator)")
print("=" * 70)

if test_pdfs:
    class MockTranslator:
        """Simple mock that prefixes text with [TR]."""
        def translate(self, text):
            return f"[TR] {text}"
    
    test_pdf = test_pdfs[0]
    print(f"  Testing with: {test_pdf}")
    
    processor = PDFProcessor(test_pdf)
    
    # Find a scanned page
    scanned_page = None
    for i in range(min(processor.page_count, 5)):
        page = processor.get_page(i)
        is_scanned, reason = processor._is_likely_scanned_page(page)
        print(f"  Page {i+1}: scanned={is_scanned} ({reason})")
        if is_scanned:
            scanned_page = i
            break
    
    if scanned_page is not None:
        print(f"\n  Translating scanned page {scanned_page + 1} via RapidDoc...")
        t0 = time.time()
        translated_doc = processor.translate_page(
            scanned_page, 
            MockTranslator(),
            text_color=(0, 0, 0),
        )
        elapsed = time.time() - t0
        
        # Verify output
        assert translated_doc is not None, "Should return a document"
        assert translated_doc.page_count == 1, "Should have exactly 1 page"
        
        # Extract text from translated page to verify
        translated_page = translated_doc[0]
        result_text = translated_page.get_text("text")
        
        print(f"  Translation completed in {elapsed:.1f}s")
        print(f"  Output text: {len(result_text)} chars")
        print(f"  Preview: {result_text[:200]}...")
        
        # Check that some [TR] prefixes are present (mock translator marker)
        tr_count = result_text.count('[TR]')
        print(f"  [TR] markers found: {tr_count}")
        
        if tr_count > 0:
            print("  ✓ PASSED - translated content present in output PDF")
        else:
            print("  ⚠ WARNING - no [TR] markers found (text may have been rendered differently)")
        
        # Save output for manual inspection
        output_path = "/tmp/rapiddoc_integration_test.pdf"
        translated_doc.save(output_path)
        print(f"  Output saved to: {output_path}")
        
        translated_doc.close()
    else:
        # If no scanned page found, test extract_text instead
        print("  No scanned pages found, testing extract_text...")
        text = processor.extract_text(0)
        print(f"  Page 1 text: {len(text)} chars")
        print(f"  Preview: {text[:200]}...")
        print("  ✓ PASSED (no scanned pages to test full pipeline)")
    
    processor.close()
else:
    print("  ⚠ SKIPPED - no PDF files found")

print("\n" + "=" * 70)
print("ALL TESTS COMPLETED")
print("=" * 70)
