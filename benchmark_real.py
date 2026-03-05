#!/usr/bin/env python3
"""
Benchmark reale su documenti in input/
Testa 4 pagine per documento e misura tempi, qualità, metriche
"""
import os
os.environ['DISABLE_MODEL_SOURCE_CHECK'] = 'True'

import time
import fitz
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
        'char_count': 0,
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
                
                if prev_y1 > 0 and y0 < prev_y1 - 1:  # 1pt tolerance
                    metrics['overlapping_lines'] += 1
                prev_y1 = y1
                
                for s in l.get('spans', []):
                    text = s.get('text', '').strip()
                    if text:
                        metrics['span_count'] += 1
                        metrics['char_count'] += len(text)
                        size = s.get('size', 0)
                        metrics['min_font'] = min(metrics['min_font'], size)
                        metrics['max_font'] = max(metrics['max_font'], size)
                        if size < 7:
                            metrics['under_7pt'] += 1
                        metrics['word_count'] += len(text.split())
    
    if metrics['min_font'] == float('inf'):
        metrics['min_font'] = 0
    
    return metrics


def test_document(pdf_path, max_pages=4):
    """Testa un documento e ritorna risultati"""
    results = {
        'file': pdf_path.name,
        'total_pages': 0,
        'tested_pages': 0,
        'times': [],
        'avg_time': 0,
        'total_words_orig': 0,
        'total_words_trans': 0,
        'overlap_pct': 0,
        'under7_pct': 0,
        'errors': 0,
        'status': 'ok'
    }
    
    try:
        doc = fitz.open(str(pdf_path))
        results['total_pages'] = len(doc)
        doc.close()
        
        pages_to_test = min(max_pages, results['total_pages'])
        
        # Inizializza processor e translator
        processor = PDFProcessor(str(pdf_path))
        translator = TranslationEngine('en', 'it')
        
        all_overlap = []
        all_under7 = []
        
        for page_num in range(pages_to_test):
            try:
                # Conta parole originali
                orig_doc = fitz.open(str(pdf_path))
                orig_text = orig_doc[page_num].get_text()
                orig_words = len(orig_text.split())
                orig_doc.close()
                results['total_words_orig'] += orig_words
                
                # Traduci e misura tempo
                start = time.time()
                new_doc = processor.translate_page(
                    page_num=page_num,
                    translator=translator,
                    preserve_line_breaks=True,
                    use_original_color=True
                )
                elapsed = time.time() - start
                results['times'].append(elapsed)
                
                if new_doc:
                    # Analizza output
                    metrics = analyze_page(new_doc, 0)
                    results['total_words_trans'] += metrics['word_count']
                    results['tested_pages'] += 1
                    
                    overlap_pct = 100 * metrics['overlapping_lines'] / metrics['total_lines'] if metrics['total_lines'] > 0 else 0
                    under7_pct = 100 * metrics['under_7pt'] / metrics['span_count'] if metrics['span_count'] > 0 else 0
                    
                    all_overlap.append(overlap_pct)
                    all_under7.append(under7_pct)
                    
                    new_doc.close()
                else:
                    results['errors'] += 1
                    
            except Exception as e:
                results['errors'] += 1
                print(f"    Errore pagina {page_num + 1}: {e}")
        
        # Calcola medie
        if results['times']:
            results['avg_time'] = sum(results['times']) / len(results['times'])
        if all_overlap:
            results['overlap_pct'] = sum(all_overlap) / len(all_overlap)
        if all_under7:
            results['under7_pct'] = sum(all_under7) / len(all_under7)
            
        if results['errors'] > 0:
            results['status'] = 'warning'
            
    except Exception as e:
        results['status'] = 'error'
        results['error_msg'] = str(e)
        print(f"  ERRORE: {e}")
    
    return results


def main():
    print("=" * 70)
    print("BENCHMARK REALE - LAC Translate v0.1.6")
    print(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    input_dir = Path("input")
    
    # Trova tutti i PDF (inclusi confidenziali)
    pdf_files = list(input_dir.glob("*.pdf")) + list(input_dir.glob("confidenziali/*.pdf"))
    
    print(f"\nDocumenti trovati: {len(pdf_files)}")
    print("-" * 70)
    
    all_results = []
    total_pages = 0
    total_time = 0
    
    for pdf_path in sorted(pdf_files):
        print(f"\n📄 {pdf_path.name[:50]}...")
        result = test_document(pdf_path, max_pages=4)
        all_results.append(result)
        
        total_pages += result['tested_pages']
        total_time += sum(result['times'])
        
        print(f"   Pagine: {result['tested_pages']}/{result['total_pages']}")
        print(f"   Tempo medio: {result['avg_time']:.2f}s/pagina")
        print(f"   Overlap: {result['overlap_pct']:.1f}%")
        print(f"   Font <7pt: {result['under7_pct']:.1f}%")
        if result['errors']:
            print(f"   ⚠️ Errori: {result['errors']}")
    
    # Riepilogo finale
    print("\n" + "=" * 70)
    print("RIEPILOGO BENCHMARK")
    print("=" * 70)
    
    avg_time_global = total_time / total_pages if total_pages > 0 else 0
    avg_overlap = sum(r['overlap_pct'] for r in all_results) / len(all_results) if all_results else 0
    avg_under7 = sum(r['under7_pct'] for r in all_results) / len(all_results) if all_results else 0
    ok_docs = sum(1 for r in all_results if r['overlap_pct'] < 10)
    
    print(f"\n📊 METRICHE AGGREGATE")
    print(f"   Documenti testati: {len(all_results)}")
    print(f"   Pagine totali tradotte: {total_pages}")
    print(f"   Tempo totale: {total_time:.1f}s")
    print(f"   Tempo medio/pagina: {avg_time_global:.2f}s")
    print(f"   Overlap medio: {avg_overlap:.1f}%")
    print(f"   Font <7pt medio: {avg_under7:.1f}%")
    print(f"   Documenti OK (overlap <10%): {ok_docs}/{len(all_results)} ({100*ok_docs/len(all_results):.0f}%)")
    
    # Tabella dettagliata
    print("\n" + "-" * 70)
    print("DETTAGLIO PER DOCUMENTO")
    print("-" * 70)
    print(f"{'Documento':<40} {'Pag':>4} {'Tempo':>8} {'Overlap':>8} {'<7pt':>8}")
    print("-" * 70)
    
    for r in all_results:
        name = r['file'][:38] + ".." if len(r['file']) > 40 else r['file']
        status = "✅" if r['overlap_pct'] < 10 else "⚠️"
        print(f"{status} {name:<38} {r['tested_pages']:>4} {r['avg_time']:>7.2f}s {r['overlap_pct']:>7.1f}% {r['under7_pct']:>7.1f}%")
    
    print("-" * 70)
    print(f"{'MEDIA':<40} {total_pages:>4} {avg_time_global:>7.2f}s {avg_overlap:>7.1f}% {avg_under7:>7.1f}%")


if __name__ == "__main__":
    main()
