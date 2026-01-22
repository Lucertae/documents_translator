#!/usr/bin/env python3
"""
Test di regressione su tutti i documenti in input/
Testa 4 pagine per documento e genera report di qualità
"""
import os
os.environ['DISABLE_MODEL_SOURCE_CHECK'] = 'True'

import fitz
from PIL import Image
from pathlib import Path
from datetime import datetime

from app.core.pdf_processor import PDFProcessor
from app.core.translator import TranslationEngine

def analyze_page(doc, page_idx):
    """Analizza una pagina e restituisce metriche"""
    page = doc[page_idx]
    blocks = page.get_text('dict')['blocks']
    
    metrics = {
        'span_count': 0,
        'word_count': 0,
        'min_font': float('inf'),
        'max_font': 0,
        'under_7pt': 0,
        'overlapping_lines': 0,
        'total_lines': 0
    }
    
    for b in blocks:
        if b.get('type') == 0:
            lines = b.get('lines', [])
            prev_y1 = 0
            
            for l in lines:
                metrics['total_lines'] += 1
                y0, y1 = l['bbox'][1], l['bbox'][3]
                
                if prev_y1 > 0 and y0 < prev_y1:
                    metrics['overlapping_lines'] += 1
                prev_y1 = y1
                
                for s in l.get('spans', []):
                    text = s.get('text', '').strip()
                    if text:
                        metrics['span_count'] += 1
                        size = s.get('size', 0)
                        metrics['min_font'] = min(metrics['min_font'], size)
                        metrics['max_font'] = max(metrics['max_font'], size)
                        if size < 7:
                            metrics['under_7pt'] += 1
                        metrics['word_count'] += len(text.split())
    
    if metrics['min_font'] == float('inf'):
        metrics['min_font'] = 0
    
    return metrics

def test_document(pdf_path, test_pages, output_dir):
    """Testa un documento su pagine specifiche"""
    print(f"\n{'='*60}")
    print(f"Testing: {pdf_path.name}")
    print(f"{'='*60}")
    
    doc = fitz.open(str(pdf_path))
    total_pages = len(doc)
    doc.close()
    
    # Filtra pagine valide
    valid_pages = [p for p in test_pages if p <= total_pages]
    
    if not valid_pages:
        print(f"  ⚠️ Nessuna pagina valida (documento ha {total_pages} pagine)")
        return None
    
    print(f"  Pagine totali: {total_pages}")
    print(f"  Pagine test: {valid_pages}")
    
    results = {
        'file': pdf_path.name,
        'total_pages': total_pages,
        'tested_pages': valid_pages,
        'pages': {}
    }
    
    translator = TranslationEngine('en', 'it')
    processor = PDFProcessor(str(pdf_path))
    
    for page_num in valid_pages:
        print(f"\n  Pagina {page_num}...")
        
        try:
            # Traduci pagina (0-indexed)
            new_doc = processor.translate_page(
                page_num=page_num - 1,  # 0-indexed
                translator=translator,
                preserve_line_breaks=True,
                use_original_color=True
            )
            
            if new_doc:
                # Analizza
                metrics = analyze_page(new_doc, 0)
                
                # Genera PNG confronto
                doc_orig = fitz.open(str(pdf_path))
                pix_orig = doc_orig[page_num - 1].get_pixmap(dpi=100)
                pix_trad = new_doc[0].get_pixmap(dpi=100)
                doc_orig.close()
                new_doc.close()
                
                # Side by side
                orig_img = Image.frombytes("RGB", [pix_orig.width, pix_orig.height], pix_orig.samples)
                trad_img = Image.frombytes("RGB", [pix_trad.width, pix_trad.height], pix_trad.samples)
                
                width = orig_img.width + trad_img.width + 10
                height = max(orig_img.height, trad_img.height)
                combined = Image.new('RGB', (width, height), 'white')
                combined.paste(orig_img, (0, 0))
                combined.paste(trad_img, (orig_img.width + 10, 0))
                
                out_png = output_dir / f"{pdf_path.stem}_p{page_num}_compare.png"
                combined.save(str(out_png))
                
                # Report
                overlap_pct = 100 * metrics['overlapping_lines'] / metrics['total_lines'] if metrics['total_lines'] > 0 else 0
                under7_pct = 100 * metrics['under_7pt'] / metrics['span_count'] if metrics['span_count'] > 0 else 0
                
                status = "✓" if overlap_pct < 10 and under7_pct < 20 else "⚠️"
                
                print(f"    {status} Words: {metrics['word_count']}, Font: {metrics['min_font']:.1f}-{metrics['max_font']:.1f}pt")
                print(f"       Overlap: {metrics['overlapping_lines']}/{metrics['total_lines']} ({overlap_pct:.1f}%)")
                print(f"       Under 7pt: {metrics['under_7pt']}/{metrics['span_count']} ({under7_pct:.1f}%)")
                
                results['pages'][page_num] = {
                    'status': 'ok' if overlap_pct < 10 else 'warning',
                    'metrics': metrics,
                    'overlap_pct': overlap_pct,
                    'under7_pct': under7_pct
                }
            else:
                print(f"    ❌ Traduzione fallita")
                results['pages'][page_num] = {'status': 'failed'}
                
        except Exception as e:
            print(f"    ❌ Errore: {e}")
            results['pages'][page_num] = {'status': 'error', 'error': str(e)}
    
    return results

def main():
    print("="*60)
    print("TEST DI REGRESSIONE - DOCUMENTS TRANSLATOR")
    print(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*60)
    
    # Setup
    input_dir = Path('input')
    output_dir = Path('output/regression_test')
    output_dir.mkdir(exist_ok=True)
    
    # Trova tutti i PDF
    # Use set to avoid duplicates, **/*.pdf already matches files in root
    pdfs = sorted(set(input_dir.glob('**/*.pdf')))
    print(f"\nDocumenti trovati: {len(pdfs)}")
    for p in pdfs:
        print(f"  - {p}")
    
    # Test pages: 1, 3, metà, ultimo
    all_results = []
    
    for pdf_path in pdfs:
        # Determina pagine da testare
        doc = fitz.open(str(pdf_path))
        total = len(doc)
        doc.close()
        
        if total <= 4:
            test_pages = list(range(1, total + 1))
        else:
            test_pages = [1, 3, total // 2, min(total, 20)]
        
        result = test_document(pdf_path, test_pages, output_dir)
        if result:
            all_results.append(result)
    
    # Report finale
    print("\n" + "="*60)
    print("RIEPILOGO RISULTATI")
    print("="*60)
    
    total_pages_tested = 0
    total_ok = 0
    total_warnings = 0
    total_errors = 0
    
    for r in all_results:
        print(f"\n{r['file']}:")
        for page_num, page_data in r['pages'].items():
            total_pages_tested += 1
            status = page_data.get('status', 'unknown')
            if status == 'ok':
                total_ok += 1
            elif status == 'warning':
                total_warnings += 1
            else:
                total_errors += 1
    
    print(f"\n{'='*60}")
    print(f"TOTALE: {total_pages_tested} pagine testate")
    print(f"  ✓ OK: {total_ok}")
    print(f"  ⚠️ Warning: {total_warnings}")
    print(f"  ❌ Errori: {total_errors}")
    
    print(f"\nPNG di confronto salvati in: {output_dir}/*.png")
    
    return all_results

if __name__ == '__main__':
    results = main()
