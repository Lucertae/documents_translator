#!/usr/bin/env python3
"""
Test specifico per documenti problematici.
Traduce pagine specifiche e salva output per ispezione visiva.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pathlib import Path
import pymupdf as fitz

from app.core.pdf_processor import PDFProcessor
from app.core.translator import TranslationEngine

INPUT_DIR = Path("input")
OUTPUT_DIR = Path("output/test_problematic")

# Documenti problematici dal benchmark
PROBLEM_DOCS = [
    {
        "file": "sim_economist_1881-08-06_39_1980.pdf",
        "pages": [0],  # Solo prima pagina per velocità
        "issue": "Quality 92.50%, font piccoli, 338+ black spans"
    },
    {
        "file": "V. S. Vladimirov - Equations of mathematical physics b.pdf",
        "pages": [1],  # Seconda pagina (la prima ha solo 6 parole)
        "issue": "Quality 95.00%, uppercase blocks, word overlap 59%"
    },
]


def find_pdf(filename: str) -> Path | None:
    """Cerca il PDF nella directory input."""
    for pdf in INPUT_DIR.rglob("*.pdf"):
        if pdf.name == filename:
            return pdf
    return None


def analyze_page_structure(doc: fitz.Document, page_num: int) -> dict:
    """Analizza la struttura di una pagina."""
    page = doc[page_num]
    
    # Estrai blocchi di testo con dettagli
    text_dict = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)
    
    stats = {
        "blocks": len(text_dict.get("blocks", [])),
        "lines": 0,
        "spans": 0,
        "fonts": set(),
        "font_sizes": [],
        "colors": set(),
        "rotations": [],
        "sample_text": []
    }
    
    for block in text_dict.get("blocks", []):
        if block.get("type") == 0:  # Text block
            for line in block.get("lines", []):
                stats["lines"] += 1
                
                # Direzione/rotazione
                dir_vec = line.get("dir", (1, 0))
                stats["rotations"].append(dir_vec)
                
                for span in line.get("spans", []):
                    stats["spans"] += 1
                    stats["fonts"].add(span.get("font", "unknown"))
                    stats["font_sizes"].append(span.get("size", 0))
                    
                    # Colore (normalizzato)
                    color = span.get("color", 0)
                    stats["colors"].add(color)
                    
                    # Campione testo
                    text = span.get("text", "").strip()
                    if text and len(stats["sample_text"]) < 5:
                        stats["sample_text"].append({
                            "text": text[:50],
                            "font": span.get("font"),
                            "size": round(span.get("size", 0), 1),
                            "color": color
                        })
    
    # Statistiche font size
    if stats["font_sizes"]:
        stats["min_font"] = min(stats["font_sizes"])
        stats["max_font"] = max(stats["font_sizes"])
        stats["avg_font"] = sum(stats["font_sizes"]) / len(stats["font_sizes"])
    
    # Rotazioni uniche
    unique_rotations = set(tuple(r) for r in stats["rotations"])
    stats["unique_rotations"] = list(unique_rotations)
    
    return stats


def translate_and_analyze(pdf_path: Path, pages: list[int], output_name: str):
    """Traduce pagine specifiche e analizza risultato."""
    
    print(f"\n{'='*70}")
    print(f"FILE: {pdf_path.name}")
    print(f"{'='*70}")
    
    # Apri documento originale per analisi
    doc_orig = fitz.open(str(pdf_path))
    print(f"Pagine totali: {len(doc_orig)}")
    
    for page_num in pages:
        if page_num >= len(doc_orig):
            print(f"  ⚠ Pagina {page_num} non esiste")
            continue
            
        print(f"\n--- Pagina {page_num + 1} (indice {page_num}) ORIGINALE ---")
        
        # Analisi struttura originale
        stats = analyze_page_structure(doc_orig, page_num)
        print(f"  Struttura originale:")
        print(f"    Blocchi: {stats['blocks']}, Linee: {stats['lines']}, Spans: {stats['spans']}")
        if stats.get('min_font'):
            print(f"    Font sizes: min={stats['min_font']:.1f}, max={stats['max_font']:.1f}, avg={stats['avg_font']:.1f}")
        print(f"    Font usati: {stats['fonts']}")
        print(f"    Colori unici: {len(stats['colors'])}")
        print(f"    Rotazioni uniche: {stats['unique_rotations']}")
        
        if stats["sample_text"]:
            print(f"    Campioni testo:")
            for s in stats["sample_text"][:3]:
                print(f"      - '{s['text']}' (font={s['font']}, size={s['size']}, color={s['color']})")
    
    doc_orig.close()
    
    # Ora traduci usando l'API corretta
    print(f"\n  🔄 Traduzione in corso...")
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Inizializza traduttore (OPUS-MT usa solo source/target)
    translator = TranslationEngine(
        source_lang="en",
        target_lang="it"
    )
    
    # Inizializza processor con il path del PDF
    processor = PDFProcessor(str(pdf_path))
    
    # Traduco ogni pagina e salvo separatamente
    for page_num in pages:
        if page_num >= processor.page_count:
            continue
            
        print(f"\n  Traducendo pagina {page_num + 1}...")
        output_path = OUTPUT_DIR / f"{output_name}_p{page_num+1}_translated.pdf"
        
        try:
            # Traduci la pagina - restituisce un nuovo documento
            translated_doc = processor.translate_page(
                page_num=page_num,
                translator=translator,
                use_original_color=True  # Usa colore originale
            )
            
            # Salva il documento tradotto
            translated_doc.save(str(output_path))
            print(f"    ✓ Salvato: {output_path}")
            
            # Analizza output tradotto
            print(f"\n  📊 Analisi output tradotto (pagina {page_num + 1}):")
            stats = analyze_page_structure(translated_doc, 0)  # Pagina 0 nel nuovo doc
            print(f"    Blocchi: {stats['blocks']}, Linee: {stats['lines']}, Spans: {stats['spans']}")
            print(f"    Colori unici: {len(stats['colors'])} -> {stats['colors']}")
            
            if stats["sample_text"]:
                print(f"    Campioni testo tradotto:")
                for s in stats["sample_text"][:5]:
                    print(f"      - '{s['text']}' (size={s['size']}, color={s['color']})")
            
            translated_doc.close()
                    
        except Exception as e:
            print(f"    ✗ Errore: {e}")
            import traceback
            traceback.print_exc()
    
    return OUTPUT_DIR


def main():
    print("="*70)
    print("TEST DOCUMENTI PROBLEMATICI")
    print("="*70)
    
    results = []
    
    for doc_info in PROBLEM_DOCS:
        pdf_path = find_pdf(doc_info["file"])
        
        if not pdf_path:
            print(f"\n⚠ Non trovato: {doc_info['file']}")
            continue
        
        print(f"\n📄 Problema noto: {doc_info['issue']}")
        
        output_name = pdf_path.stem[:30]  # Troncato per sicurezza
        
        try:
            output_dir = translate_and_analyze(
                pdf_path, 
                doc_info["pages"],
                output_name
            )
            results.append((doc_info["file"], output_dir, "OK"))
        except Exception as e:
            print(f"  ✗ ERRORE FATALE: {e}")
            import traceback
            traceback.print_exc()
            results.append((doc_info["file"], None, str(e)))
    
    print("\n" + "="*70)
    print("RIEPILOGO")
    print("="*70)
    for filename, output, status in results:
        if output:
            print(f"  ✓ {filename} -> {output}")
        else:
            print(f"  ✗ {filename}: {status}")
    
    print(f"\n📁 Output salvati in: {OUTPUT_DIR.absolute()}")
    print("   Apri i PDF per ispezione visiva!")


if __name__ == "__main__":
    main()
