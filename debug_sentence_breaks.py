"""
Debug script to analyze text block extraction from DI_PAOLO_THESIS.pdf
Focuses on page 2 to understand line breaking and sentence context issues.
"""
import pymupdf
from pathlib import Path

PDF_PATH = Path("input/DI_PAOLO_THESIS.pdf")
PAGE_NUM = 1  # 0-indexed, so page 2

def analyze_page_blocks(pdf_path: Path, page_num: int):
    """Analyze how text is extracted and grouped into blocks."""
    doc = pymupdf.open(pdf_path)
    page = doc[page_num]
    
    print("=" * 80)
    print(f"ANALYZING PAGE {page_num + 1} OF {pdf_path.name}")
    print("=" * 80)
    
    # Method 1: Get text as blocks
    print("\n" + "=" * 80)
    print("METHOD 1: get_text('blocks') - Raw block extraction")
    print("=" * 80)
    
    blocks = page.get_text("blocks", flags=pymupdf.TEXT_DEHYPHENATE)
    for i, block in enumerate(blocks):
        if len(block) > 4:
            text = block[4].strip()
            if text and len(text) > 5:
                bbox = block[:4]
                print(f"\n--- BLOCK {i} ---")
                print(f"BBox: x0={bbox[0]:.1f}, y0={bbox[1]:.1f}, x1={bbox[2]:.1f}, y1={bbox[3]:.1f}")
                print(f"Text ({len(text)} chars):")
                # Show line breaks clearly
                lines = text.split('\n')
                for j, line in enumerate(lines):
                    print(f"  Line {j}: [{line}]")
    
    # Method 2: Get detailed dict structure
    print("\n" + "=" * 80)
    print("METHOD 2: get_text('dict') - Detailed structure with lines and spans")
    print("=" * 80)
    
    text_dict = page.get_text("dict")
    for block_idx, block in enumerate(text_dict.get("blocks", [])):
        if "lines" not in block:
            continue
            
        block_bbox = block.get("bbox", [])
        lines = block.get("lines", [])
        
        if not lines:
            continue
            
        # Collect all text from this block
        block_text = ""
        for line in lines:
            line_text = ""
            for span in line.get("spans", []):
                line_text += span.get("text", "")
            block_text += line_text + "\n"
        
        if len(block_text.strip()) < 10:
            continue
            
        print(f"\n{'='*60}")
        print(f"BLOCK {block_idx}")
        print(f"BBox: {block_bbox}")
        print(f"{'='*60}")
        
        for line_idx, line in enumerate(lines):
            line_bbox = line.get("bbox", [])
            spans = line.get("spans", [])
            line_text = "".join([s.get("text", "") for s in spans])
            
            if not line_text.strip():
                continue
                
            # Check if line ends with punctuation (sentence end)
            ends_with_period = line_text.rstrip().endswith('.')
            ends_with_punct = line_text.rstrip()[-1] in '.!?:' if line_text.rstrip() else False
            
            print(f"\n  LINE {line_idx}:")
            print(f"    BBox: y0={line_bbox[1]:.1f}, y1={line_bbox[3]:.1f}")
            print(f"    Text: [{line_text}]")
            print(f"    Ends with period: {ends_with_period}")
            print(f"    Ends with punctuation: {ends_with_punct}")
            
            # Show font info for first span
            if spans:
                span = spans[0]
                print(f"    Font: {span.get('font', 'unknown')}, Size: {span.get('size', 0):.1f}")
    
    # Method 3: Analyze potential sentence breaks
    print("\n" + "=" * 80)
    print("METHOD 3: Analyzing sentence continuity across line breaks")
    print("=" * 80)
    
    # Get full text to see how lines connect
    full_text = page.get_text("text")
    lines = full_text.split('\n')
    
    print("\nPotential mid-sentence line breaks (line doesn't end with .):")
    print("-" * 60)
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line or len(line) < 20:
            continue
            
        # Check if this looks like a mid-sentence break
        if not line.endswith('.') and not line.endswith('!') and not line.endswith('?'):
            if not line.endswith(':') and not line.endswith(';'):
                # This line probably continues on the next line
                next_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
                if next_line and next_line[0].islower():
                    print(f"\n  LINE {i}: [{line}]")
                    print(f"  --> continues to: [{next_line[:60]}...]")
    
    doc.close()


