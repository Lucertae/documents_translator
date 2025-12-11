#!/usr/bin/env python3
"""
LAC-Translate Comprehensive Benchmark & Quality Assessment Suite

This script performs end-to-end testing of the PDF translation pipeline:
1. Text Extraction Quality (native + OCR)
2. Translation Quality (OPUS-MT)
3. PDF Rendering Quality (output fidelity)

Generates detailed reports for development guidance.

Usage:
    python benchmark.py                    # Run full benchmark on all PDFs
    python benchmark.py --quick            # Quick test (2 pages per PDF)
    python benchmark.py --pdf <file.pdf>   # Test single PDF
    python benchmark.py --report           # Generate HTML report

Author: LAC-Translate Development Team
"""

import sys
import os
import json
import time
import logging
import argparse
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple
from collections import Counter
import re

# Setup path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Suppress excessive logging during benchmark
logging.basicConfig(level=logging.ERROR, format='%(levelname)s: %(message)s')

# Suppress specific warnings from pymupdf and paddleocr
import warnings
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', message='.*Font size.*')

import pymupdf

from app.core.pdf_processor import PDFProcessor
from app.core.translator import TranslationEngine, split_into_sentences


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class PageMetrics:
    """Metrics for a single page."""
    page_num: int
    is_scanned: bool
    scan_detection_reason: str
    
    # Extraction metrics
    extraction_method: str  # 'native' or 'ocr'
    extraction_time_ms: float
    text_quality_score: float
    word_count: int
    char_count: int
    
    # Translation metrics
    translation_time_ms: float
    source_words: int
    translated_words: int
    translation_ratio: float
    sentence_count: int
    
    # Rendering metrics
    render_time_ms: float
    blocks_processed: int
    lines_translated: int
    
    # Span analysis (new!)
    red_spans: int = 0           # Translated text (expected)
    black_spans: int = 0         # Original text (should be 0!)
    original_lines: int = 0      # Lines in original
    line_coverage: float = 1.0   # trans_lines / orig_lines
    
    # Quality issues detected
    issues: List[str] = field(default_factory=list)


@dataclass
class DocumentMetrics:
    """Aggregate metrics for a document."""
    filename: str
    total_pages: int
    pages_tested: int
    
    # Aggregate stats
    scanned_pages: int
    native_pages: int
    total_extraction_time_ms: float
    total_translation_time_ms: float
    total_render_time_ms: float
    total_time_ms: float
    
    avg_text_quality: float
    total_words_extracted: int
    total_words_translated: int
    
    # Page details
    page_metrics: List[PageMetrics] = field(default_factory=list)
    
    # Document-level issues
    issues: List[str] = field(default_factory=list)


@dataclass
class BenchmarkReport:
    """Complete benchmark report."""
    timestamp: str
    total_documents: int
    total_pages_tested: int
    total_time_seconds: float
    
    # Aggregate stats
    avg_extraction_time_ms: float
    avg_translation_time_ms: float
    avg_render_time_ms: float
    avg_text_quality: float
    
    # Document details
    documents: List[DocumentMetrics] = field(default_factory=list)
    
    # Summary recommendations
    recommendations: List[str] = field(default_factory=list)


# =============================================================================
# QUALITY ANALYSIS FUNCTIONS
# =============================================================================

