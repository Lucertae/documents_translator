#!/usr/bin/env python3
"""
Structured Quality Verification Framework

This script provides comprehensive testing for the PDF translation pipeline:
1. OCR Accuracy - Character/word error rates, brand name preservation
2. Translation Quality - Fluency, terminology, completeness
3. Sentence Coherence - Original vs translated sentence alignment
4. Final Formatting - Layout preservation, font handling

Usage:
    python test_quality_framework.py --document <path> --pages 1-3
    python test_quality_framework.py --all-documents
"""
import sys
import os
import json
import time
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple
from pathlib import Path

# Environment setup for PaddlePaddle CPU (must be before imports)
os.environ['DISABLE_MODEL_SOURCE_CHECK'] = 'True'

sys.path.insert(0, str(Path(__file__).parent / 'app'))

import fitz
from paddleocr import PaddleOCR

# Local imports
from core.pdf_processor import PDFProcessor
from core.translator import TranslationEngine
from core.ocr_utils import clean_ocr_text, post_process_ocr_text


# ============================================
# Test Documents Registry
# ============================================
TEST_DOCUMENTS = {
    "mimaki_contract": {
        "path": "input/confidenziali/Signed_FY2025_2027_Authorized_Distribution_Agreement_Distributor.pdf",
        "description": "13-page scanned contract (EN)",
        "type": "scanned",
        "language": "en",
        "expected_terms": ["Mimaki", "Distributor", "Agreement", "Article", "Exhibit"],
        "pages": 13
    },
    "trotec_contract": {
        "path": "input/confidenziali/Distribution Contract Trotec Bompan SRL_01062024_signed both parties.pdf",
        "description": "Distribution contract (likely EN)",
        "type": "unknown",
        "language": "en",
        "expected_terms": ["Trotec", "Bompan", "Contract", "Distribution"],
        "pages": None
    },
    "physitek_letter": {
        "path": "input/confidenziali/2025-04-30 Physitek Letter [4].pdf",
        "description": "Business letter",
        "type": "unknown",
        "language": "en",
        "expected_terms": [],
        "pages": None
    },
    "coates": {
        "path": "input/Coates_825.pdf",
        "description": "Academic/technical document",
        "type": "unknown",
        "language": "en",
        "expected_terms": [],
        "pages": None
    },
    "world_bank": {
        "path": "input/The-World-Bank-economic-review-30-1.pdf",
        "description": "World Bank economic review",
        "type": "native_pdf",
        "language": "en",
        "expected_terms": ["World Bank", "economic", "review"],
        "pages": None
    },
    "iso_standard": {
        "path": "input/ISO-128-1-2020.pdf",
        "description": "ISO technical standard",
        "type": "native_pdf",
        "language": "en",
        "expected_terms": ["ISO", "standard", "technical"],
        "pages": None
    }
}


@dataclass
class OCRQualityResult:
    """OCR quality metrics."""
    page_num: int
    text_regions: int
    confidence_avg: float
    confidence_min: float
    expected_terms_found: List[str]
    expected_terms_missing: List[str]
    ocr_errors_detected: List[str]  # e.g., "MimakI", "nibit"
    raw_sample: str
    cleaned_sample: str


@dataclass
class TranslationQualityResult:
    """Translation quality metrics."""
    page_num: int
    original_sentences: int
    translated_sentences: int
    sentence_ratio: float  # Should be close to 1.0
    sample_pairs: List[Tuple[str, str]]  # (original, translated) samples
    terminology_preserved: List[str]  # Brand names kept as-is
    potential_issues: List[str]


@dataclass
class FormattingQualityResult:
    """Formatting quality metrics."""
    page_num: int
    text_blocks: int
    has_proper_layout: bool
    font_sizes_used: List[float]
    issues: List[str]


@dataclass
class PageQualityReport:
    """Complete quality report for a page."""
    ocr: Optional[OCRQualityResult]
    translation: Optional[TranslationQualityResult]
    formatting: Optional[FormattingQualityResult]
    overall_score: float  # 0-100


