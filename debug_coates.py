#!/usr/bin/env python3
"""
Debug specifico per Coates_825.pdf - analizza cosa manca nella traduzione.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pathlib import Path
import pymupdf as fitz

from app.core.pdf_processor import PDFProcessor
from app.core.translator import TranslationEngine

PDF_PATH = Path("input/Coates_825.pdf")
OUTPUT_DIR = Path("output/debug_coates")


def extract_all_text_with_details(page: fitz.Page) -> list:
    """Estrae tutto il testo con dettagli per ogni span."""
    result = []
    text_dict = page.get_text("dict")
    
    for block_idx, block in enumerate(text_dict.get("blocks", [])):
        if "lines" not in block:
            continue
        
        for line_idx, line in enumerate(block["lines"]):
            for span_idx, span in enumerate(line.get("spans", [])):
                text = span.get("text", "")
                if text.strip():
                    result.append({
                        "block": block_idx,
                        "line": line_idx,
                        "span": span_idx,
                        "text": text,
                        "bbox": span.get("bbox"),
                        "font": span.get("font"),
                        "size": span.get("size"),
                        "color": span.get("color", 0)
                    })
    return result


def compare_texts(original_spans: list, translated_spans: list):
    """Confronta i testi e trova cosa manca."""
    
    # Raccogli tutto il testo originale
    orig_texts = [s["text"].strip() for s in original_spans if s["text"].strip()]
    trans_texts = [s["text"].strip() for s in translated_spans if s["text"].strip()]
    
    print(f"\n{'='*70}")
    print("CONFRONTO TESTI")
    print(f"{'='*70}")
    print(f"Spans originali: {len(orig_texts)}")
    print(f"Spans tradotti: {len(trans_texts)}")
    
    # Trova testi originali che potrebbero essere stati persi
    orig_words = set()
    for t in orig_texts:
        orig_words.update(t.lower().split())
    
    trans_words = set()
    for t in trans_texts:
        trans_words.update(t.lower().split())
    
    # Parole originali non presenti (potrebbero essere tradotte)
    missing_orig = orig_words - trans_words
    
    # Parole nuove (traduzioni)
    new_words = trans_words - orig_words
    
    print(f"\nParole originali: {len(orig_words)}")
    print(f"Parole nel tradotto: {len(trans_words)}")
    print(f"Parole 'scomparse' (tradotte): {len(missing_orig)}")
    print(f"Parole nuove (traduzioni): {len(new_words)}")
    
    # Mostra i primi 20 testi originali
    print(f"\n--- PRIMI 30 SPAN ORIGINALI ---")
    for i, s in enumerate(original_spans[:30]):
        print(f"  [{i}] '{s['text'][:60]}' (font={s['font']}, size={s['size']:.1f})")
    
    # Mostra i primi 20 testi tradotti
    print(f"\n--- PRIMI 30 SPAN TRADOTTI ---")
    for i, s in enumerate(translated_spans[:30]):
        print(f"  [{i}] '{s['text'][:60]}' (font={s['font']}, size={s['size']:.1f})")
    
    # Cerca pattern di testo mancante
    print(f"\n--- ANALISI COPERTURA ---")
    
    # Confronta per posizione approssimativa (bbox)
    orig_by_y = sorted(original_spans, key=lambda s: (s['bbox'][1], s['bbox'][0]))
    trans_by_y = sorted(translated_spans, key=lambda s: (s['bbox'][1], s['bbox'][0]))
    
    # Raggruppa per "riga" (stessa Y approssimativa)
    def group_by_row(spans, tolerance=5):
        rows = []
        current_row = []
        current_y = None
        for s in spans:
            y = s['bbox'][1]
            if current_y is None or abs(y - current_y) < tolerance:
                current_row.append(s)
                current_y = y
            else:
                if current_row:
                    rows.append(current_row)
                current_row = [s]
                current_y = y
        if current_row:
            rows.append(current_row)
        return rows
    
    orig_rows = group_by_row(orig_by_y)
    trans_rows = group_by_row(trans_by_y)
    
    print(f"\nRighe originali: {len(orig_rows)}")
    print(f"Righe tradotte: {len(trans_rows)}")
    
    if len(trans_rows) < len(orig_rows):
        print(f"⚠️ MANCANO {len(orig_rows) - len(trans_rows)} RIGHE!")
    
    # Mostra righe fianco a fianco
    print(f"\n--- CONFRONTO RIGA PER RIGA (prime 20) ---")
    max_rows = min(20, max(len(orig_rows), len(trans_rows)))
    
    for i in range(max_rows):
        orig_text = " ".join(s['text'] for s in orig_rows[i]) if i < len(orig_rows) else "[MANCANTE]"
        trans_text = " ".join(s['text'] for s in trans_rows[i]) if i < len(trans_rows) else "[MANCANTE]"
        
        # Tronca per leggibilità
        orig_text = orig_text[:70] + "..." if len(orig_text) > 70 else orig_text
        trans_text = trans_text[:70] + "..." if len(trans_text) > 70 else trans_text
        
        status = "✓" if i < len(trans_rows) else "✗"
        print(f"\n  [{i}] {status}")
        print(f"      ORIG: {orig_text}")
        print(f"      TRAD: {trans_text}")


def main():
    print("="*70)
    print("DEBUG COATES_825.pdf")
    print("="*70)
    
    if not PDF_PATH.exists():
        print(f"❌ File non trovato: {PDF_PATH}")
        return
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Apri originale
    doc_orig = fitz.open(str(PDF_PATH))
    print(f"Pagine totali: {len(doc_orig)}")
    
    # Analizziamo pagina 1 (indice 0)
    page_num = 0
    page_orig = doc_orig[page_num]
    
    print(f"\n--- ANALISI PAGINA {page_num + 1} ORIGINALE ---")
    original_spans = extract_all_text_with_details(page_orig)
    print(f"Spans totali: {len(original_spans)}")
    
    # Testo completo originale
    orig_full_text = page_orig.get_text()
    print(f"Caratteri totali: {len(orig_full_text)}")
    print(f"\nPrimi 500 caratteri originale:")
    print(orig_full_text[:500])
    
    doc_orig.close()
    
    # Ora traduci
    print(f"\n{'='*70}")
    print("TRADUZIONE IN CORSO...")
    print(f"{'='*70}")
    
    translator = TranslationEngine(source_lang="en", target_lang="it")
    processor = PDFProcessor(str(PDF_PATH))
    
    translated_doc = processor.translate_page(
        page_num=page_num,
        translator=translator,
        use_original_color=True
    )
    
    # Salva
    output_path = OUTPUT_DIR / "coates_p1_translated.pdf"
    translated_doc.save(str(output_path))
    print(f"✓ Salvato: {output_path}")
    
    # Analizza tradotto
    print(f"\n--- ANALISI PAGINA TRADOTTA ---")
    page_trans = translated_doc[0]
    translated_spans = extract_all_text_with_details(page_trans)
    print(f"Spans totali: {len(translated_spans)}")
    
    # Testo completo tradotto
    trans_full_text = page_trans.get_text()
    print(f"Caratteri totali: {len(trans_full_text)}")
    print(f"\nPrimi 500 caratteri tradotto:")
    print(trans_full_text[:500])
    
    translated_doc.close()
    
    # Confronta
    doc_orig = fitz.open(str(PDF_PATH))
    original_spans = extract_all_text_with_details(doc_orig[page_num])
    doc_orig.close()
    
    doc_trans = fitz.open(str(output_path))
    translated_spans = extract_all_text_with_details(doc_trans[0])
    doc_trans.close()
    
    compare_texts(original_spans, translated_spans)
    
    print(f"\n{'='*70}")
    print(f"PDF tradotto salvato in: {output_path}")
    print("Aprilo per ispezione visiva!")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