def analyze_extraction_quality(text: str) -> Tuple[float, List[str]]:
    """
    Deep analysis of extracted text quality.
    
    Returns:
        Tuple of (quality_score 0-1, list of issues)
    """
    issues = []
    score = 1.0
    
    if not text or len(text.strip()) < 10:
        return 0.0, ["Empty or too short"]
    
    words = text.split()
    total_words = len(words)
    total_chars = len(text)
    
    # Check 1: Special character ratio
    special_chars = len(re.findall(r'[^\w\s.,;:!?\'"()\-\[\]@#$%&*+=<>/\\]', text))
    special_ratio = special_chars / total_chars if total_chars > 0 else 0
    if special_ratio > 0.1:
        issues.append(f"High special chars ({special_ratio:.1%})")
        score -= special_ratio * 2
    
    # Check 2: Single character words (fragmentation)
    single_char = sum(1 for w in words if len(w) == 1 and not w.isdigit())
    single_ratio = single_char / total_words if total_words > 0 else 0
    if single_ratio > 0.2:
        issues.append(f"Text fragmentation ({single_ratio:.1%} single chars)")
        score -= single_ratio
    
    # Check 3: Repeated characters (OCR artifacts)
    repeated = len(re.findall(r'(.)\1{4,}', text))
    if repeated > 3:
        issues.append(f"Repeated char artifacts ({repeated})")
        score -= 0.15
    
    # Check 4: Vowel ratio (for European languages)
    vowels = len(re.findall(r'[aeiouAEIOUàèìòùáéíóúäëïöüâêîôû]', text))
    vowel_ratio = vowels / total_chars if total_chars > 0 else 0
    if vowel_ratio < 0.08 and total_chars > 100:
        issues.append(f"Low vowels ({vowel_ratio:.1%}) - encoding issue?")
        score -= 0.2
    
    # Check 5: Average word length
    avg_word_len = sum(len(w) for w in words) / total_words if total_words > 0 else 0
    if avg_word_len < 2.0:
        issues.append(f"Very short words (avg {avg_word_len:.1f})")
        score -= 0.15
    elif avg_word_len > 15:
        issues.append(f"Very long words (avg {avg_word_len:.1f})")
        score -= 0.1
    
    # Check 6: Consecutive uppercase (headers or OCR errors)
    uppercase_blocks = len(re.findall(r'[A-Z]{10,}', text))
    if uppercase_blocks > 5:
        issues.append(f"Many uppercase blocks ({uppercase_blocks})")
        score -= 0.1
    
    # Check 7: Unicode ligatures in output (rendering concern)
    ligatures = len(re.findall(r'[\ufb00-\ufb06]', text))
    if ligatures > 0:
        issues.append(f"Unicode ligatures ({ligatures})")
        # Not a quality issue, just tracking
    
    return max(0.0, min(1.0, score)), issues


def analyze_translation_quality(source: str, translated: str) -> Tuple[float, List[str]]:
    """
    Analyze translation quality metrics.
    
    Returns:
        Tuple of (quality_score 0-1, list of issues)
    """
    issues = []
    score = 1.0
    
    if not translated or len(translated.strip()) < 5:
        return 0.0, ["Empty translation"]
    
    source_words = len(source.split())
    trans_words = len(translated.split())
    
    # Check 1: Length ratio (should be similar, +/- 50%)
    if source_words > 0:
        ratio = trans_words / source_words
        if ratio < 0.5:
            issues.append(f"Translation too short ({ratio:.1%})")
            score -= 0.3
        elif ratio > 2.0:
            issues.append(f"Translation too long ({ratio:.1%})")
            score -= 0.2
    
    # Check 2: Untranslated words (common for proper nouns, OK in moderation)
    source_set = set(w.lower() for w in source.split() if len(w) > 3)
    trans_set = set(w.lower() for w in translated.split() if len(w) > 3)
    overlap = source_set & trans_set
    overlap_ratio = len(overlap) / len(source_set) if source_set else 0
    if overlap_ratio > 0.5 and len(source_set) > 5:
        issues.append(f"High word overlap ({overlap_ratio:.1%}) - undertranslated?")
        score -= overlap_ratio * 0.3
    
    # Check 3: Sentence structure preservation
    source_sentences = len(split_into_sentences(source))
    trans_sentences = len(split_into_sentences(translated))
    if source_sentences > 0:
        sent_ratio = trans_sentences / source_sentences
        if sent_ratio < 0.5 or sent_ratio > 2.0:
            issues.append(f"Sentence count changed significantly ({source_sentences}→{trans_sentences})")
            score -= 0.1
    
    return max(0.0, min(1.0, score)), issues


