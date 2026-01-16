"""
Test the cross-block merging on DI_PAOLO_THESIS.pdf page 2
"""
import sys
sys.path.insert(0, '.')

import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

from app.core.pdf_processor import PDFProcessor

PDF_PATH = "input/DI_PAOLO_THESIS.pdf"
PAGE_NUM = 1  # 0-indexed, page 2

def test_merge():
    """Test cross-block merging."""
    processor = PDFProcessor(PDF_PATH)
    
    # Get the page's text dict
    page = processor.document[PAGE_NUM]
    text_dict = page.get_text("dict")
    
    print("=" * 80)
    print("Testing _merge_single_line_blocks on DI_PAOLO_THESIS.pdf page 2")
    print("=" * 80)
    
    # Test the merge function
    merged_groups = processor._merge_single_line_blocks(text_dict)
    
    print(f"\nMerged into {len(merged_groups)} paragraph groups:")
    
    for i, group in enumerate(merged_groups):
        print(f"\n{'='*60}")
        print(f"GROUP {i+1} ({len(group)} blocks)")
        print(f"{'='*60}")
        
        # Show combined text
        combined_text = " ".join(b['text'] for b in group)
        print(f"Combined text ({len(combined_text)} chars):")
        print(f"  {combined_text}")
        print()
        
        # Show individual blocks in this group
        for j, block_data in enumerate(group):
            ends_punct = block_data['text'][-1] in '.!?' if block_data['text'] else False
            marker = "✓" if ends_punct else "→"
            print(f"  {marker} Block {j}: {block_data['text'][:60]}{'...' if len(block_data['text']) > 60 else ''}")

if __name__ == "__main__":
    test_merge()