def analyze_translation_blocks(pdf_path: Path, page_num: int):
    """Show how the current translation system would split this page."""
    from app.core.pdf_processor import PDFProcessor
    
    print("\n" + "=" * 80)
    print("CURRENT TRANSLATION BLOCK EXTRACTION")
    print("=" * 80)
    
    processor = PDFProcessor(str(pdf_path), "en")
    doc = pymupdf.open(pdf_path)
    page = doc[page_num]
    
    # Extract blocks the way translation does
    blocks_data = processor.get_translation_blocks(page, page_num)
    
    print(f"\nFound {len(blocks_data)} translation blocks:")
    
    for i, block in enumerate(blocks_data):
        text = block.get('text', '')
        block_type = block.get('type', 'unknown')
        
        print(f"\n{'='*60}")
        print(f"TRANSLATION BLOCK {i} (type: {block_type})")
        print(f"{'='*60}")
        
        # Show how lines are currently grouped
        lines = text.split('\n')
        for j, line in enumerate(lines):
            line = line.strip()
            if line:
                ends_sentence = line[-1] in '.!?' if line else False
                print(f"  {j}: [{line}]")
                if not ends_sentence:
                    print(f"      ^ does NOT end sentence (context may be broken)")
    
    doc.close()


def analyze_block_structure(pdf_path: Path, page_num: int):
    """
    Analyze the BLOCK structure - the key issue is that each line 
    might be a separate block, preventing paragraph grouping.
    """
    doc = pymupdf.open(pdf_path)
    page = doc[page_num]
    
    print("\n" + "=" * 80)
    print("CRITICAL ANALYSIS: Block vs Line Structure")
    print("=" * 80)
    
    text_dict = page.get_text("dict")
    
    blocks_with_multiple_lines = 0
    blocks_with_single_line = 0
    
    for block_idx, block in enumerate(text_dict.get("blocks", [])):
        if "lines" not in block:
            continue
        
        lines = block.get("lines", [])
        if len(lines) == 1:
            blocks_with_single_line += 1
        else:
            blocks_with_multiple_lines += 1
    
    print(f"\nBlocks with SINGLE line: {blocks_with_single_line}")
    print(f"Blocks with MULTIPLE lines: {blocks_with_multiple_lines}")
    print()
    
    if blocks_with_single_line > blocks_with_multiple_lines:
        print("⚠️  PROBLEM DETECTED: Most blocks have only 1 line!")
        print("   This means _group_lines_into_paragraphs cannot work properly")
        print("   because paragraph grouping only works within a block.")
        print()
        print("   SOLUTION: We need to merge adjacent blocks that:")
        print("   1. Have similar font size")
        print("   2. Have similar x position (same column)")
        print("   3. Previous block does NOT end with period (.!?)")
    
    # Show the first few blocks to understand the pattern
    print("\n" + "-" * 60)
    print("First 10 text blocks to show pattern:")
    print("-" * 60)
    
    count = 0
    for block_idx, block in enumerate(text_dict.get("blocks", [])):
        if "lines" not in block:
            continue
        
        lines = block.get("lines", [])
        for line in lines:
            text = "".join(s.get("text", "") for s in line.get("spans", []))
            if text.strip():
                ends_punct = text.strip()[-1] in '.!?' if text.strip() else False
                print(f"Block {block_idx}: [{text[:60]}{'...' if len(text) > 60 else ''}]")
                print(f"          ends_sentence={ends_punct}")
                count += 1
                if count >= 10:
                    break
        if count >= 10:
            break
    
    doc.close()