def analyze_pdf_output(original_page: pymupdf.Page, translated_page: pymupdf.Page) -> Tuple[float, List[str], Dict]:
    """
    Analyze PDF rendering quality.
    
    Returns:
        Tuple of (quality_score 0-1, list of issues, span_stats dict)
    """
    issues = []
    score = 1.0
    
    # Get text from translated page
    trans_text = translated_page.get_text()
    trans_dict = translated_page.get_text("dict")
    
    # Get original line count for comparison
    orig_dict = original_page.get_text("dict")
    orig_lines = sum(
        len(b.get("lines", []))
        for b in orig_dict.get("blocks", [])
        if "lines" in b
    )
    
    if not trans_text or len(trans_text.strip()) < 10:
        return 0.0, ["No text in output"], {"red_spans": 0, "black_spans": 0, "original_lines": orig_lines, "translated_lines": 0}
    
    # Count spans by color
    red_spans = 0   # Translated text (should be red)
    black_spans = 0 # Original text (should be 0 if properly cleared)
    other_spans = 0
    trans_lines = 0
    
    for block in trans_dict.get("blocks", []):
        if "lines" not in block:
            continue
        for line in block["lines"]:
            trans_lines += 1
            for span in line.get("spans", []):
                text = span.get("text", "").strip()
                if not text:
                    continue
                    
                color_int = span.get("color", 0)
                r = ((color_int >> 16) & 0xFF)
                g = ((color_int >> 8) & 0xFF)
                b = (color_int & 0xFF)
                
                if r > 150 and g < 50 and b < 50:  # Red
                    red_spans += 1
                elif r < 50 and g < 50 and b < 50:  # Black
                    black_spans += 1
                else:
                    other_spans += 1
    
    span_stats = {
        "red_spans": red_spans,
        "black_spans": black_spans,
        "other_spans": other_spans,
        "original_lines": orig_lines,
        "translated_lines": trans_lines
    }
    
    # Check 1: Original text not properly removed (critical!)
    if black_spans > 0:
        issues.append(f"⚠️ CRITICAL: {black_spans} black spans (original text not removed)")
        score -= min(0.5, black_spans * 0.05)
    
    # Check 2: Line coverage
    line_coverage = trans_lines / orig_lines if orig_lines > 0 else 0
    span_stats["line_coverage"] = line_coverage
    if line_coverage < 0.8:
        issues.append(f"Low line coverage ({line_coverage:.1%}) - content missing")
        score -= (1 - line_coverage) * 0.5
    
    # Check 3: Text extraction from output (searchability)
    words = trans_text.split()
    if len(words) < 10:
        issues.append("Low searchable text in output")
        score -= 0.2
    
    # Check 4: Font variety (should have translations)
    fonts = set()
    for block in trans_dict.get("blocks", []):
        if "lines" in block:
            for line in block["lines"]:
                for span in line.get("spans", []):
                    fonts.add(span.get("font", ""))
    
    # Check 5: Unicode ligatures in output
    ligatures = len(re.findall(r'[\ufb00-\ufb06]', trans_text))
    if ligatures > 10:
        issues.append(f"Many ligatures in output ({ligatures})")
        # Minor issue, visual is usually OK
    
    # Check 4: Text overflow detection (approximate)
    # Check if any text appears cut off or truncated
    truncated = trans_text.count("...")
    if truncated > 5:
        issues.append(f"Possible text truncation ({truncated} ellipsis)")
        score -= 0.1
    
    return max(0.0, min(1.0, score)), issues, span_stats


# =============================================================================
# BENCHMARK FUNCTIONS
# =============================================================================

