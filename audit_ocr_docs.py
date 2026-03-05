#!/usr/bin/env python3
"""Comprehensive audit of all OCR documents through the translation pipeline."""
import os
import sys
import time
import json
import logging

os.environ['MINERU_DEVICE_MODE'] = 'cpu'
logging.basicConfig(level=logging.WARNING, format='%(message)s')

import pymupdf

# ──────────────────────────────────────────────────
# PHASE 1: Identify all scanned documents
# ──────────────────────────────────────────────────
print("=" * 80)
print("PHASE 1: Document Audit — Identifying scanned pages")
print("=" * 80)

input_dirs = ['input', 'input/confidenziali']
pdfs = []
for d in input_dirs:
    if os.path.exists(d):
        for f in sorted(os.listdir(d)):
            if f.endswith('.pdf'):
                pdfs.append(os.path.join(d, f))

scanned_docs = []  # (path, [page_indices])

for pdf_path in pdfs:
    doc = pymupdf.open(pdf_path)
    scanned = []
    for i in range(doc.page_count):
        page = doc[i]
        imgs = page.get_images(full=True)
        text = page.get_text('text')
        words = len(text.split())
        pa = page.rect.width * page.rect.height
        ia = 0
        for img in imgs:
            try:
                for r in page.get_image_rects(img[0]):
                    ia += r.width * r.height
            except:
                pass
        cov = ia / pa if pa > 0 else 0
        s = ((len(imgs) >= 1 and cov > 0.5 and words < 10)
             or (cov > 0.7 and words < 20)
             or (cov > 0.9)
             or (len(text.strip()) < 5 and len(imgs) > 0))
        if s:
            scanned.append(i)
    n = doc.page_count
    doc.close()
    bn = os.path.basename(pdf_path)[:60]
    if scanned:
        ps = [p + 1 for p in scanned[:8]]
        extra = f"...(+{len(scanned) - 8})" if len(scanned) > 8 else ""
        print(f"  SCAN  {bn}  {len(scanned)}/{n}  pages={ps}{extra}")
        scanned_docs.append((pdf_path, scanned))
    else:
        print(f"  TEXT  {bn}  0/{n}")

print(f"\nTotal: {len(scanned_docs)} documents with scanned pages")
print()

# ──────────────────────────────────────────────────
# PHASE 2: RapidDoc extraction quality audit
# ──────────────────────────────────────────────────
print("=" * 80)
print("PHASE 2: RapidDoc Extraction Quality Audit")
print("=" * 80)

from app.core.rapid_doc_engine import RapidDocEngine
engine = RapidDocEngine()

if not engine.is_available():
    print("ERROR: RapidDoc not available!")
    sys.exit(1)

# Test representative pages from each scanned document
# Pick 1-2 pages per doc: first scanned + a body page
results = []

for pdf_path, scanned_pages in scanned_docs:
    bn = os.path.basename(pdf_path)[:50]
    with open(pdf_path, 'rb') as f:
        pdf_bytes = f.read()

    # Pick test pages: first page + a body page (if available)
    test_pages = [scanned_pages[0]]
    if len(scanned_pages) > 3:
        # Pick a body page (3rd scanned page, likely has more text)
        test_pages.append(scanned_pages[min(2, len(scanned_pages) - 1)])

    for pg in test_pages:
        print(f"\n--- {bn} page {pg + 1} ---")
        try:
            md, meta = engine.extract_page_markdown(pdf_bytes, page_num=pg)

            # Parse elements
            from app.core.pdf_processor import PDFProcessor
            elements = PDFProcessor._parse_rapiddoc_markdown(md)

            n_headings = sum(1 for e in elements if e['type'] == 'heading')
            n_paras = sum(1 for e in elements if e['type'] == 'paragraph')
            n_tables = sum(1 for e in elements if e['type'] == 'table')
            total_words = sum(len(e['text'].split()) for e in elements)

            print(f"  Chars: {len(md)}  Elements: {len(elements)} "
                  f"(H:{n_headings} P:{n_paras} T:{n_tables})  "
                  f"Words: {total_words}  Time: {meta['elapsed']:.1f}s")

            # Show first few elements
            for i, e in enumerate(elements[:6]):
                preview = e['text'][:75].replace('\n', ' ')
                if len(e['text']) > 75:
                    preview += '...'
                print(f"    [{e['type'][0].upper()}{e.get('level', '')}] {preview}")
            if len(elements) > 6:
                print(f"    ... +{len(elements) - 6} more")

            # Quality checks
            issues = []
            if total_words < 5 and len(md) > 20:
                issues.append("LOW_WORDS: very few words extracted")
            if n_headings == 0 and n_paras == 0:
                issues.append("NO_CONTENT: no headings or paragraphs")
            if len(md) < 20:
                issues.append("EMPTY: almost no content extracted")

            # Check for garbled text (non-latin chars in what should be latin text)
            import re
            non_latin = len(re.findall(r'[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff]', md))
            if non_latin > 5:
                issues.append(f"CJK_CHARS: {non_latin} CJK characters in supposedly Latin text")

            if issues:
                print(f"  ⚠ ISSUES: {'; '.join(issues)}")
            else:
                print(f"  ✓ OK")

            results.append({
                'file': bn,
                'page': pg + 1,
                'chars': len(md),
                'elements': len(elements),
                'words': total_words,
                'headings': n_headings,
                'paragraphs': n_paras,
                'tables': n_tables,
                'time': meta['elapsed'],
                'issues': issues,
                'md_preview': md[:300],
            })

        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            results.append({
                'file': bn,
                'page': pg + 1,
                'error': str(e),
            })

