#!/usr/bin/env python3
"""
Benchmark OCR completo per valutare la qualità dell'output RapidOCR.

Testa tutti i documenti con metriche di qualità:
- Confidence media
- Rilevamento colonne
- Conteggio caratteri/parole
- Confronto con reference text (dove disponibile)
- Tempo per pagina
"""
import os
os.environ['DISABLE_MODEL_SOURCE_CHECK'] = 'True'

import logging
logging.basicConfig(level=logging.WARNING)

import sys
import time
import re
from pathlib import Path
from difflib import SequenceMatcher

import numpy as np
import pymupdf

# Reset singleton to pick up new params
from app.core.rapid_ocr import RapidOcrEngine, OCR_ENGINE_NAME
RapidOcrEngine._instance = None
RapidOcrEngine._engine = None
RapidOcrEngine._available = None

from app.core.preprocess_for_ocr import preprocess_page_from_pymupdf
from app.core.ocr_utils import clean_ocr_text, post_process_ocr_text


# --- Reference text per la pagina TOC del contratto Authorized Distribution Agreement ---
REFERENCE_TOC_KEYWORDS = [
    "AUTHORIZED DISTRIBUTION AGREEMENT",
    "Table of Contents",
    "Article 1",
    "Definitions",
    "Article 2",
    "Authorised Distributor",
    "Article 3",
    "Non-Competition",
    "Article 4",
    "Article 5",
    "Orders and delivery",
    "Article 6",
    "Conditions of supply",
    "Article 7",
    "Sales targets",
    "Article 8",
    "Performance of functions",
    "Article 9",
    "Information obligation",
    "Article 10",
    "Warranty",
    "Article 12",
    "trademarks",
    "Article 13",
    "Confidential information",
    "Article 14",
    "Stock of Products",
    "Article 15",
    "Article 16",
    "Training",
    "Article 17",
    "Demos",
    "Article 18",
    "Duration and termination",
    "Article 19",
    "Article 20",
    "Resolution of disputes",
    "Article 21",
    "Applicable law",
    "Article 22",
    "Compliance",
    "Article 23",
    "Personal Data Protection",
    "Article 24",
    "Miscellaneous",
    "Exhibit #1",
    "Exhibit #2",
    "Exhibit #3",
    "Warranty Duration",
    "Spare Parts",
    "Print Heads",
    "UV Lamp",
    "Ink Warranty",
]

# Reference: body text keywords (page 2 = Articles 2-6 content)
REFERENCE_BODY_KEYWORDS = [
    "AUTHORIZED DISTRIBUTION AGREEMENT",
    "Article 2",
    "Authorised Distributor",
    "Products",
    "Territory",
    "Article 3",
    "Non-Competition",
    "Article 4",
    "obligations",
    "responsible businessman",
    "Article 5",
    "Orders and delivery",
    "Article 6",
    "Conditions of supply",
    "Mimaki",
    "Agreement",
    "warranty",
    "complaints",
    "purchase",
    "price",
    "delivery",
]


def keyword_recall(text: str, keywords: list) -> tuple:
    """
    Calcola la percentuale di keywords trovate nel testo.
    Returns: (recall_score, found_list, missing_list)
    """
    found = []
    missing = []
    for kw in keywords:
        if kw.lower() in text.lower():
            found.append(kw)
        else:
            missing.append(kw)
    recall = len(found) / len(keywords) if keywords else 0.0
    return recall, found, missing


def test_document(pdf_path: str, pages_to_test: list = None, reference_keywords: dict = None):
    """
    Testa un documento e restituisce metriche dettagliate.
    """
    doc = pymupdf.open(pdf_path)
    total_pages = len(doc)
    
    if pages_to_test is None:
        # Test prima 3 pagine
        pages_to_test = list(range(min(3, total_pages)))
    
    engine = RapidOcrEngine()
    results = {
        'file': Path(pdf_path).name,
        'total_pages': total_pages,
        'pages': []
    }
    
    for page_idx in pages_to_test:
        if page_idx >= total_pages:
            continue
        
        page = doc[page_idx]
        
        # Preprocess
        t0 = time.time()
        png_bytes, info = preprocess_page_from_pymupdf(page, dpi=300)
        t_preproc = time.time() - t0
        
        # OCR
        t1 = time.time()
        text, confidence = engine.recognize_text(png_bytes)
        t_ocr = time.time() - t1
        
        # Post-process
        clean_text = clean_ocr_text(text)
        
        page_result = {
            'page': page_idx,
            'preproc_time': t_preproc,
            'ocr_time': t_ocr,
            'total_time': t_preproc + t_ocr,
            'confidence': confidence,
            'chars': len(text),
            'words': len(text.split()),
            'lines': text.count('\n') + 1,
            'image_size': f"{info['width']}x{info['height']}",
            'file_size_kb': info['file_size_kb'],
        }
        
        # Keyword matching if reference available
        if reference_keywords and page_idx in reference_keywords:
            recall, found, missing = keyword_recall(clean_text, reference_keywords[page_idx])
            page_result['keyword_recall'] = recall
            page_result['keywords_found'] = len(found)
            page_result['keywords_total'] = len(reference_keywords[page_idx])
            page_result['keywords_missing'] = missing
        
        # Detect if multi-column was found (check for column separator in text)
        page_result['text_preview'] = text[:500]
        
        results['pages'].append(page_result)
    
    doc.close()
    return results