def benchmark_document(
    pdf_path: str,
    max_pages: Optional[int] = None,
    verbose: bool = False
) -> DocumentMetrics:
    """
    Run comprehensive benchmark on a single document.
    
    Args:
        pdf_path: Path to PDF file
        max_pages: Maximum pages to test (None = all)
        verbose: Print progress
        
    Returns:
        DocumentMetrics with all measurements
    """
    filename = Path(pdf_path).name
    
    if verbose:
        print(f"\n{'='*60}")
        print(f"Benchmarking: {filename}")
        print(f"{'='*60}")
    
    # Initialize
    doc_start = time.time()
    processor = PDFProcessor(pdf_path)
    translator = TranslationEngine(source_lang="en", target_lang="it")
    
    total_pages = processor.page_count
    pages_to_test = min(max_pages or total_pages, total_pages)
    
    doc_metrics = DocumentMetrics(
        filename=filename,
        total_pages=total_pages,
        pages_tested=pages_to_test,
        scanned_pages=0,
        native_pages=0,
        total_extraction_time_ms=0,
        total_translation_time_ms=0,
        total_render_time_ms=0,
        total_time_ms=0,
        avg_text_quality=0,
        total_words_extracted=0,
        total_words_translated=0,
        page_metrics=[],
        issues=[]
    )
    
    quality_scores = []
    
    for page_num in range(pages_to_test):
        if verbose:
            print(f"\n  Page {page_num + 1}/{pages_to_test}...")
        
        page = processor.get_page(page_num)
        page_issues = []
        
        # 1. Scan Detection
        is_scanned, scan_reason = processor._is_likely_scanned_page(page)
        if is_scanned:
            doc_metrics.scanned_pages += 1
            extraction_method = "ocr"
        else:
            doc_metrics.native_pages += 1
            extraction_method = "native"
        
        # 2. Text Extraction
        ext_start = time.time()
        extracted_text = processor.extract_text(page_num, "en")
        ext_time = (time.time() - ext_start) * 1000
        
        text_quality, text_issues = analyze_extraction_quality(extracted_text)
        page_issues.extend(text_issues)
        quality_scores.append(text_quality)
        
        word_count = len(extracted_text.split())
        char_count = len(extracted_text)
        doc_metrics.total_words_extracted += word_count
        
        # 3. Translation
        trans_start = time.time()
        
        # Translate in chunks for realistic benchmarking
        sentences = split_into_sentences(extracted_text)
        translated_text = ""
        for sent in sentences:
            translated_text += translator.translate(sent) + " "
        
        trans_time = (time.time() - trans_start) * 1000
        
        trans_word_count = len(translated_text.split())
        trans_quality, trans_issues = analyze_translation_quality(extracted_text, translated_text)
        page_issues.extend(trans_issues)
        
        translation_ratio = trans_word_count / word_count if word_count > 0 else 0
        doc_metrics.total_words_translated += trans_word_count
        
        # 4. PDF Rendering
        render_start = time.time()
        translated_doc = processor.translate_page(page_num, translator)
        render_time = (time.time() - render_start) * 1000
        
        # Analyze output with span statistics
        output_page = translated_doc[0]
        output_quality, output_issues, span_stats = analyze_pdf_output(page, output_page)
        page_issues.extend(output_issues)
        
        # Count translated elements
        output_dict = output_page.get_text("dict")
        blocks_processed = len([b for b in output_dict.get("blocks", []) if "lines" in b])
        lines_translated = sum(
            len(b.get("lines", []))
            for b in output_dict.get("blocks", [])
            if "lines" in b
        )
        
        translated_doc.close()
        
        # Record page metrics with span statistics
        page_metric = PageMetrics(
            page_num=page_num + 1,
            is_scanned=is_scanned,
            scan_detection_reason=scan_reason,
            extraction_method=extraction_method,
            extraction_time_ms=ext_time,
            text_quality_score=text_quality,
            word_count=word_count,
            char_count=char_count,
            translation_time_ms=trans_time,
            source_words=word_count,
            translated_words=trans_word_count,
            translation_ratio=translation_ratio,
            sentence_count=len(sentences),
            render_time_ms=render_time,
            blocks_processed=blocks_processed,
            lines_translated=lines_translated,
            red_spans=span_stats.get("red_spans", 0),
            black_spans=span_stats.get("black_spans", 0),
            original_lines=span_stats.get("original_lines", 0),
            line_coverage=span_stats.get("line_coverage", 1.0),
            issues=page_issues
        )
        
        doc_metrics.page_metrics.append(page_metric)
        doc_metrics.total_extraction_time_ms += ext_time
        doc_metrics.total_translation_time_ms += trans_time
        doc_metrics.total_render_time_ms += render_time
        
        if verbose:
            status = "✓" if text_quality > 0.7 else "⚠" if text_quality > 0.4 else "✗"
            print(f"    {status} {extraction_method}: {word_count} words, quality={text_quality:.2f}")
            print(f"      Extraction: {ext_time:.0f}ms, Translation: {trans_time:.0f}ms, Render: {render_time:.0f}ms")
            # Show span stats
            coverage_status = "✓" if span_stats.get("line_coverage", 1) >= 0.95 else "⚠"
            black_status = "✓" if span_stats.get("black_spans", 0) == 0 else "✗"
            print(f"      Spans: {span_stats.get('red_spans', 0)} red {black_status}, {span_stats.get('black_spans', 0)} black, coverage={span_stats.get('line_coverage', 1):.1%} {coverage_status}")
            if page_issues:
                for issue in page_issues[:3]:
                    print(f"      ⚠ {issue}")
    
    # Finalize document metrics
    doc_metrics.total_time_ms = (time.time() - doc_start) * 1000
    doc_metrics.avg_text_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
    
    processor.close()
    
    if verbose:
        print(f"\n  Summary: {doc_metrics.pages_tested} pages in {doc_metrics.total_time_ms/1000:.1f}s")
        print(f"  Avg quality: {doc_metrics.avg_text_quality:.2f}")
        print(f"  Scanned: {doc_metrics.scanned_pages}, Native: {doc_metrics.native_pages}")
    
    return doc_metrics