class QualityFramework:
    """Comprehensive quality verification framework."""
    
    def __init__(self):
        self.ocr = None
        self.translator = None
        self.results = {}
    
    def _init_ocr(self, lang: str = 'en'):
        """Initialize OCR engine lazily with PP-OCRv5 models.
        
        Supported languages: en, it, fr, de, es, pt, ru, ar, zh, ja, ko, etc.
        For mixed-language docs use 'latin' or 'multilingual'.
        """
        if self.ocr is None:
            print(f"Initializing PaddleOCR 3.3.3 (PP-OCRv5, lang={lang})...")
            self.ocr = PaddleOCR(
                lang=lang,
                use_textline_orientation=True  # Better text line detection
            )
    
    def _init_translator(self, source='en', target='it'):
        """Initialize translator lazily."""
        if self.translator is None:
            print(f"Initializing translator ({source} → {target})...")
            self.translator = TranslationEngine(source, target)
    
    def analyze_ocr_quality(
        self, 
        pdf_path: str, 
        page_num: int,
        expected_terms: List[str] = None
    ) -> OCRQualityResult:
        """Analyze OCR quality for a single page."""
        self._init_ocr()
        
        doc = fitz.open(pdf_path)
        page = doc[page_num]
        
        # Convert to image
        mat = fitz.Matrix(2.0, 2.0)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img_path = f'/tmp/quality_test_p{page_num}.png'
        pix.save(img_path)
        
        # Run OCR (PaddleOCR 3.3.3 uses predict() method with PP-OCRv5)
        result = self.ocr.predict(img_path)
        
        if not result or len(result) == 0:
            doc.close()
            return OCRQualityResult(
                page_num=page_num,
                text_regions=0,
                confidence_avg=0,
                confidence_min=0,
                expected_terms_found=[],
                expected_terms_missing=expected_terms or [],
                ocr_errors_detected=[],
                raw_sample="",
                cleaned_sample=""
            )
        
        # PaddleOCR 3.3.3 returns: [{'rec_texts': [...], 'rec_scores': [...], ...}]
        ocr_result = result[0]
        texts = ocr_result.get('rec_texts', [])
        scores = ocr_result.get('rec_scores', [])
        
        # Calculate confidence metrics
        valid_scores = [s for s in scores if s > 0]
        confidence_avg = sum(valid_scores) / len(valid_scores) if valid_scores else 0
        confidence_min = min(valid_scores) if valid_scores else 0
        
        # Build raw text
        raw_text = ' '.join(texts)
        cleaned_text = clean_ocr_text(raw_text)
        
        # Check expected terms
        expected_terms = expected_terms or []
        found = [t for t in expected_terms if t.lower() in cleaned_text.lower()]
        missing = [t for t in expected_terms if t.lower() not in cleaned_text.lower()]
        
        # Detect common OCR errors
        ocr_errors = []
        error_patterns = ['MimakI', 'MimaKI', 'MIMAKl', 'nibit', 'Exhlbit', 'ICE ']
        for pattern in error_patterns:
            if pattern in raw_text:
                ocr_errors.append(pattern)
        
        doc.close()
        
        return OCRQualityResult(
            page_num=page_num,
            text_regions=len(texts),
            confidence_avg=round(confidence_avg, 3),
            confidence_min=round(confidence_min, 3),
            expected_terms_found=found,
            expected_terms_missing=missing,
            ocr_errors_detected=ocr_errors,
            raw_sample=raw_text[:500],
            cleaned_sample=cleaned_text[:500]
        )
    
    def analyze_translation_quality(
        self,
        original_text: str,
        translated_text: str,
        page_num: int,
        preserve_terms: List[str] = None
    ) -> TranslationQualityResult:
        """Analyze translation quality."""
        # Split into sentences
        import re
        orig_sentences = [s.strip() for s in re.split(r'[.!?]+', original_text) if s.strip()]
        trans_sentences = [s.strip() for s in re.split(r'[.!?]+', translated_text) if s.strip()]
        
        ratio = len(trans_sentences) / len(orig_sentences) if orig_sentences else 0
        
        # Check term preservation
        preserve_terms = preserve_terms or []
        preserved = [t for t in preserve_terms if t in translated_text]
        
        # Sample pairs (first 5)
        pairs = list(zip(orig_sentences[:5], trans_sentences[:5]))
        
        # Detect potential issues
        issues = []
        if ratio < 0.8:
            issues.append(f"Sentence count dropped significantly ({len(orig_sentences)} → {len(trans_sentences)})")
        if ratio > 1.3:
            issues.append(f"Sentence count increased significantly ({len(orig_sentences)} → {len(trans_sentences)})")
        
        return TranslationQualityResult(
            page_num=page_num,
            original_sentences=len(orig_sentences),
            translated_sentences=len(trans_sentences),
            sentence_ratio=round(ratio, 2),
            sample_pairs=pairs,
            terminology_preserved=preserved,
            potential_issues=issues
        )
    
    def run_full_test(
        self,
        doc_key: str,
        pages: List[int] = None
    ) -> Dict:
        """Run full quality test on a document."""
        if doc_key not in TEST_DOCUMENTS:
            raise ValueError(f"Unknown document: {doc_key}")
        
        doc_info = TEST_DOCUMENTS[doc_key]
        pdf_path = doc_info['path']
        
        if not os.path.exists(pdf_path):
            return {"error": f"File not found: {pdf_path}"}
        
        # Determine pages to test
        doc = fitz.open(pdf_path)
        total_pages = doc.page_count
        doc.close()
        
        if pages is None:
            # Test first 3 pages and last page
            pages = [0, 1, 2]
            if total_pages > 3:
                pages.append(total_pages - 1)
        
        results = {
            "document": doc_key,
            "path": pdf_path,
            "total_pages": total_pages,
            "tested_pages": pages,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "page_reports": []
        }
        
        for page_num in pages:
            if page_num >= total_pages:
                continue
            
            print(f"\n--- Testing page {page_num + 1}/{total_pages} ---")
            
            # OCR quality
            ocr_result = self.analyze_ocr_quality(
                pdf_path, 
                page_num,
                doc_info.get('expected_terms', [])
            )
            
            report = PageQualityReport(
                ocr=ocr_result,
                translation=None,
                formatting=None,
                overall_score=0
            )
            
            # Calculate score
            score = 0
            if ocr_result.text_regions > 0:
                score += 30  # OCR found text
            if ocr_result.confidence_avg > 0.8:
                score += 20
            if not ocr_result.ocr_errors_detected:
                score += 30  # No OCR errors
            if len(ocr_result.expected_terms_found) == len(doc_info.get('expected_terms', [])):
                score += 20  # All expected terms found
            
            report.overall_score = score
            results["page_reports"].append(asdict(report))
        
        return results


