#!/usr/bin/env python3
"""Test Story API multi-column with real Economist content.
Avoids importing app package to skip transformers/torch deps.
"""
import os, re, html as html_mod
os.environ['MINERU_DEVICE_MODE'] = 'cpu'
import logging
logging.basicConfig(level=logging.WARNING)

import pymupdf

# Import rapid_doc_engine directly (not through app.core)
import importlib.util
spec = importlib.util.spec_from_file_location(
    "rapid_doc_engine",
    "app/core/rapid_doc_engine.py",
    submodule_search_locations=[]
)
rde_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rde_mod)
RapidDocEngine = rde_mod.RapidDocEngine

engine = RapidDocEngine()

# Extract real content
with open('input/sim_economist_1881-08-06_39_1980.pdf', 'rb') as f:
    pdf_bytes = f.read()
md, meta = engine.extract_page_markdown(pdf_bytes, page_num=2)

cols, col_ranges = engine.detect_column_count(meta['block_bboxes'], meta.get('page_size'))
print(f"Detected: {cols} columns, ranges: {col_ranges}")
print(f"Markdown: {len(md)} chars")

# Parse markdown into HTML elements
elements = []
for line in md.split('\n'):
    line = line.strip()
    if not line:
        continue
    m = re.match(r'^(#{1,6})\s+(.*)', line)
    if m:
        level = len(m.group(1))
        elements.append(f'<h{level}>{html_mod.escape(m.group(2))}</h{level}>')
    elif line.startswith('|'):
        pass  # skip table lines for now
    else:
        elements.append(f'<p>{html_mod.escape(line)}</p>')

full_html = '\n'.join(elements)
print(f"HTML elements: {len(elements)}, HTML chars: {len(full_html)}")

# Page dimensions
page_w, page_h = 724.0, 984.0
margin = 30
gap = 15
body_fs = 9.5

css = f"""
* {{ font-family: Helvetica, sans-serif; margin: 0; padding: 0; color: black; }}
p {{ font-size: {body_fs}pt; line-height: 1.15; margin-top: 1.5pt; margin-bottom: 1.5pt; text-align: justify; }}
h1 {{ font-size: {body_fs*1.5}pt; font-weight: bold; margin-top: 5pt; margin-bottom: 2pt; }}
h2 {{ font-size: {body_fs*1.3}pt; font-weight: bold; margin-top: 5pt; margin-bottom: 2pt; }}
h3 {{ font-size: {body_fs*1.15}pt; font-weight: bold; margin-top: 4pt; margin-bottom: 2pt; }}
"""

col_w = (page_w - 2*margin - gap) / 2
left_rect = pymupdf.Rect(margin, margin, margin + col_w, page_h - margin)
right_rect = pymupdf.Rect(margin + col_w + gap, margin, page_w - margin, page_h - margin)
mediabox = pymupdf.Rect(0, 0, page_w, page_h)

print(f"Column width: {col_w:.0f}pt, height: {page_h - 2*margin:.0f}pt")

# Story API with 2-column rects
story = pymupdf.Story(html=full_html, user_css=css)

def rectfn(rect_num, filled):
    if rect_num == 0:
        return (mediabox, left_rect, None)
    elif rect_num == 1:
        return (None, right_rect, None)
    else:
        return (None, None, None)

temp_doc = story.write_with_links(rectfn)
print(f"Temp doc pages: {temp_doc.page_count}")

page = temp_doc[0]
words = page.get_text('words')
mid = page_w / 2
left_w = sum(1 for w in words if w[2] < mid)
right_w = sum(1 for w in words if w[0] > mid)
print(f"Words: {len(words)} total, {left_w} left, {right_w} right")

# Overlay onto clean output page
out_doc = pymupdf.open()
out_page = out_doc.new_page(width=page_w, height=page_h)
out_page.draw_rect(out_page.rect, color=(1,1,1), fill=(1,1,1))
out_page.show_pdf_page(out_page.rect, temp_doc, 0)

out_words = out_page.get_text('words')
print(f"Output words: {len(out_words)}")

out_doc.save("output/visual_check/economist_story_columns.pdf")
out_doc.close()
temp_doc.close()
print("Saved: output/visual_check/economist_story_columns.pdf")