# ──────────────────────────────────────────────────
# PHASE 3: Translation completeness test
# ──────────────────────────────────────────────────
print("\n" + "=" * 80)
print("PHASE 3: Translation Completeness (Mock Translator)")
print("=" * 80)

from app.core.pdf_processor import PDFProcessor

class CountingTranslator:
    """Translator that tracks what gets translated."""
    def __init__(self):
        self.calls = []

    def translate(self, text):
        self.calls.append(text)
        return f"[TR] {text}"

# Test on a representative body page from each scanned doc
for pdf_path, scanned_pages in scanned_docs:
    bn = os.path.basename(pdf_path)[:50]

    # Pick a body page (not just the cover)
    if len(scanned_pages) > 2:
        test_pg = scanned_pages[2]  # 3rd scanned page
    elif len(scanned_pages) > 1:
        test_pg = scanned_pages[1]
    else:
        test_pg = scanned_pages[0]

    print(f"\n--- {bn} page {test_pg + 1} ---")
    proc = PDFProcessor(pdf_path)
    translator = CountingTranslator()

    try:
        t0 = time.time()
        result_doc = proc.translate_page(test_pg, translator)
        elapsed = time.time() - t0

        result_text = result_doc[0].get_text('text')

        # Count [TR] markers in output
        tr_count = result_text.count('[TR]')

        # Count words in source (from RapidDoc extraction)
        with open(pdf_path, 'rb') as f:
            pdf_bytes = f.read()
        try:
            md, _ = engine.extract_page_markdown(pdf_bytes, page_num=test_pg)
            source_words = len(md.split())
        except:
            source_words = -1

        # Check completeness
        output_words = len(result_text.split())
        total_source_chars = sum(len(c) for c in translator.calls)
        print(f"  Translator calls: {len(translator.calls)} | Source chars: {total_source_chars}")
        print(f"  Output: {len(result_text)} chars, {output_words} words, {tr_count} [TR] markers")
        print(f"  Time: {elapsed:.1f}s")

        if tr_count == 0 and output_words > 0:
            print(f"  ⚠ NO_TR_MARKERS: text present but no [TR] markers — translation may not be applied")
        elif tr_count < len(translator.calls):
            print(f"  ⚠ INCOMPLETE: {tr_count}/{len(translator.calls)} elements visible (page overflow?)")
        else:
            print(f"  ✓ COMPLETE: all {tr_count} elements translated and visible")

        # Show preview
        preview = result_text[:300].replace('\n', ' | ')
        print(f"  Preview: {preview}...")

        result_doc.close()

    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        proc.close()

# ──────────────────────────────────────────────────
# Summary
# ──────────────────────────────────────────────────
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

total_ok = sum(1 for r in results if not r.get('issues') and not r.get('error'))
total_issues = sum(1 for r in results if r.get('issues'))
total_errors = sum(1 for r in results if r.get('error'))

print(f"  Pages tested: {len(results)}")
print(f"  OK: {total_ok}  |  Issues: {total_issues}  |  Errors: {total_errors}")

if total_issues > 0 or total_errors > 0:
    print("\n  Problems found:")
    for r in results:
        if r.get('issues') or r.get('error'):
            label = r['file'] + f" p{r['page']}"
            if r.get('error'):
                print(f"    ✗ {label}: ERROR — {r['error']}")
            else:
                print(f"    ⚠ {label}: {'; '.join(r['issues'])}")