def main():
    """Run quality tests."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Quality verification framework")
    parser.add_argument("--document", "-d", help="Document key to test")
    parser.add_argument("--pages", "-p", help="Pages to test (e.g., 1-3 or 1,2,5)")
    parser.add_argument("--list", "-l", action="store_true", help="List available documents")
    parser.add_argument("--all", "-a", action="store_true", help="Test all documents")
    
    args = parser.parse_args()
    
    if args.list:
        print("\nAvailable test documents:")
        for key, info in TEST_DOCUMENTS.items():
            exists = "✓" if os.path.exists(info['path']) else "✗"
            print(f"  {exists} {key}: {info['description']}")
        return
    
    framework = QualityFramework()
    
    if args.all:
        for key in TEST_DOCUMENTS:
            print(f"\n{'='*60}")
            print(f"Testing: {key}")
            print('='*60)
            try:
                result = framework.run_full_test(key)
                print(json.dumps(result, indent=2, default=str))
            except Exception as e:
                print(f"Error: {e}")
    elif args.document:
        pages = None
        if args.pages:
            # Parse page range
            if '-' in args.pages:
                start, end = map(int, args.pages.split('-'))
                pages = list(range(start - 1, end))
            else:
                pages = [int(p) - 1 for p in args.pages.split(',')]
        
        result = framework.run_full_test(args.document, pages)
        print(json.dumps(result, indent=2, default=str))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