def generate_recommendations(report: BenchmarkReport) -> List[str]:
    """Generate development recommendations based on benchmark results."""
    recommendations = []
    
    # Analyze aggregate data
    low_quality_pages = 0
    ocr_needed = 0
    slow_translations = 0
    ligature_issues = 0
    
    for doc in report.documents:
        for page in doc.page_metrics:
            if page.text_quality_score < 0.6:
                low_quality_pages += 1
            if page.is_scanned:
                ocr_needed += 1
            if page.translation_time_ms > 5000:
                slow_translations += 1
            if any("ligature" in issue.lower() for issue in page.issues):
                ligature_issues += 1
    
    total_pages = report.total_pages_tested
    
    # Generate recommendations
    if low_quality_pages > total_pages * 0.2:
        recommendations.append(
            f"TEXT EXTRACTION: {low_quality_pages}/{total_pages} pages have low quality scores. "
            "Consider improving OCR parameters or adding post-processing."
        )
    
    if ocr_needed > total_pages * 0.5:
        recommendations.append(
            f"OCR USAGE: {ocr_needed}/{total_pages} pages require OCR. "
            "Consider optimizing PaddleOCR settings for speed."
        )
    
    if report.avg_translation_time_ms > 2000:
        recommendations.append(
            f"TRANSLATION SPEED: Average {report.avg_translation_time_ms:.0f}ms per page. "
            "Consider batch translation or model quantization."
        )
    
    if ligature_issues > 0:
        recommendations.append(
            f"RENDERING: {ligature_issues} pages have ligature issues. "
            "Consider using insert_text instead of insert_htmlbox where possible."
        )
    
    if report.avg_text_quality < 0.7:
        recommendations.append(
            f"OVERALL QUALITY: Average quality {report.avg_text_quality:.2f} is below target. "
            "Priority areas: text extraction and OCR accuracy."
        )
    
    if not recommendations:
        recommendations.append("All metrics within acceptable ranges. System performing well.")
    
    return recommendations


def run_full_benchmark(
    input_dir: str = "input",
    max_pages_per_doc: Optional[int] = None,
    single_pdf: Optional[str] = None,
    verbose: bool = True
) -> BenchmarkReport:
    """
    Run benchmark on all PDFs in input directory.
    
    Args:
        input_dir: Directory containing PDF files
        max_pages_per_doc: Limit pages per document (None = all)
        single_pdf: Test only this specific PDF
        verbose: Print progress
        
    Returns:
        Complete BenchmarkReport
    """
    start_time = time.time()
    
    # Find PDFs
    input_path = Path(input_dir)
    if single_pdf:
        pdf_files = [Path(single_pdf)]
    else:
        pdf_files = sorted(input_path.glob("*.pdf"))
    
    if not pdf_files:
        print(f"No PDF files found in {input_dir}")
        return None
    
    print(f"\n{'#'*70}")
    print(f"# LAC-TRANSLATE BENCHMARK SUITE")
    print(f"# {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*70}")
    print(f"\nFound {len(pdf_files)} PDF(s) to benchmark")
    if max_pages_per_doc:
        print(f"Testing max {max_pages_per_doc} pages per document")
    
    # Run benchmarks
    documents = []
    for pdf_path in pdf_files:
        try:
            doc_metrics = benchmark_document(
                str(pdf_path),
                max_pages=max_pages_per_doc,
                verbose=verbose
            )
            documents.append(doc_metrics)
        except Exception as e:
            print(f"\n✗ Error benchmarking {pdf_path.name}: {e}")
            continue
    
    # Aggregate results
    total_time = time.time() - start_time
    total_pages = sum(d.pages_tested for d in documents)
    
    report = BenchmarkReport(
        timestamp=datetime.now().isoformat(),
        total_documents=len(documents),
        total_pages_tested=total_pages,
        total_time_seconds=total_time,
        avg_extraction_time_ms=sum(d.total_extraction_time_ms for d in documents) / total_pages if total_pages > 0 else 0,
        avg_translation_time_ms=sum(d.total_translation_time_ms for d in documents) / total_pages if total_pages > 0 else 0,
        avg_render_time_ms=sum(d.total_render_time_ms for d in documents) / total_pages if total_pages > 0 else 0,
        avg_text_quality=sum(d.avg_text_quality for d in documents) / len(documents) if documents else 0,
        documents=documents
    )
    
    # Generate recommendations
    report.recommendations = generate_recommendations(report)
    
    return report


