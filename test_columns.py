#!/usr/bin/env python3
"""Test Story API multi-column approach."""
import pymupdf

html = """
<h2>Column Test Heading</h2>
<p>This is the first paragraph that should appear in the left column. It contains quite a lot of text to demonstrate the column flow behavior of the Story API in PyMuPDF.</p>
<p>Second paragraph with more text. The content should flow naturally from the left column to the right column when the left column fills up.</p>
<h3>Another Section</h3>
<p>Third paragraph. When text overflows the left column rectangle, it should continue in the right column rectangle. This is how multi-column layouts work in PyMuPDF.</p>
<p>Fourth paragraph with additional content. The Story API manages flowing text across multiple rectangles automatically, which is exactly what we need for newspaper-style 2-column layouts.</p>
<p>Fifth paragraph to ensure we have enough content to fill both columns visually.</p>
<p>Sixth paragraph. More text here.</p>
<p>Seventh and final paragraph with the remaining content that should overflow into the second column for a nice visual layout.</p>
"""

css = """
* { font-family: Helvetica, sans-serif; margin: 0; padding: 0; }
p { font-size: 10pt; line-height: 1.2; margin-top: 2pt; margin-bottom: 2pt; text-align: justify; }
h2 { font-size: 14pt; font-weight: bold; margin-top: 6pt; margin-bottom: 3pt; }
h3 { font-size: 12pt; font-weight: bold; margin-top: 5pt; margin-bottom: 2pt; }
"""

# Page dimensions similar to Economist
page_w, page_h = 724, 984
margin = 30
gap = 15

col_w = (page_w - 2*margin - gap) / 2
left_rect = pymupdf.Rect(margin, margin, margin + col_w, page_h - margin)
right_rect = pymupdf.Rect(margin + col_w + gap, margin, page_w - margin, page_h - margin)

mediabox = pymupdf.Rect(0, 0, page_w, page_h)

print(f"Left col: {left_rect}")
print(f"Right col: {right_rect}")

# Use Story.write_with_links to get a PDF Document directly
story = pymupdf.Story(html=html, user_css=css)

def rectfn(rect_num, filled):
    if rect_num == 0:
        return (mediabox, left_rect, None)   # new page, left column
    elif rect_num == 1:
        return (None, right_rect, None)       # same page, right column
    else:
        return (None, None, None)             # stop

temp_doc = story.write_with_links(rectfn)
print(f"Temp doc pages: {temp_doc.page_count}")

# Check word positions
page = temp_doc[0]
words = page.get_text('words')
mid = page_w / 2
left_words = [w for w in words if w[2] < mid]
right_words = [w for w in words if w[0] > mid]
print(f"Left column words: {len(left_words)}")
print(f"Right column words: {len(right_words)}")

# Now overlay onto output page
out_doc = pymupdf.open()
out_page = out_doc.new_page(width=page_w, height=page_h)
out_page.draw_rect(out_page.rect, color=(1,1,1), fill=(1,1,1))
out_page.show_pdf_page(out_page.rect, temp_doc, 0)

# Check text preserved
out_words = out_page.get_text('words')
print(f"Output words: {len(out_words)}")
print(f"  Left: {sum(1 for w in out_words if w[2] < mid)}")
print(f"  Right: {sum(1 for w in out_words if w[0] > mid)}")

out_doc.save("output/visual_check/column_test.pdf")
print("Saved: output/visual_check/column_test.pdf")
out_doc.close()
temp_doc.close()
