#!/usr/bin/env python3
"""
Debug della traduzione blocco per blocco per capire lo sfasamento.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pathlib import Path
import pymupdf as fitz

from app.core.translator import TranslationEngine, split_into_sentences, align_sentences_to_lines

PDF_PATH = Path("input/Coates_825.pdf")


def main():
    print("="*80)
    print("DEBUG TRADUZIONE BLOCCO PER BLOCCO")
    print("="*80)
    
    doc = fitz.open(str(PDF_PATH))
    page = doc[0]
    
    text_dict = page.get_text("dict")
    
    translator = TranslationEngine(source_lang="en", target_lang="it")
    
    block_num = 0
    for block in text_dict.get("blocks", []):
        if "lines" not in block:
            continue
        
        block_num += 1
        lines_data = []
        block_full_text = []
        
        for line in block["lines"]:
            if "spans" not in line:
                continue
            
            line_text_parts = []
            for span in line["spans"]:
                text = span.get("text", "").strip()
                if text:
                    line_text_parts.append(text)
            
            if line_text_parts:
                line_text = " ".join(line_text_parts)
                lines_data.append({
                    'text': line_text,
                    'bbox': line.get("bbox")
                })
                block_full_text.append(line_text)
        
        if not lines_data:
            continue
        
        print(f"\n{'='*80}")
        print(f"BLOCCO {block_num}")
        print(f"{'='*80}")
        
        # Mostra linee originali
        print(f"\n📖 LINEE ORIGINALI ({len(lines_data)}):")
        for i, ld in enumerate(lines_data):
            print(f"  [{i}] ({len(ld['text']):3d} chars) '{ld['text']}'")
        
        # Testo completo del blocco
        block_text = " ".join(block_full_text)
        print(f"\n📝 BLOCCO COMPLETO ({len(block_text)} chars):")
        print(f"  '{block_text}'")
        
        # Traduzione
        translated_block = translator.translate(block_text)
        print(f"\n🔄 TRADUZIONE ({len(translated_block)} chars):")
        print(f"  '{translated_block}'")
        
        # Split in frasi
        translated_sentences = split_into_sentences(translated_block)
        print(f"\n📊 FRASI TRADOTTE ({len(translated_sentences)}):")
        for i, s in enumerate(translated_sentences):
            print(f"  [{i}] '{s}'")
        
        # Allineamento
        original_line_lengths = [len(line['text']) for line in lines_data]
        line_texts = align_sentences_to_lines(
            translated_sentences,
            len(lines_data),
            original_line_lengths
        )
        
        print(f"\n📐 ALLINEAMENTO RISULTANTE:")
        for i, (orig, trans) in enumerate(zip(lines_data, line_texts)):
            status = "✓" if trans.strip() else "❌"
            print(f"  [{i}] {status}")
            print(f"      ORIG ({len(orig['text']):3d}): '{orig['text']}'")
            print(f"      TRAD ({len(trans):3d}): '{trans}'")
        
        # Verifica problemi
        if len(translated_sentences) != len(lines_data):
            print(f"\n  ⚠️ MISMATCH: {len(translated_sentences)} frasi → {len(lines_data)} linee")
    
    doc.close()
    print(f"\n{'='*80}")
    print("FINE DEBUG")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