def print_report(report: BenchmarkReport):
    """Print formatted benchmark report."""
    print(f"\n{'='*70}")
    print("BENCHMARK RESULTS")
    print(f"{'='*70}")
    
    print(f"\nOverall Statistics:")
    print(f"  Documents tested: {report.total_documents}")
    print(f"  Pages tested: {report.total_pages_tested}")
    print(f"  Total time: {report.total_time_seconds:.1f}s")
    print(f"  Average page time: {(report.total_time_seconds*1000)/report.total_pages_tested:.0f}ms")
    
    print(f"\nPerformance Metrics (per page average):")
    print(f"  Extraction: {report.avg_extraction_time_ms:.0f}ms")
    print(f"  Translation: {report.avg_translation_time_ms:.0f}ms")
    print(f"  Rendering: {report.avg_render_time_ms:.0f}ms")
    
    print(f"\nQuality Metrics:")
    print(f"  Average text quality: {report.avg_text_quality:.2%}")
    
    print(f"\nPer-Document Summary:")
    for doc in report.documents:
        status = "✓" if doc.avg_text_quality > 0.7 else "⚠"
        print(f"  {status} {doc.filename}")
        print(f"      Pages: {doc.pages_tested}/{doc.total_pages} (Scanned: {doc.scanned_pages}, Native: {doc.native_pages})")
        print(f"      Quality: {doc.avg_text_quality:.2%}, Words: {doc.total_words_extracted}→{doc.total_words_translated}")
        print(f"      Time: {doc.total_time_ms/1000:.1f}s")
        
        # Show top issues
        all_issues = []
        for page in doc.page_metrics:
            all_issues.extend(page.issues)
        if all_issues:
            issue_counts = Counter(all_issues)
            top_issues = issue_counts.most_common(3)
            print(f"      Issues: {', '.join(f'{i[0]} ({i[1]}x)' for i in top_issues)}")
    
    print(f"\n{'='*70}")
    print("DEVELOPMENT RECOMMENDATIONS")
    print(f"{'='*70}")
    for i, rec in enumerate(report.recommendations, 1):
        print(f"\n{i}. {rec}")
    
    print(f"\n{'='*70}")


def save_report_json(report: BenchmarkReport, output_path: str = "benchmark_report.json"):
    """Save report as JSON for further analysis."""
    
    def convert_to_dict(obj):
        if hasattr(obj, '__dict__'):
            return {k: convert_to_dict(v) for k, v in obj.__dict__.items()}
        elif isinstance(obj, list):
            return [convert_to_dict(i) for i in obj]
        else:
            return obj
    
    with open(output_path, 'w') as f:
        json.dump(convert_to_dict(report), f, indent=2, default=str)
    
    print(f"\nReport saved to: {output_path}")


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="LAC-Translate Benchmark Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python benchmark.py                    # Full benchmark
  python benchmark.py --quick            # Quick test (2 pages each)
  python benchmark.py --pdf input/doc.pdf   # Single document
  python benchmark.py --output report.json  # Custom output
        """
    )
    
    parser.add_argument("--quick", action="store_true",
                       help="Quick mode: test only 2 pages per document")
    parser.add_argument("--pdf", type=str,
                       help="Benchmark specific PDF file")
    parser.add_argument("--max-pages", type=int, default=None,
                       help="Maximum pages per document")
    parser.add_argument("--input-dir", type=str, default="input",
                       help="Input directory (default: input)")
    parser.add_argument("--output", type=str, default="benchmark_report.json",
                       help="Output JSON file (default: benchmark_report.json)")
    parser.add_argument("--quiet", action="store_true",
                       help="Minimal output")
    
    args = parser.parse_args()
    
    # Determine max pages
    max_pages = args.max_pages
    if args.quick and max_pages is None:
        max_pages = 2
    
    # Run benchmark
    report = run_full_benchmark(
        input_dir=args.input_dir,
        max_pages_per_doc=max_pages,
        single_pdf=args.pdf,
        verbose=not args.quiet
    )
    
    if report:
        print_report(report)
        save_report_json(report, args.output)


if __name__ == "__main__":
    main()