def propose_merged_paragraphs(pdf_path: Path, page_num: int):
    """
    Propose how blocks should be merged into paragraphs based on:
    - Font size consistency
    - Horizontal alignment
    - Sentence-ending punctuation
    """
    doc = pymupdf.open(pdf_path)
    page = doc[page_num]
    
    print("\n" + "=" * 80)
    print("PROPOSED PARAGRAPH MERGING")
    print("=" * 80)
    
    text_dict = page.get_text("dict")
    
    # Collect all lines from all blocks
    all_lines = []
    for block in text_dict.get("blocks", []):
        if "lines" not in block:
            continue
        for line in block.get("lines", []):
            spans = line.get("spans", [])
            if spans:
                text = "".join(s.get("text", "") for s in spans)
                if text.strip():
                    first_span = spans[0]
                    all_lines.append({
                        'text': text.strip(),
                        'bbox': line.get("bbox", [0,0,0,0]),
                        'font_size': first_span.get("size", 11),
                        'font': first_span.get("font", ""),
                        'is_bold': 'Bold' in first_span.get("font", ""),
                    })
    
    # Now merge consecutive lines that should be in same paragraph
    paragraphs = []
    current_para = [all_lines[0]] if all_lines else []
    
    for i in range(1, len(all_lines)):
        prev = all_lines[i-1]
        curr = all_lines[i]
        
        should_merge = True
        reason = "continue"
        
        # Check 1: Previous line ends with sentence punctuation
        if prev['text'][-1] in '.!?':
            # Check it's not abbreviation
            last_word = prev['text'].split()[-1].rstrip('.!?')
            if len(last_word) > 2:
                should_merge = False
                reason = "sentence_end"
        
        # Check 2: Font size change
        if should_merge:
            size_ratio = curr['font_size'] / prev['font_size'] if prev['font_size'] > 0 else 1
            if size_ratio > 1.15 or size_ratio < 0.85:
                should_merge = False
                reason = f"size_change ({size_ratio:.2f})"
        
        # Check 3: Bold change
        if should_merge:
            if curr['is_bold'] != prev['is_bold']:
                should_merge = False
                reason = "bold_change"
        
        # Check 4: Short title-like line
        if should_merge:
            if len(curr['text']) < 40 and (curr['text'].istitle() or curr['text'].isupper()):
                if curr['text'][-1] not in '.,;':
                    should_merge = False
                    reason = "title_pattern"
        
        if should_merge:
            current_para.append(curr)
        else:
            paragraphs.append((current_para, reason))
            current_para = [curr]
    
    if current_para:
        paragraphs.append((current_para, "end"))
    
    # Show proposed paragraphs
    print(f"\nProposed {len(paragraphs)} paragraphs (vs {len(all_lines)} lines):\n")
    
    for i, (para_lines, end_reason) in enumerate(paragraphs):
        print(f"\n{'='*60}")
        print(f"PARAGRAPH {i+1} ({len(para_lines)} lines) - ends due to: {end_reason}")
        print(f"{'='*60}")
        
        # Show combined text
        full_text = " ".join(l['text'] for l in para_lines)
        print(f"Combined text:\n  {full_text}")
        print()
        
        # Show individual lines
        for j, line in enumerate(para_lines):
            marker = "✓" if line['text'].endswith('.') else "→"
            print(f"  {marker} Line {j}: {line['text'][:70]}{'...' if len(line['text']) > 70 else ''}")
    
    doc.close()


if __name__ == "__main__":
    print("\n" + "#" * 80)
    print("# DI_PAOLO_THESIS.pdf - Page 2 Text Extraction Analysis")
    print("#" * 80)
    
    # First analyze the block structure
    analyze_block_structure(PDF_PATH, PAGE_NUM)
    
    # Then show proposed paragraph merging
    propose_merged_paragraphs(PDF_PATH, PAGE_NUM)