def print_results(results: dict):
    """Stampa risultati in formato leggibile."""
    print(f"\n{'='*80}")
    print(f"📄 {results['file']} ({results['total_pages']} pages)")
    print(f"{'='*80}")
    
    for pr in results['pages']:
        print(f"\n  --- Page {pr['page']} ---")
        print(f"  Image: {pr['image_size']}, {pr['file_size_kb']} KB")
        print(f"  Time: preproc={pr['preproc_time']:.2f}s, OCR={pr['ocr_time']:.2f}s, total={pr['total_time']:.2f}s")
        print(f"  Confidence: {pr['confidence']:.3f}")
        print(f"  Output: {pr['chars']} chars, {pr['words']} words, {pr['lines']} lines")
        
        if 'keyword_recall' in pr:
            emoji = "✅" if pr['keyword_recall'] >= 0.9 else "⚠️" if pr['keyword_recall'] >= 0.7 else "❌"
            print(f"  Keyword recall: {emoji} {pr['keyword_recall']*100:.1f}% ({pr['keywords_found']}/{pr['keywords_total']})")
            if pr['keywords_missing']:
                print(f"  Missing: {pr['keywords_missing'][:10]}")
        
        print(f"  Preview: {pr['text_preview'][:300]}...")


def main():
    print("=" * 80)
    print(f"OCR QUALITY BENCHMARK - {OCR_ENGINE_NAME}")
    print(f"DPI: 300 | Detection: PPOCRv5 MOBILE | Recognition: PPOCRv4 LATIN SERVER")
    print("=" * 80)
    
    # Define test cases
    test_cases = [
        {
            'path': 'input/confidenziali/Signed_FY2025_2027_Authorized_Distribution_Agreement_Distributor.pdf',
            'pages': [1, 2, 3],  # TOC page, first body page, second body page
            'keywords': {
                1: REFERENCE_TOC_KEYWORDS,
                2: REFERENCE_BODY_KEYWORDS,
            },
            'description': 'Two-column legal contract (Mimaki Distribution Agreement)',
        },
        {
            'path': 'input/confidenziali/Distribution Contract Trotec Bompan SRL_01062024_signed both parties.pdf',
            'pages': [0, 1, 2],
            'keywords': {},
            'description': 'Distribution contract (Trotec-Bompan)',
        },
        {
            'path': 'input/confidenziali/1.pdf',
            'pages': [0, 1],
            'keywords': {},
            'description': 'Confidential document 1',
        },
        {
            'path': 'input/2015.129351.Bibliography-Of-Doctoral-Dissertations_text.pdf',
            'pages': [0, 1, 2],
            'keywords': {},
            'description': 'Bibliography of Doctoral Dissertations (scanned)',
        },
        {
            'path': 'input/sim_economist_1881-08-06_39_1980.pdf',
            'pages': [0, 1, 2],
            'keywords': {},
            'description': 'The Economist 1881 (historical scanned)',
        },
        {
            'path': 'input/sim_quarterly-journal-of-economics_1980_94_contents.pdf',
            'pages': [0, 1],
            'keywords': {},
            'description': 'Quarterly Journal of Economics 1980 (contents)',
        },
    ]
    
    all_results = []
    total_time = 0
    total_pages = 0
    
    for tc in test_cases:
        path = tc['path']
        if not os.path.exists(path):
            print(f"\n⚠️  Skipping {path} (not found)")
            continue
        
        print(f"\n📄 Testing: {tc['description']}")
        result = test_document(path, tc['pages'], tc.get('keywords'))
        all_results.append(result)
        print_results(result)
        
        for pr in result['pages']:
            total_time += pr['total_time']
            total_pages += 1
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"Total documents: {len(all_results)}")
    print(f"Total pages tested: {total_pages}")
    print(f"Total time: {total_time:.1f}s")
    print(f"Avg time/page: {total_time/total_pages:.2f}s" if total_pages > 0 else "N/A")
    
    # Average confidence
    all_confs = [pr['confidence'] for r in all_results for pr in r['pages']]
    if all_confs:
        print(f"Avg confidence: {np.mean(all_confs):.3f}")
    
    # Keyword recall summary
    all_recalls = [pr['keyword_recall'] for r in all_results for pr in r['pages'] if 'keyword_recall' in pr]
    if all_recalls:
        print(f"Avg keyword recall: {np.mean(all_recalls)*100:.1f}%")
    
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
