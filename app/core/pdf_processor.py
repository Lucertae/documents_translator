"""
PDF processing module - RapidOCR Edition
Handles PDF loading, text extraction, OCR, and manipulation with superior quality.

SPAN-LEVEL FORMATTING PRESERVATION:
This module preserves formatting at the span level, not just line level.
Bold, italic, color, and size are tracked per-segment and
intelligently mapped to the translated text using proportional allocation.

OCR Engine: RapidOCR (ONNX Runtime + PP-OCRv4/v5)
- ~1-3 secondi per pagina su CPU
- Pipeline: text detection + direction classification + text recognition
- Modelli PP-OCRv5 (detection) + PP-OCRv4 (recognition EN)
- Nessun server esterno (tutto in-process)
"""
import logging
import math
import re
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
import pymupdf
from PIL import Image

# Import sentence-aware translation helpers
from .translator import split_into_sentences, align_sentences_to_lines

# Import centralized configuration
from .config import (
    DEFAULT_OCR_CONFIG,
    DEFAULT_TEXT_QUALITY_CONFIG,
    DEFAULT_SCAN_DETECTION_CONFIG,
    DEFAULT_PARAGRAPH_CONFIG,
)

# Import formatting classes
from .formatting import SpanFormat, LineFormatInfo

# Import formatting utilities
from .format_utils import (
    map_formatting_to_translation,
    normalize_text_for_pdf as _normalize_text_for_pdf,
    escape_html as _escape_html,
)

# Import OCR post-processing
from .ocr_utils import post_process_ocr_text

# Import Sentry integration
from .sentry_integration import capture_exception

# Import pymupdf4llm column detection (battle-tested multi-column layout analysis)
try:
    from pymupdf4llm.helpers.multi_column import column_boxes
    COLUMN_BOXES_AVAILABLE = True
except ImportError:
    COLUMN_BOXES_AVAILABLE = False
    logging.warning("pymupdf4llm not available — falling back to heuristic block merging")

# Import pymupdf4llm heading detection (document-level font-size analysis)
try:
    from pymupdf4llm import IdentifyHeaders
    IDENTIFY_HEADERS_AVAILABLE = True
except ImportError:
    IDENTIFY_HEADERS_AVAILABLE = False
    logging.warning("pymupdf4llm.IdentifyHeaders not available — using heuristic heading detection")


# NOTE: SpanFormat and LineFormatInfo classes moved to formatting.py
# NOTE: map_formatting_to_translation and helpers moved to format_utils.py
# NOTE: detect_title_or_heading moved to format_utils.py (simplified version)


def _detect_page_alignment(text_dict: dict, page_width: float) -> dict:
    """
    Detect text alignment at the page level by analyzing line bounding boxes.
    
    Returns a dict with:
        - 'alignment': 'left', 'justify', 'center', or 'right'
        - 'left_margin': most common left x position
        - 'right_margin': most common right x position
        - 'indent_x0s': set of common x0 positions (for indentation detection)
    """
    from collections import Counter
    
    left_edges = []
    right_edges = []
    
    for block in text_dict.get("blocks", []):
        if "lines" not in block:
            continue
        for line in block.get("lines", []):
            spans = line.get("spans", [])
            line_text = "".join(s.get("text", "") for s in spans).strip()
            # Skip very short lines (titles, list items, etc.)
            if len(line_text) < 30:
                continue
            bbox = line.get("bbox", (0, 0, 0, 0))
            left_edges.append(round(bbox[0], 0))
            right_edges.append(round(bbox[2], 0))
    
    result = {
        'alignment': 'left',
        'left_margin': 0,
        'right_margin': page_width,
        'indent_x0s': set(),
    }
    
    if not left_edges or not right_edges:
        return result
    
    left_counts = Counter(left_edges)
    right_counts = Counter(right_edges)
    
    most_common_left = left_counts.most_common(1)[0][0]
    most_common_right = right_counts.most_common(1)[0][0]
    
    result['left_margin'] = most_common_left
    result['right_margin'] = most_common_right
    
    # Collect all unique x0 positions for indentation tracking
    all_x0_counts = Counter(round(bbox[0], 0) for block in text_dict.get("blocks", [])
                            if "lines" in block
                            for line in block.get("lines", [])
                            for bbox in [line.get("bbox", (0, 0, 0, 0))]
                            if "".join(s.get("text", "") for s in line.get("spans", [])).strip())
    result['indent_x0s'] = set(all_x0_counts.keys())
    
    # Calculate right-edge standard deviation to detect justification
    if len(right_edges) >= 3:
        mean_right = sum(right_edges) / len(right_edges)
        right_std = (sum((r - mean_right)**2 for r in right_edges) / len(right_edges)) ** 0.5
        
        if right_std < 10:
            result['alignment'] = 'justify'
        elif right_std < 25:
            # Check if most lines reach close to the right margin
            close_to_margin = sum(1 for r in right_edges if abs(r - most_common_right) < 15)
            if close_to_margin > len(right_edges) * 0.6:
                result['alignment'] = 'justify'
    
    return result


# Bullet/list patterns for structural detection
_LIST_PATTERNS = [
    re.compile(r'^[•●○◦▪▸▹–—]\s'),           # Unicode bullets
    re.compile(r'^-\s(?![0-9])'),               # Hyphen bullet (but not negative numbers)
    re.compile(r'^\d{1,3}[.)]\s'),              # Numbered list: "1. " or "1) "
    re.compile(r'^[a-z][.)]\s'),                # Lettered: "a) " or "a. "
    re.compile(r'^[A-Z][.)]\s(?![A-Z])'),       # Cap lettered: "A) " (but not abbreviations)
    re.compile(r'^(?:i{1,3}|iv|vi{0,3}|ix|x)[.)]\s', re.IGNORECASE),  # Roman numerals
    re.compile(r'^\(\d{1,3}\)\s'),              # Parenthesized number: "(1) "
    re.compile(r'^\([a-z]\)\s'),                # Parenthesized letter: "(a) "
]


def _is_list_item(text: str) -> bool:
    """Check if text starts with a bullet or list marker."""
    text = text.strip()
    return any(pat.match(text) for pat in _LIST_PATTERNS)


def _extract_list_prefix(text: str) -> tuple:
    """
    Extract list prefix from text if it's a list item.
    
    Returns (prefix, body) or (None, text) if not a list item.
    """
    text = text.strip()
    for pat in _LIST_PATTERNS:
        m = pat.match(text)
        if m:
            return text[:m.end()], text[m.end():]
    return None, text


def _is_likely_footnote_marker(text: str, font_size: float, page_height: float, y_pos: float) -> bool:
    """
    Improved footnote detection. A line is a footnote reference only if:
    - It starts with a number followed by space
    - AND (font is smaller than body text OR it's in the bottom 30% of the page)
    - AND the number is reasonable (1-99)
    
    This prevents false positives on normal text starting with numbers
    like "3 main points" or "2020 was a leap year".
    """
    m = re.match(r'^(\d{1,2})\s', text.strip())
    if not m:
        return False
    
    num = int(m.group(1))
    if num < 1 or num > 99:
        return False
    
    # Must be either small font or at bottom of page
    is_small_font = font_size < 9.5
    is_bottom_of_page = y_pos > page_height * 0.70
    
    return is_small_font or is_bottom_of_page


# OCR integration via RapidOCR (ONNX Runtime)
try:
    from .rapid_ocr import RapidOcrEngine
    _ocr_engine_instance = RapidOcrEngine()
    OCR_AVAILABLE = _ocr_engine_instance.is_available()
    if not OCR_AVAILABLE:
        logging.warning("RapidOCR not ready - run: pip install rapidocr onnxruntime")
except ImportError as e:
    OCR_AVAILABLE = False
    _ocr_engine_instance = None
    logging.warning(f"OCR not available: {e}")

# RapidDoc integration for structured document parsing (layout + OCR + table)
try:
    from .rapid_doc_engine import RapidDocEngine
    _rapiddoc_engine_instance = RapidDocEngine()
    RAPIDDOC_AVAILABLE = _rapiddoc_engine_instance.is_available()
    if RAPIDDOC_AVAILABLE:
        logging.info("RapidDoc engine available — structured document parsing enabled")
    else:
        logging.info("RapidDoc not available, using plain RapidOCR for scanned pages")
except ImportError as e:
    RAPIDDOC_AVAILABLE = False
    _rapiddoc_engine_instance = None
    logging.info(f"RapidDoc not available: {e}")
except Exception as e:
    RAPIDDOC_AVAILABLE = False
    _rapiddoc_engine_instance = None
    logging.warning(f"RapidDoc initialization error: {e}")


class PDFProcessor:
    """
    Professional PDF processor with RapidOCR (fast ONNX-based OCR).
    Supports normal PDFs and scanned documents via RapidOCR.
    
    RapidOCR Advantages:
    - ~1-3 sec/page on CPU (vs 5+ min with GLM-OCR)
    - PP-OCRv4/v5 models via ONNX Runtime
    - No external server needed (in-process)
    - Automatic model download (~15 MB)
    """
    
    def __init__(self, pdf_path: str):
        """
        Initialize PDF processor.
        
        Args:
            pdf_path: Path to PDF file
        """
        self.pdf_path = pdf_path
        self.document = None
        self.page_count = 0
        self._hdr_info = None  # Lazy-initialized IdentifyHeaders
        self._load_document()
        
    def _load_document(self) -> None:
        """Load PDF document into memory."""
        try:
            self.document = pymupdf.open(self.pdf_path)
            self.page_count = self.document.page_count
            logging.info(f"PDF loaded: {self.pdf_path} ({self.page_count} pages)")
        except Exception as e:
            capture_exception(e, context={
                "operation": "load_pdf",
                "pdf_path": self.pdf_path,
            }, tags={"component": "pdf_processor"})
            logging.error(f"Failed to load PDF: {e}")
            raise

    def _get_hdr_info(self):
        """Lazy-initialize document-level heading detector.
        
        Uses pymupdf4llm.IdentifyHeaders to scan the entire document and
        determine heading levels based on font size frequency analysis.
        The most common font size = body text; larger sizes = headings.
        
        Returns:
            IdentifyHeaders instance, or None if not available.
        """
        if self._hdr_info is None and IDENTIFY_HEADERS_AVAILABLE and self.document:
            try:
                self._hdr_info = IdentifyHeaders(self.document, max_levels=4)
                logging.info(
                    f"IdentifyHeaders initialized: body_limit={self._hdr_info.body_limit}, "
                    f"header_levels={self._hdr_info.header_id}"
                )
            except Exception as e:
                logging.warning(f"IdentifyHeaders initialization failed: {e}")
                self._hdr_info = False  # Sentinel: don't retry
        return self._hdr_info if self._hdr_info else None
    
    def get_page(self, page_num: int) -> pymupdf.Page:
        """Get specific page from document."""
        if 0 <= page_num < self.page_count:
            return self.document[page_num]
        raise IndexError(f"Page {page_num} out of range (0-{self.page_count-1})")
    
    def _is_likely_scanned_page(self, page: pymupdf.Page) -> Tuple[bool, str]:
        """
        Intelligent detection of scanned/image-based pages.
        
        Uses multiple heuristics to determine if a page needs OCR:
        1. Image coverage ratio (scans are typically one big image)
        2. Text layer presence and quality
        3. Font embedding analysis
        
        Returns:
            Tuple of (is_scanned: bool, reason: str)
        """
        page_rect = page.rect
        page_area = page_rect.width * page_rect.height
        
        if page_area <= 0:
            return False, "invalid_page"
        
        # Analyze images on page
        image_list = page.get_images(full=True)
        total_image_area = 0
        large_images = 0
        
        for img in image_list:
            try:
                xref = img[0]
                # Get image bbox by finding where it's used on the page
                img_rects = page.get_image_rects(xref)
                for rect in img_rects:
                    img_area = rect.width * rect.height
                    total_image_area += img_area
                    # Large image = covers more than 50% of page
                    if img_area > page_area * 0.5:
                        large_images += 1
            except Exception:
                continue
        
        image_coverage = total_image_area / page_area if page_area > 0 else 0
        
        # Analyze text layer
        text_dict = page.get_text("dict")
        text_blocks = [b for b in text_dict.get("blocks", []) if "lines" in b]
        total_chars = 0
        total_words = 0
        
        for block in text_blocks:
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span.get("text", "")
                    total_chars += len(text)
                    total_words += len(text.split())
        
        # Decision logic
        # Case 1: Page is mostly one big image with little/no text
        if large_images >= 1 and total_words < 10:
            return True, f"large_image_detected (coverage={image_coverage:.1%}, words={total_words})"
        
        # Case 2: High image coverage (>70%) with minimal text
        if image_coverage > 0.7 and total_words < 20:
            return True, f"high_image_coverage ({image_coverage:.1%}, words={total_words})"
        
        # Case 3: Almost full page image (>90%)
        if image_coverage > 0.9:
            return True, f"full_page_image ({image_coverage:.1%})"
        
        # Case 4: No text at all but has images
        if total_chars < 5 and len(image_list) > 0:
            return True, f"no_text_with_images (chars={total_chars})"
        
        return False, f"native_pdf (coverage={image_coverage:.1%}, words={total_words})"
    
    def _assess_text_quality(self, text: str) -> Tuple[float, str]:
        """
        Assess the quality of extracted text to detect garbled/corrupted text.
        
        Returns:
            Tuple of (quality_score: 0.0-1.0, issues: str)
        """
        if not text or len(text.strip()) < 5:
            return 0.0, "empty_or_too_short"
        
        import re
        
        # Count meaningful words (2+ letters, mostly alphabetic)
        words = text.split()
        total_words = len(words)
        
        if total_words == 0:
            return 0.0, "no_words"
        
        # Check for common text quality issues
        issues = []
        
        # Issue 1: Too many special characters (encoding problems)
        special_chars = len(re.findall(r'[^\w\s.,;:!?\'"()-]', text))
        special_ratio = special_chars / len(text) if len(text) > 0 else 0
        if special_ratio > 0.15:
            issues.append(f"high_special_chars({special_ratio:.1%})")
        
        # Issue 2: Too many single-character "words" (fragmented text)
        single_char_words = sum(1 for w in words if len(w) == 1 and not w.isdigit())
        single_char_ratio = single_char_words / total_words if total_words > 0 else 0
        if single_char_ratio > 0.3:
            issues.append(f"fragmented({single_char_ratio:.1%})")
        
        # Issue 3: Repeated characters (OCR artifacts like "lllll" or ".......")
        repeated_pattern = len(re.findall(r'(.)\1{4,}', text))
        if repeated_pattern > 2:
            issues.append(f"repeated_chars({repeated_pattern})")
        
        # Issue 4: Very few vowels (indicates non-text or encoding issues for European languages)
        vowels = len(re.findall(r'[aeiouAEIOUàèìòùáéíóúäëïöü]', text))
        vowel_ratio = vowels / len(text) if len(text) > 0 else 0
        if vowel_ratio < 0.1 and len(text) > 50:
            issues.append(f"low_vowels({vowel_ratio:.1%})")
        
        # Issue 5: Average word length too short or too long
        avg_word_len = sum(len(w) for w in words) / total_words if total_words > 0 else 0
        if avg_word_len < 2.5 or avg_word_len > 15:
            issues.append(f"unusual_word_length({avg_word_len:.1f})")
        
        # Calculate quality score (1.0 = perfect, 0.0 = garbage)
        quality = 1.0
        quality -= special_ratio * 2  # Heavy penalty for special chars
        quality -= single_char_ratio * 1.5  # Penalty for fragmentation
        quality -= min(0.3, repeated_pattern * 0.1)  # Penalty for artifacts
        if vowel_ratio < 0.1:
            quality -= 0.2
        
        quality = max(0.0, min(1.0, quality))
        
        return quality, "; ".join(issues) if issues else "good"
    
    def extract_text(self, page_num: int, ocr_language: str = "en") -> str:
        """
        Intelligent text extraction with automatic OCR detection.
        
        This method automatically determines the best extraction strategy:
        1. Detects if page is scanned/image-based
        2. Assesses quality of extracted text
        3. Falls back to OCR when native extraction is insufficient
        
        Args:
            page_num: Page number to extract from
            ocr_language: Language code for OCR (used for logging)
            
        Returns:
            Extracted text with best possible quality
        """
        page = self.get_page(page_num)
        
        # Step 1: Analyze page structure
        is_scanned, scan_reason = self._is_likely_scanned_page(page)
        
        if is_scanned:
            logging.info(f"Page {page_num + 1}: Detected as scanned ({scan_reason}), using OCR directly")
            # Prefer RapidDoc for structured text extraction
            if RAPIDDOC_AVAILABLE:
                try:
                    text = _rapiddoc_engine_instance.extract_page_text(
                        open(self.pdf_path, 'rb').read(),
                        page_num=page_num,
                        parse_method='auto',
                    )
                    if text and len(text.strip()) > 10:
                        logging.info(f"Page {page_num + 1}: RapidDoc extracted {len(text)} chars")
                        return text
                except Exception as e:
                    logging.warning(f"Page {page_num + 1}: RapidDoc extraction failed: {e}")
            # Fallback to plain RapidOCR
            if OCR_AVAILABLE:
                text = self._extract_via_ocr(page, ocr_language)
                if text and len(text.strip()) > 10:
                    return text
            return "[Scanned page - OCR not available]"
        
        # Step 2: Try native text extraction methods
        best_text = ""
        best_quality = 0.0
        
        extraction_methods = [
            ("standard", lambda: page.get_text("text")),
            ("whitespace", lambda: page.get_text("text", flags=pymupdf.TEXT_PRESERVE_WHITESPACE)),
            ("dehyphenate", lambda: page.get_text("text", flags=pymupdf.TEXT_DEHYPHENATE | pymupdf.TEXT_PRESERVE_WHITESPACE)),
            ("blocks", lambda: self._extract_from_blocks(page)),
            ("dict", lambda: self._extract_from_dict(page)),
            ("words", lambda: self._extract_from_words(page)),
        ]
        
        for method_name, extractor in extraction_methods:
            try:
                text = extractor()
                if text and len(text.strip()) > 10:
                    quality, issues = self._assess_text_quality(text)
                    logging.debug(f"Page {page_num + 1} [{method_name}]: quality={quality:.2f}, issues={issues}")
                    
                    if quality > best_quality:
                        best_quality = quality
                        best_text = text
                    
                    # If we found high-quality text, no need to try more methods
                    if quality > 0.8:
                        logging.info(f"Page {page_num + 1}: High-quality text via {method_name} (q={quality:.2f})")
                        return text
            except Exception as e:
                logging.debug(f"Method {method_name} failed: {e}")
                continue
        
        # Step 3: Decide if OCR is needed based on quality
        MIN_ACCEPTABLE_QUALITY = 0.5
        MIN_WORD_COUNT = 15
        
        word_count = len(best_text.split()) if best_text else 0
        
        if best_quality >= MIN_ACCEPTABLE_QUALITY and word_count >= MIN_WORD_COUNT:
            logging.info(f"Page {page_num + 1}: Using native text (q={best_quality:.2f}, words={word_count})")
            return best_text
        
        # Step 4: Native extraction insufficient, try OCR
        if OCR_AVAILABLE:
            logging.info(f"Page {page_num + 1}: Native text quality too low (q={best_quality:.2f}, words={word_count}), trying OCR")
            ocr_text = self._extract_via_ocr(page, ocr_language)
            
            if ocr_text:
                ocr_quality, ocr_issues = self._assess_text_quality(ocr_text)
                ocr_words = len(ocr_text.split())
                
                # Use OCR if it's better than native extraction
                if ocr_quality > best_quality or ocr_words > word_count * 1.5:
                    logging.info(f"Page {page_num + 1}: OCR provided better results (q={ocr_quality:.2f}, words={ocr_words})")
                    return ocr_text
        
        # Step 5: Return best available result
        if best_text and len(best_text.strip()) > 10:
            logging.info(f"Page {page_num + 1}: Using best available text (q={best_quality:.2f})")
            return best_text
        
        logging.warning(f"Page {page_num + 1}: No text extracted")
        return "[No extractable text]"
    
    def _extract_from_blocks(self, page: pymupdf.Page) -> str:
        """Extract text from blocks."""
        blocks = page.get_text("blocks", flags=pymupdf.TEXT_DEHYPHENATE)
        parts = []
        for block in blocks:
            if len(block) > 4:
                text_part = block[4]
                if text_part and text_part.strip() and len(text_part.strip()) > 2:
                    parts.append(text_part)
        return " ".join(parts)
    
    def _extract_from_dict(self, page: pymupdf.Page) -> str:
        """Extract text from dictionary structure."""
        text_dict = page.get_text("dict")
        parts = []
        for block in text_dict.get("blocks", []):
            if "lines" in block:
                for line in block["lines"]:
                    if "spans" in line:
                        for span in line["spans"]:
                            if "text" in span and span["text"].strip():
                                parts.append(span["text"])
        return " ".join(parts)
    
    def _extract_from_words(self, page: pymupdf.Page) -> str:
        """Extract text from word list."""
        words = page.get_text("words")
        if words and len(words) > 10:
            return " ".join([word[4] for word in words if word[4].strip()])
        return ""
    
    def _extract_via_ocr(self, page: pymupdf.Page, language: str) -> str:
        """
        Extract text using RapidOCR, con preprocessing robusto.
        
        Lavora direttamente sulla pagina PyMuPDF senza scrivere PDF temporanei.
        Logga le caratteristiche del PNG preprocessato.
        """
        global _ocr_engine_instance
        if _ocr_engine_instance is None:
            logging.warning("RapidOCR engine not available")
            return ""
        try:
            logging.info(f"RapidOCR extraction (lang={language}) [preprocessing attivo]")
            from .preprocess_for_ocr import preprocess_page_from_pymupdf, DEFAULT_DPI
            
            # Preprocessa direttamente dalla pagina (no file temporanei)
            # DPI 300: coerente con max_side_len=3000 dell'engine RapidOCR
            png_bytes, info = preprocess_page_from_pymupdf(page, dpi=DEFAULT_DPI)
            
            logging.info(
                f"PNG per OCR: {info['width']}x{info['height']} px | "
                f"DPI={info['dpi']} | Mode={info['mode']} | "
                f"Size={info['file_size_kb']} KB"
            )
            
            # Usa RapidOCR per il riconoscimento
            text = _ocr_engine_instance.recognize_document_page(
                png_bytes,
                detect_tables=True
            )
            
            if text:
                # post_process_ocr_text include già clean_ocr_text come primo passo
                text = post_process_ocr_text(text)
                logging.info(f"RapidOCR OK: {len(text)} chars")
                return text
            
            logging.warning("RapidOCR returned no text")
            return ""
            
        except Exception as e:
            capture_exception(e, context={
                "operation": "rapidocr_extract",
                "language": language,
            }, tags={"component": "ocr"})
            logging.warning(f"RapidOCR failed: {e}")
            return ""
    
    def render_page(self, page_num: int, zoom: float = 1.0) -> Tuple[bytes, int, int]:
        """
        Render page as PNG image.
        
        Args:
            page_num: Page number to render
            zoom: Zoom factor (1.0 = 100%)
            
        Returns:
            Tuple of (PNG bytes, width, height)
        """
        page = self.get_page(page_num)
        matrix = pymupdf.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=matrix)
        
        img_bytes = pix.tobytes("png")
        return img_bytes, pix.width, pix.height
    
    # ------------------------------------------------------------------
    # Markdown element parser for RapidDoc output
    # ------------------------------------------------------------------
    
    @staticmethod
    def _parse_rapiddoc_markdown(md_text: str) -> List[Dict[str, Any]]:
        """
        Parse RapidDoc's Markdown output into structured elements.
        
        Each element is a dict with:
        - type: 'heading', 'paragraph', 'table', 'empty'
        - level: heading level (1-6) for headings, 0 for others
        - text: the text content (Markdown markers stripped)
        - raw: original Markdown text
        
        Returns:
            List of elements in document order
        """
        elements = []
        lines = md_text.split('\n')
        current_paragraph: List[str] = []
        in_table = False
        table_lines: List[str] = []
        
        def flush_paragraph():
            nonlocal current_paragraph
            if current_paragraph:
                text = ' '.join(current_paragraph).strip()
                if text:
                    elements.append({
                        'type': 'paragraph',
                        'level': 0,
                        'text': text,
                        'raw': '\n'.join(current_paragraph),
                    })
                current_paragraph = []
        
        def flush_table():
            nonlocal table_lines, in_table
            if table_lines:
                elements.append({
                    'type': 'table',
                    'level': 0,
                    'text': '\n'.join(table_lines),
                    'raw': '\n'.join(table_lines),
                })
                table_lines = []
            in_table = False
        
        for line in lines:
            stripped = line.strip()
            
            # Empty line: flush paragraph
            if not stripped:
                if in_table:
                    flush_table()
                flush_paragraph()
                continue
            
            # Table line (starts with |)
            if stripped.startswith('|'):
                if not in_table:
                    flush_paragraph()
                in_table = True
                # Skip separator lines like |---|---|
                if re.match(r'^\|[\s\-:|]+\|$', stripped):
                    continue
                table_lines.append(stripped)
                continue
            
            if in_table:
                flush_table()
            
            # Heading
            heading_match = re.match(r'^(#{1,6})\s+(.+)', stripped)
            if heading_match:
                flush_paragraph()
                level = len(heading_match.group(1))
                text = heading_match.group(2).strip()
                elements.append({
                    'type': 'heading',
                    'level': level,
                    'text': text,
                    'raw': stripped,
                })
                continue
            
            # Image reference (skip)
            if stripped.startswith('!['):
                continue
            
            # Regular text line → accumulate into paragraph
            current_paragraph.append(stripped)
        
        # Flush remaining
        if in_table:
            flush_table()
        flush_paragraph()
        
        return elements
    
    # ------------------------------------------------------------------
    # RapidDoc-based scanned page translation (structured output)
    # ------------------------------------------------------------------
    
    def _translate_scanned_page_rapiddoc(
        self,
        new_doc: pymupdf.Document,
        page: pymupdf.Page,
        page_num: int,
        translator,
        text_color: Tuple[float, float, float] = (0, 0, 0),
        ocr_language: str = "en"
    ) -> pymupdf.Document:
        """
        Translate a scanned page using RapidDoc (structured document parsing).
        
        Unlike plain RapidOCR, RapidDoc provides:
        - Heading detection (# / ## / ###) via PP-DocLayoutV2 layout analysis
        - Table recognition (UNET + SLANET_PLUS)
        - Reading order restoration
        - Proper paragraph segmentation
        
        Strategy:
        1. RapidDoc extracts structured Markdown from the page
        2. Parse Markdown into elements (headings, paragraphs, tables)
        3. Translate each element preserving its semantic role
        4. Create clean page with proper typographic hierarchy
        
        Args:
            new_doc: Document to modify
            page: Original page to translate
            page_num: Page number (for logging)
            translator: Translation engine
            text_color: Color for translated text
            ocr_language: Language code (for logging)
            
        Returns:
            Document with translated structured content
        """
        global _rapiddoc_engine_instance
        
        if not RAPIDDOC_AVAILABLE or _rapiddoc_engine_instance is None:
            logging.warning(f"Page {page_num + 1}: RapidDoc not available, falling back to RapidOCR")
            return self._translate_scanned_page(
                new_doc, page, page_num, translator, text_color, ocr_language
            )
        
        try:
            # ============================================
            # STEP 1: Read original PDF bytes for RapidDoc
            # ============================================
            page_rect = page.rect
            page_width = page_rect.width
            page_height = page_rect.height
            
            # Read original PDF bytes
            pdf_bytes = open(self.pdf_path, 'rb').read()
            
            logging.info(f"Page {page_num + 1}: Using RapidDoc for structured extraction")
            
            # ============================================
            # STEP 2: Extract structured Markdown via RapidDoc
            # ============================================
            md_content, metadata = _rapiddoc_engine_instance.extract_page_markdown(
                pdf_bytes,
                page_num=page_num,
                parse_method='auto',
                table_enable=True,
                formula_enable=False,
            )
            
            if not md_content or len(md_content.strip()) < 5:
                logging.warning(f"Page {page_num + 1}: RapidDoc returned no content, falling back to RapidOCR")
                return self._translate_scanned_page(
                    new_doc, page, page_num, translator, text_color, ocr_language
                )
            
            logging.info(
                f"Page {page_num + 1}: RapidDoc extracted {len(md_content)} chars, "
                f"{metadata['num_elements']} elements in {metadata['elapsed']:.1f}s"
            )
            
            # Detect multi-column layout — prefer column_boxes (robust,
            # C-native) and fall back to RapidDoc block analysis for
            # scanned pages where PyMuPDF has no native text layer.
            detected_columns = 1
            col_x_ranges: list = []
            layout_hints = {'centered': False, 'sparse': False, 'content_y_range': None}
            if COLUMN_BOXES_AVAILABLE:
                try:
                    cb_rects = column_boxes(page, no_image_text=True)
                    if len(cb_rects) > 1:
                        detected_columns = len(cb_rects)
                        col_x_ranges = [(r.x0, r.x1) for r in cb_rects]
                except Exception:
                    pass
            if detected_columns == 1 and metadata.get('block_bboxes'):
                detected_columns, col_x_ranges = _rapiddoc_engine_instance.detect_column_count(
                    metadata['block_bboxes'],
                    metadata.get('page_size'),
                )
            if metadata.get('block_bboxes'):
                layout_hints = _rapiddoc_engine_instance.analyze_layout(
                    metadata['block_bboxes'],
                    metadata.get('page_size'),
                )
                if detected_columns > 1:
                    logging.info(
                        f"Page {page_num + 1}: Detected {detected_columns}-column layout "
                        f"(x-ranges: {[(f'{x0:.0f}-{x1:.0f}') for x0, x1 in col_x_ranges]})"
                    )
                if layout_hints.get('centered'):
                    logging.info(f"Page {page_num + 1}: Layout is centered")
                if layout_hints.get('sparse'):
                    logging.info(f"Page {page_num + 1}: Layout is sparse (cover-like)")
            
            # ============================================
            # STEP 3: Parse Markdown into structured elements
            # ============================================
            elements = self._parse_rapiddoc_markdown(md_content)
            
            if not elements:
                logging.warning(f"Page {page_num + 1}: No elements parsed from RapidDoc output")
                return self._translate_scanned_page(
                    new_doc, page, page_num, translator, text_color, ocr_language
                )
            
            logging.info(
                f"Page {page_num + 1}: Parsed {len(elements)} elements "
                f"({sum(1 for e in elements if e['type'] == 'heading')} headings, "
                f"{sum(1 for e in elements if e['type'] == 'paragraph')} paragraphs, "
                f"{sum(1 for e in elements if e['type'] == 'table')} tables)"
            )
            
            # ============================================
            # STEP 4: Translate each element
            # ============================================
            translated_elements = []
            for elem in elements:
                if elem['type'] == 'table':
                    # For tables: translate cell-by-cell
                    translated_table = self._translate_table_element(elem, translator)
                    translated_elements.append(translated_table)
                elif elem['text'] and len(elem['text'].strip()) >= 2:
                    try:
                        translated = translator.translate(elem['text'])
                        if translated and translated.strip():
                            translated_elements.append({
                                **elem,
                                'text': translated.strip(),
                            })
                        else:
                            translated_elements.append(elem)
                    except Exception as e:
                        logging.warning(f"Translation failed for element: {e}")
                        translated_elements.append(elem)
                else:
                    translated_elements.append(elem)
            
            logging.info(f"Page {page_num + 1}: Translated {len(translated_elements)} elements")
            
            # ============================================
            # STEP 5: Build single HTML document and render
            # ============================================
            # Instead of inserting elements one-by-one (which wastes space
            # on height estimation and causes overflow), build ALL content
            # as a single HTML document. PyMuPDF's insert_htmlbox() with
            # scale_low=0 will auto-scale the content to fit the page.
            
            new_page = new_doc[0]
            
            # Clear everything — draw white rectangle over entire page
            new_page.draw_rect(page_rect, color=(1, 1, 1), fill=(1, 1, 1))
            
            # Layout classification
            is_centered = layout_hints.get('centered', False)
            is_sparse = layout_hints.get('sparse', False)
            
            # Adaptive margins — tighter for dense content
            total_chars = sum(len(e.get('text', '')) for e in translated_elements)
            is_dense = total_chars > 2000 or len(translated_elements) > 20
            
            if is_dense:
                margin_lr = max(28, page_width * 0.04)
                margin_top = max(30, page_height * 0.035)
                margin_bottom = max(30, page_height * 0.035)
            elif is_sparse:
                # Sparse/cover pages: generous margins
                margin_lr = max(50, page_width * 0.08)
                margin_top = max(40, page_height * 0.045)
                margin_bottom = max(40, page_height * 0.045)
            else:
                margin_lr = max(36, page_width * 0.06)
                margin_top = max(40, page_height * 0.045)
                margin_bottom = max(40, page_height * 0.045)
            
            text_rect = pymupdf.Rect(
                margin_lr, margin_top,
                page_width - margin_lr, page_height - margin_bottom
            )
            text_width = text_rect.width
            
            if text_width < 100:
                text_rect = pymupdf.Rect(
                    20, margin_top,
                    page_width - 20, page_height - margin_bottom
                )
                text_width = text_rect.width
            
            # Base font sizing — adaptive based on page size and layout
            body_font_size = max(8, min(11, text_width / 50))
            
            # Boost font size for sparse/cover pages (few elements, lots of whitespace)
            if is_sparse:
                body_font_size = max(body_font_size, min(14, text_width / 35))
            
            # CSS color
            css_color = f"rgb({int(text_color[0]*255)}, {int(text_color[1]*255)}, {int(text_color[2]*255)})"
            
            # ── Adjust text_rect for sparse pages ──
            # Move text_rect down proportionally if content doesn't start
            # at the top in the original, and constrain bottom if content
            # ends well before the page bottom.
            content_y_range = layout_hints.get('content_y_range')
            orig_page_size = metadata.get('page_size')
            
            # Proportional gap margins for sparse pages (applied inline)
            # Maps element index → extra margin-top in pt
            sparse_gap_margins: dict = {}
            
            if is_sparse and content_y_range and orig_page_size:
                orig_h = orig_page_size[1]
                y_start_pct = content_y_range[0] / orig_h
                y_end_pct = content_y_range[1] / orig_h
                
                # Push text_rect top down proportionally
                if y_start_pct > 0.10:
                    new_y0 = page_height * y_start_pct * 0.85
                    if new_y0 > text_rect.y0 and new_y0 < page_height * 0.5:
                        text_rect = pymupdf.Rect(
                            text_rect.x0, new_y0,
                            text_rect.x1, text_rect.y1
                        )
                
                # Constrain bottom if content doesn't reach page bottom
                if y_end_pct < 0.85:
                    new_y1 = page_height * y_end_pct * 1.10
                    if new_y1 > text_rect.y0 + 100:
                        text_rect = pymupdf.Rect(
                            text_rect.x0, text_rect.y0,
                            text_rect.x1, new_y1
                        )
                
                # Compute proportional vertical gaps from block positions
                # For sparse pages, elements roughly map 1:1 to content blocks
                CONTENT_TYPES = {'text', 'title', 'paragraph_title', 'list'}
                content_bboxes = sorted(
                    [b['bbox'] for b in metadata.get('block_bboxes', [])
                     if b.get('type') in CONTENT_TYPES],
                    key=lambda bb: bb[1]  # sort by y0
                )
                
                n_elems = sum(1 for e in translated_elements
                              if e.get('text', '').strip())
                
                if (len(content_bboxes) >= 2
                        and abs(n_elems - len(content_bboxes)) <= 2):
                    # Compute gap ratios between blocks
                    orig_span = content_y_range[1] - content_y_range[0]
                    if orig_span > 0:
                        for i in range(1, len(content_bboxes)):
                            gap = content_bboxes[i][1] - content_bboxes[i - 1][3]
                            if gap > 10:  # only for significant gaps
                                gap_ratio = gap / orig_span
                                margin_pt = text_rect.height * gap_ratio
                                sparse_gap_margins[i] = max(10, margin_pt)
            
            # Build HTML document from all translated elements
            html_parts = []
            
            elem_idx = 0
            for elem in translated_elements:
                elem_type = elem['type']
                elem_text = elem.get('text', '').strip()
                
                if not elem_text:
                    continue
                
                # Compute inline margin-top for proportional spacing
                extra_margin = sparse_gap_margins.get(elem_idx, 0)
                margin_style = f' style="margin-top: {extra_margin:.0f}pt"' if extra_margin > 5 else ''
                
                if elem_type == 'heading':
                    level = min(elem.get('level', 1), 6)
                    html_parts.append(
                        f'<h{level}{margin_style}>{_escape_html(elem_text)}</h{level}>'
                    )
                elif elem_type == 'table':
                    table_html = self._render_table_as_html(
                        elem_text, body_font_size, text_color
                    )
                    html_parts.append(table_html)
                else:  # paragraph
                    html_parts.append(
                        f'<p{margin_style}>{_escape_html(elem_text)}</p>'
                    )
                
                elem_idx += 1
            
            full_html = '\n'.join(html_parts)
            
            # Build CSS stylesheet
            # Heading scale factors: h1=1.5x, h2=1.3x, h3=1.15x, h4=1.05x
            h1_size = body_font_size * 1.5
            h2_size = body_font_size * 1.3
            h3_size = body_font_size * 1.15
            h4_size = body_font_size * 1.05
            
            # Tighter spacing for dense pages
            if is_dense:
                p_margin = f"{body_font_size * 0.25:.1f}pt"
                h_margin_top = f"{body_font_size * 0.5:.1f}pt"
                h_margin_bottom = f"{body_font_size * 0.2:.1f}pt"
                line_height = "1.15"
            elif is_sparse:
                # Generous spacing for sparse/cover pages
                p_margin = f"{body_font_size * 0.8:.1f}pt"
                h_margin_top = f"{body_font_size * 1.5:.1f}pt"
                h_margin_bottom = f"{body_font_size * 0.6:.1f}pt"
                line_height = "1.4"
            else:
                p_margin = f"{body_font_size * 0.4:.1f}pt"
                h_margin_top = f"{body_font_size * 0.8:.1f}pt"
                h_margin_bottom = f"{body_font_size * 0.3:.1f}pt"
                line_height = "1.25"
            
            # Text alignment based on layout analysis
            text_align = "center" if is_centered else "justify"
            
            css = f"""
            * {{
                font-family: Helvetica, Arial, sans-serif;
                color: {css_color};
                margin: 0;
                padding: 0;
            }}
            p {{
                font-size: {body_font_size:.1f}pt;
                line-height: {line_height};
                margin-top: {p_margin};
                margin-bottom: {p_margin};
                text-align: {text_align};
            }}
            h1 {{
                font-size: {h1_size:.1f}pt;
                font-weight: bold;
                line-height: 1.15;
                margin-top: {h_margin_top};
                margin-bottom: {h_margin_bottom};
                text-align: {text_align};
            }}
            h2 {{
                font-size: {h2_size:.1f}pt;
                font-weight: bold;
                line-height: 1.15;
                margin-top: {h_margin_top};
                margin-bottom: {h_margin_bottom};
                text-align: {text_align};
            }}
            h3 {{
                font-size: {h3_size:.1f}pt;
                font-weight: bold;
                line-height: 1.2;
                margin-top: {h_margin_top};
                margin-bottom: {h_margin_bottom};
                text-align: {text_align};
            }}
            h4, h5, h6 {{
                font-size: {h4_size:.1f}pt;
                font-weight: bold;
                line-height: 1.2;
                margin-top: {h_margin_top};
                margin-bottom: {h_margin_bottom};
                text-align: {text_align};
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin-top: {p_margin};
                margin-bottom: {p_margin};
            }}
            td, th {{
                border: 1px solid #ccc;
                padding: 3px 5px;
                text-align: left;
                font-size: {body_font_size * 0.88:.1f}pt;
                line-height: 1.15;
            }}
            th {{
                font-weight: bold;
                background-color: #f5f5f5;
            }}
            """
            
            total_inserted = len(translated_elements)
            
            if detected_columns > 1:
                # ── MULTI-COLUMN: use Story API with multiple rects ──
                # PyMuPDF's insert_htmlbox ignores CSS column-count.
                # The correct approach is to create a Story and flow
                # content across separate column rectangles.
                
                if col_x_ranges:
                    # Use actual column positions from layout detection
                    col_rects = []
                    for cx0, cx1 in col_x_ranges:
                        col_rects.append(pymupdf.Rect(
                            cx0, text_rect.y0,
                            cx1, text_rect.y1
                        ))
                else:
                    # Fallback: evenly divide text_rect
                    col_gap = body_font_size * 1.5
                    col_w = (text_rect.width - col_gap * (detected_columns - 1)) / detected_columns
                    col_rects = []
                    for ci in range(detected_columns):
                        x0 = text_rect.x0 + ci * (col_w + col_gap)
                        col_rects.append(pymupdf.Rect(
                            x0, text_rect.y0,
                            x0 + col_w, text_rect.y1
                        ))
                
                mediabox = pymupdf.Rect(0, 0, page_width, page_height)
                
                story = pymupdf.Story(html=full_html, user_css=css)
                
                def rectfn(rect_num, filled):
                    if rect_num < detected_columns:
                        # First rect starts a new page; rest stay on same page
                        mb = mediabox if rect_num == 0 else None
                        return (mb, col_rects[rect_num], None)
                    return (None, None, None)  # stop — single page only
                
                temp_doc = story.write_with_links(rectfn)
                
                # Overlay the temp page onto our output page
                new_page.show_pdf_page(page_rect, temp_doc, 0)
                
                # Log column layout info
                temp_page = temp_doc[0]
                temp_words = temp_page.get_text('words')
                mid_x = page_width / 2
                left_w = sum(1 for w in temp_words if w[2] < mid_x)
                right_w = sum(1 for w in temp_words if w[0] > mid_x)
                
                logging.info(
                    f"Page {page_num + 1}: RapidDoc {detected_columns}-column layout "
                    f"({left_w} words left, {right_w} words right, "
                    f"{total_inserted} elements)"
                )
                
                try:
                    temp_doc.close()
                except Exception:
                    pass
            else:
                # ── SINGLE-COLUMN: use insert_htmlbox with auto-scaling ──
                # scale_low=0 means PyMuPDF will shrink content as much as
                # needed to fit; minimum readable is ~0.3 of original
                result = new_page.insert_htmlbox(
                    text_rect, full_html, css=css, scale_low=0
                )
                spare_height, scale = result
                
                if spare_height < 0:
                    logging.warning(
                        f"Page {page_num + 1}: Content could not fit even with "
                        f"full scaling (scale={scale:.2f})"
                    )
                elif scale < 1.0:
                    logging.info(
                        f"Page {page_num + 1}: Content auto-scaled to "
                        f"{scale:.0%} to fit page "
                        f"(spare={spare_height:.0f}pt)"
                    )
                
                logging.info(
                    f"Page {page_num + 1}: RapidDoc clean page created with "
                    f"{total_inserted} translated elements "
                    f"(scale={scale:.0%}, spare_height={spare_height:.0f}pt)"
                )
            return new_doc
            
        except Exception as e:
            capture_exception(e, context={
                "operation": "translate_scanned_page_rapiddoc",
                "page_num": page_num,
            }, tags={"component": "pdf_processor"})
            logging.error(
                f"Page {page_num + 1}: RapidDoc translation failed: {e}, "
                f"falling back to RapidOCR", exc_info=True
            )
            # Fallback to plain RapidOCR
            return self._translate_scanned_page(
                new_doc, page, page_num, translator, text_color, ocr_language
            )
    
    def _translate_table_element(
        self, elem: Dict[str, Any], translator
    ) -> Dict[str, Any]:
        """
        Translate a table element cell-by-cell.
        
        Parses Markdown table lines (|col1|col2|...) and translates
        each cell individually to preserve table structure.
        """
        lines = elem['text'].strip().split('\n')
        translated_lines = []
        
        for line in lines:
            if not line.strip().startswith('|'):
                translated_lines.append(line)
                continue
            
            cells = [c.strip() for c in line.split('|')]
            # Remove empty first/last from leading/trailing |
            if cells and cells[0] == '':
                cells = cells[1:]
            if cells and cells[-1] == '':
                cells = cells[:-1]
            
            translated_cells = []
            for cell in cells:
                if cell and len(cell.strip()) >= 2:
                    try:
                        translated = translator.translate(cell.strip())
                        translated_cells.append(translated or cell)
                    except Exception:
                        translated_cells.append(cell)
                else:
                    translated_cells.append(cell)
            
            translated_lines.append('| ' + ' | '.join(translated_cells) + ' |')
        
        return {
            **elem,
            'text': '\n'.join(translated_lines),
        }
    
    @staticmethod
    def _render_table_as_html(
        table_text: str,
        font_size: float,
        text_color: Tuple[float, float, float]
    ) -> str:
        """
        Convert a Markdown-style table to HTML for PDF rendering.
        
        Args:
            table_text: Pipe-separated table text (|col1|col2|...)
            font_size: Base font size
            text_color: Text color tuple
            
        Returns:
            HTML string with <table> structure
        """
        lines = table_text.strip().split('\n')
        if not lines:
            return f"<p>{table_text}</p>"
        
        html_parts = ['<table>']
        
        for i, line in enumerate(lines):
            if not line.strip().startswith('|'):
                continue
            
            cells = [c.strip() for c in line.split('|')]
            if cells and cells[0] == '':
                cells = cells[1:]
            if cells and cells[-1] == '':
                cells = cells[:-1]
            
            if not cells:
                continue
            
            tag = 'th' if i == 0 else 'td'
            html_parts.append('<tr>')
            for cell in cells:
                html_parts.append(f'<{tag}>{_escape_html(cell)}</{tag}>')
            html_parts.append('</tr>')
        
        html_parts.append('</table>')
        return '\n'.join(html_parts)
    
    def _translate_scanned_page(
        self,
        new_doc: pymupdf.Document,
        page: pymupdf.Page,
        page_num: int,
        translator,
        text_color: Tuple[float, float, float] = (0, 0, 0),
        ocr_language: str = "en"
    ) -> pymupdf.Document:
        """
        Translate a scanned (image-based) page using RapidOCR + CLEAN SLATE approach.
        
        Strategy:
        1. Render page to high-resolution image
        2. RapidOCR extracts all text (detection + classification + recognition)
        3. Post-process OCR text (fix errors, normalize)
        4. Split into paragraphs and translate each
        5. Create CLEAN BLANK PAGE with same dimensions
        6. Insert translated text as flowing paragraphs
        
        Args:
            new_doc: Document to modify (will be replaced with clean page)
            page: Original page to translate
            page_num: Page number (for logging)
            translator: Translation engine
            text_color: Color for translated text
            ocr_language: Language code (for logging)
            
        Returns:
            New document with translated content on clean page
        """
        if not OCR_AVAILABLE:
            logging.warning(f"Page {page_num + 1}: OCR not available, cannot translate scanned page")
            return new_doc
        
        try:
            # ============================================
            # STEP 1: Get page dimensions and render to image
            # ============================================
            page_rect = page.rect
            page_width = page_rect.width
            page_height = page_rect.height
            
            # Convert page to high-resolution PNG for OCR
            ocr_scale = 2.0  # 2x = 144 DPI — good balance of quality vs speed
            pix = page.get_pixmap(matrix=pymupdf.Matrix(ocr_scale, ocr_scale))
            img_data = pix.tobytes("png")
            
            logging.info(f"Page {page_num + 1}: Rendered to {pix.width}x{pix.height} for RapidOCR")
            
            # ============================================
            # STEP 2: RapidOCR text extraction
            # ============================================
            ocr_text = _ocr_engine_instance.recognize_document_page(
                img_data, 
                detect_tables=True
            )
            
            if not ocr_text or len(ocr_text.strip()) < 5:
                logging.warning(f"Page {page_num + 1}: RapidOCR returned no usable text")
                return new_doc
            
            logging.info(f"Page {page_num + 1}: RapidOCR extracted {len(ocr_text)} chars")
            
            # ============================================
            # STEP 3: Post-process OCR text
            # ============================================
            # post_process_ocr_text include già clean_ocr_text come primo passo
            ocr_text = post_process_ocr_text(ocr_text)
            
            # ============================================
            # STEP 4: Split into paragraphs and translate
            # ============================================
            # OCR output uses double newlines for paragraphs
            raw_paragraphs = re.split(r'\n\s*\n', ocr_text)
            
            translated_paragraphs = []
            for para in raw_paragraphs:
                para = para.strip()
                if not para or len(para) < 3:
                    continue
                
                # Translate the paragraph
                translated = translator.translate(para)
                if translated and translated.strip():
                    translated_paragraphs.append(translated.strip())
                else:
                    # Keep original if translation fails
                    translated_paragraphs.append(para)
            
            if not translated_paragraphs:
                logging.warning(f"Page {page_num + 1}: No paragraphs to insert after translation")
                return new_doc
            
            logging.info(f"Page {page_num + 1}: Translated {len(translated_paragraphs)} paragraphs")
            
            # ============================================
            # STEP 5: CREATE CLEAN PAGE and insert translated text
            # ============================================
            new_page = new_doc[0]
            
            # Clear everything — draw white rectangle over entire page
            new_page.draw_rect(page_rect, color=(1, 1, 1), fill=(1, 1, 1))
            
            # Page margins
            margin_left = max(30, page_width * 0.05)
            margin_right = max(30, page_width * 0.05)
            margin_top = max(40, page_height * 0.04)
            margin_bottom = max(40, page_height * 0.04)
            
            # Text area
            text_x0 = margin_left
            text_x1 = page_width - margin_right
            text_width = text_x1 - text_x0
            
            if text_width < 100:
                # Fallback for very narrow pages
                text_x0 = 20
                text_x1 = page_width - 20
            
            # Font sizing — adaptive based on page size
            # Standard A4 is 595 wide, typical body text is 10-11pt
            base_font_size = max(8, min(11, text_width / 50))
            
            current_y = margin_top
            total_inserted = 0
            paragraph_gap = base_font_size * 0.8  # Gap between paragraphs
            
            for para_text in translated_paragraphs:
                if current_y >= page_height - margin_bottom:
                    logging.warning(f"Page {page_num + 1}: Ran out of space, {len(translated_paragraphs) - total_inserted} paragraphs remaining")
                    break
                
                # Estimate required height for the text box
                # Rough estimate: chars per line, then lines needed
                chars_per_line = max(1, int(text_width / (base_font_size * 0.5)))
                estimated_lines = max(1, len(para_text) / chars_per_line + 1)
                estimated_height = estimated_lines * base_font_size * 1.3
                
                # Ensure we don't exceed page
                available_height = page_height - margin_bottom - current_y
                box_height = min(estimated_height * 1.5, available_height)
                
                if box_height < base_font_size * 1.5:
                    break  # Not enough space for even one line
                
                text_rect = pymupdf.Rect(text_x0, current_y, text_x1, current_y + box_height)
                
                try:
                    excess = new_page.insert_textbox(
                        text_rect,
                        para_text,
                        fontsize=base_font_size,
                        fontname="helv",
                        color=text_color,
                        align=0,  # Left-aligned
                    )
                    
                    if excess < 0:
                        # Text didn't fit — try smaller font
                        smaller_font = max(7, base_font_size * 0.8)
                        expanded_rect = pymupdf.Rect(
                            text_x0, current_y, text_x1, 
                            current_y + box_height * 1.5
                        )
                        excess = new_page.insert_textbox(
                            expanded_rect,
                            para_text,
                            fontsize=smaller_font,
                            fontname="helv",
                            color=text_color,
                            align=0,
                        )
                        # Use expanded height for Y advancement
                        actual_height = box_height * 1.5 if excess >= 0 else box_height
                    else:
                        # Calculate actual used height from excess
                        actual_height = box_height - excess if excess > 0 else box_height
                    
                    current_y += actual_height + paragraph_gap
                    total_inserted += 1
                    
                except Exception as e:
                    logging.debug(f"Failed to insert paragraph: {e}")
                    current_y += base_font_size * 2  # Skip some space and continue
            
            logging.info(f"Page {page_num + 1}: Clean page created with {total_inserted} translated paragraphs")
            return new_doc
            
        except Exception as e:
            capture_exception(e, context={
                "operation": "translate_scanned_page",
                "page_num": page_num,
            }, tags={"component": "pdf_processor"})
            logging.error(f"Page {page_num + 1}: Scanned page translation failed: {e}", exc_info=True)
            return new_doc

    def translate_page(
        self, 
        page_num: int, 
        translator,
        text_color: Tuple[float, float, float] = (0, 0, 0),
        use_original_color: bool = True,
        preserve_font_style: bool = True,
        preserve_line_breaks: bool = True,
        ocr_language: str = "en"
    ) -> pymupdf.Document:
        """
        World-class translation system with maximum fidelity to original.
        
        Architecture:
        1. Phase 0: Detect if page is scanned and needs OCR
        2. Phase 1: Extract all text structure with SPAN-LEVEL formatting
        3. Phase 2: Translate LINE BY LINE to preserve structure
        4. Phase 3: Apply SPAN-LEVEL formatting to translated text
        5. Phase 4: Remove ALL original text via redaction (clean slate)
        6. Phase 5: Insert translations with inline formatting preserved
        
        For scanned pages:
        - Uses RapidOCR for text extraction
        - Creates clean page with translated text
        
        LINE-BY-LINE TRANSLATION (preserve_line_breaks=True):
        This mode translates each line independently, preserving the original
        document structure. This is crucial for:
        - Titles and headings on separate lines
        - Lists and bullet points
        - Tables and structured content
        - Poetry and formatted text
        
        SPAN-LEVEL FORMATTING:
        Tracks formatting at the span level (individual text segments within a line).
        This allows proper preservation of:
        - Inline bold (e.g., "This is **important** text")
        - Inline italic (e.g., "See the *definition* here")
        - Mixed formatting within the same line
        - Color changes for emphasis
        
        Args:
            page_num: Page number to translate
            translator: Translation engine instance
            text_color: RGB color tuple for translated text (default black)
            use_original_color: If True, use the original text color instead (default True)
            preserve_font_style: If True, match original font family style
            preserve_line_breaks: If True, translate line by line (default True)
            ocr_language: Language code for OCR (default "en")
            
        Returns:
            New document containing translated page
        """
        WHITE = pymupdf.pdfcolor["white"]
        
        new_doc = pymupdf.open()
        new_doc.insert_pdf(self.document, from_page=page_num, to_page=page_num)
        page = new_doc[0]
        
        # ============================================
        # PHASE 0: Check if page is scanned (needs OCR)
        # ============================================
        is_scanned, scan_reason = self._is_likely_scanned_page(page)
        
        if is_scanned:
            logging.info(f"Page {page_num + 1}: Detected as scanned ({scan_reason})")
            # Prefer RapidDoc for structured output (headings, tables, reading order)
            if RAPIDDOC_AVAILABLE:
                logging.info(f"Page {page_num + 1}: Using RapidDoc for structured OCR translation")
                return self._translate_scanned_page_rapiddoc(
                    new_doc, page, page_num, translator,
                    text_color, ocr_language
                )
            else:
                logging.info(f"Page {page_num + 1}: Using RapidOCR translation mode (RapidDoc not available)")
                return self._translate_scanned_page(
                    new_doc, page, page_num, translator, 
                    text_color, ocr_language
                )
        
        text_dict = page.get_text("dict", sort=True)
        
        # ============================================
        # PHASE 0b: Detect page-level alignment, margins and header/footer zones
        # ============================================
        page_alignment = _detect_page_alignment(text_dict, page.rect.width)
        
        # Detect header/footer zones (top/bottom 8% of page)
        page_height = page.rect.height
        header_zone_y = page_height * 0.08
        footer_zone_y = page_height * 0.92
        
        logging.info(f"Page {page_num + 1}: Detected alignment={page_alignment['alignment']}, "
                      f"margins=({page_alignment['left_margin']:.0f}, {page_alignment['right_margin']:.0f})")
        
        # Collect ALL areas to redact (will be applied in bulk before insertions)
        areas_to_redact = []
        # Collect all translations to insert (after redaction)
        translations_to_insert = []
        
        translated_count = 0
        total_blocks = len([b for b in text_dict.get("blocks", []) if "lines" in b])
        
        logging.info(f"Page {page_num + 1}: Found {total_blocks} text blocks to process (preserve_line_breaks={preserve_line_breaks})")
        
        # ============================================
        # PHASE 0c: Detect and translate tables
        # ============================================
        table_rects = []  # List of pymupdf.Rect for table areas to skip in block processing
        try:
            tables = page.find_tables()
            if tables.tables:
                logging.info(f"Page {page_num + 1}: Found {len(tables.tables)} tables")
                for tab_idx, tab in enumerate(tables.tables):
                    tab_rect = pymupdf.Rect(tab.bbox)
                    table_rects.append(tab_rect)
                    
                    # Extract table data
                    cells_data = tab.extract()
                    if not cells_data:
                        continue
                    
                    # Translate each cell
                    translated_cells = []
                    for row in cells_data:
                        translated_row = []
                        for cell in row:
                            if cell and cell.strip():
                                try:
                                    cell_trans = translator.translate(cell.strip())
                                    translated_row.append(cell_trans if cell_trans else cell)
                                except Exception:
                                    translated_row.append(cell)
                            else:
                                translated_row.append(cell or "")
                        translated_cells.append(translated_row)
                    
                    # Redact the table area
                    areas_to_redact.append(tuple(tab_rect))
                    
                    # We'll insert the translated table as text after redaction
                    # Calculate cell positions from the table structure
                    num_rows = tab.row_count
                    num_cols = tab.col_count
                    
                    if num_rows > 0 and num_cols > 0:
                        cell_height = (tab_rect.height) / num_rows
                        cell_width = (tab_rect.width) / num_cols
                        
                        for r_idx, row in enumerate(translated_cells):
                            for c_idx, cell_text in enumerate(row):
                                if not cell_text or not cell_text.strip():
                                    continue
                                
                                # Calculate cell bbox
                                cell_x0 = tab_rect.x0 + c_idx * cell_width + 2  # 2pt padding
                                cell_y0 = tab_rect.y0 + r_idx * cell_height + 2
                                cell_x1 = tab_rect.x0 + (c_idx + 1) * cell_width - 2
                                cell_y1 = tab_rect.y0 + (r_idx + 1) * cell_height - 2
                                
                                cell_bbox = (cell_x0, cell_y0, cell_x1, cell_y1)
                                
                                # Estimate font size from cell height
                                cell_font_size = min(10, max(6, cell_height * 0.5))
                                
                                # Create a synthetic LineFormatInfo for cell
                                cell_line_info = LineFormatInfo(
                                    text=cell_text,
                                    spans=[],
                                    merged_bbox=cell_bbox,
                                    text_align='left',
                                )
                                
                                translations_to_insert.append({
                                    'line_info': cell_line_info,
                                    'line_data': {
                                        'text': cell_text,
                                        'bboxes': [cell_bbox],
                                        'merged_bbox': cell_bbox,
                                        'avg_size': cell_font_size,
                                        'is_bold': False,
                                        'is_italic': False,
                                        'is_serif': False,
                                        'is_monospace': False,
                                        'dominant_color': (0, 0, 0),
                                        'rotation': 0,
                                        'text_align': 'left',
                                        'indent': 0,
                                    },
                                    'text': cell_text,
                                    'formatted_html': cell_text,
                                    'use_html': False,
                                    'is_table_cell': True,
                                })
                                translated_count += 1
                    
                    logging.info(f"  Table {tab_idx}: {num_rows}x{num_cols} translated")
        except Exception as e:
            logging.warning(f"Table detection/translation failed: {e}")
            table_rects = []
        
        # ============================================
        # PHASE 0: Pre-merge single-line blocks into paragraph groups
        # ============================================
        # Strategy: use pymupdf4llm's column_boxes() for robust multi-column
        # detection and reading-order sorting. This is a battle-tested algorithm
        # maintained by the PyMuPDF team that handles:
        # - Multi-column layouts (academic papers, newspapers, etc.)
        # - Background color zones (sidebars, callout boxes)
        # - Header/footer exclusion
        # - Table/image area avoidance
        # - Correct reading order across columns
        # Falls back to heuristic merging if pymupdf4llm is not installed.
        
        if COLUMN_BOXES_AVAILABLE:
            # Build avoid list from detected table rects
            avoid_rects = [pymupdf.Rect(tr) for tr in table_rects] if table_rects else None
            
            try:
                text_rects = column_boxes(
                    page,
                    footer_margin=page_height * 0.08,   # 8% footer zone
                    header_margin=page_height * 0.08,    # 8% header zone
                    no_image_text=True,
                    avoid=avoid_rects,
                )
                
                # For each column rect, extract text blocks and build paragraph groups
                merged_block_groups = []
                for rect in text_rects:
                    clip_dict = page.get_text("dict", clip=rect, sort=True)
                    groups = self._merge_text_blocks(clip_dict, page_height)
                    merged_block_groups.extend(groups)
                
                logging.info(
                    f"Page {page_num + 1}: column_boxes found {len(text_rects)} regions "
                    f"→ {len(merged_block_groups)} paragraph groups"
                )
            except Exception as e:
                logging.warning(f"column_boxes failed: {e}, falling back to heuristic merging")
                merged_block_groups = self._merge_text_blocks(
                    text_dict, page_height,
                    header_zone_y=header_zone_y, footer_zone_y=footer_zone_y,
                    check_x_overlap=True,
                )
        else:
            # ── FALLBACK: PyMuPDF-only heuristic paragraph merging ──
            merged_block_groups = self._merge_text_blocks(
                text_dict, page_height,
                header_zone_y=header_zone_y, footer_zone_y=footer_zone_y,
                check_x_overlap=True,
            )
        
        # ============================================
        # PHASE 1: Extract structure with SPAN-LEVEL formatting
        # ============================================
        for group_idx, block_group in enumerate(merged_block_groups):
            # Collect lines_info from ALL blocks in this group
            lines_info: List[LineFormatInfo] = []
            
            for block_data in block_group:
                block = block_data['block']
                
                # Skip blocks that overlap with detected tables
                # (tables are handled separately in Phase 0c)
                if table_rects:
                    block_bbox = block.get("bbox", (0, 0, 0, 0))
                    block_rect = pymupdf.Rect(block_bbox)
                    skip_block = False
                    for tab_rect in table_rects:
                        # Check if block significantly overlaps with table
                        intersection = block_rect & tab_rect
                        if intersection.is_empty:
                            continue
                        overlap_area = intersection.width * intersection.height
                        block_area = block_rect.width * block_rect.height
                        if block_area > 0 and overlap_area / block_area > 0.5:
                            skip_block = True
                            break
                    if skip_block:
                        logging.debug(f"Skipping block overlapping table: {block_bbox}")
                        continue
                
                for line in block.get("lines", []):
                    if "spans" not in line:
                        continue
                    
                    # Extract text direction for rotation support
                    line_dir = line.get("dir", (1, 0))  # Default: horizontal left-to-right
                    line_wmode = line.get("wmode", 0)   # 0 = horizontal, 1 = vertical
                    
                    # Calculate rotation angle from direction vector
                    cos_val, neg_sin_val = line_dir
                    angle_rad = math.atan2(-neg_sin_val, cos_val)
                    angle_deg = math.degrees(angle_rad)
                    rotation = round(angle_deg / 90) * 90
                    rotation = int(rotation) % 360
                    
                    # Create SpanFormat objects for each span
                    span_formats: List[SpanFormat] = []
                    line_bboxes = []
                    
                    # First pass: collect sizes and origins to calculate line averages
                    span_data = []
                    for span in line["spans"]:
                        # Always add span bbox to redaction list (even empty spans)
                        span_bbox = span.get("bbox")
                        if span_bbox:
                            areas_to_redact.append(span_bbox)
                        
                        text = span.get("text", "").strip()
                        if text:
                            bbox = span["bbox"]
                            size = span.get("size", 11)
                            origin = span.get("origin", (bbox[0], bbox[3]))  # Default to bottom-left
                            origin_y = origin[1] if origin else bbox[3]
                            span_data.append({
                                "span": span,
                                "text": text,
                                "bbox": bbox,
                                "size": size,
                                "origin_y": origin_y
                            })
                    
                    # Calculate line average size (for superscript/subscript detection)
                    if span_data:
                        all_sizes = [d["size"] for d in span_data]
                        line_avg_size = sum(all_sizes) / len(all_sizes)
                        
                        # Calculate baseline origin_y from normal-sized spans
                        normal_spans = [d for d in span_data if d["size"] >= line_avg_size * 0.8]
                        if normal_spans:
                            line_origin_y = sum(d["origin_y"] for d in normal_spans) / len(normal_spans)
                        else:
                            line_origin_y = sum(d["origin_y"] for d in span_data) / len(span_data)
                    else:
                        line_avg_size = 11
                        line_origin_y = 0
                    
                    # Second pass: create SpanFormat objects with baseline info
                    for data in span_data:
                        span = data["span"]
                        bbox = data["bbox"]
                        line_bboxes.append(bbox)
                        
                        # Extract color from integer
                        color_int = span.get("color", 0)
                        r = ((color_int >> 16) & 0xFF) / 255.0
                        g = ((color_int >> 8) & 0xFF) / 255.0
                        b = (color_int & 0xFF) / 255.0
                        
                        span_format = SpanFormat(
                            text=data["text"],
                            bbox=bbox,
                            size=data["size"],
                            font=span.get("font", ""),
                            color=(r, g, b),
                            flags=span.get("flags", 0),
                            line_avg_size=line_avg_size,
                            origin_y=data["origin_y"],
                            line_origin_y=line_origin_y
                        )
                        span_formats.append(span_format)
                    
                    if span_formats:
                        # Smart span joining: only add space if there's a gap between spans
                        # Many PDFs split words across spans (for formatting changes mid-word)
                        # Blindly adding " " creates artifacts like "in troduction"
                        parts = []
                        for idx_s, sf in enumerate(span_formats):
                            if idx_s == 0:
                                parts.append(sf.text)
                            else:
                                prev_sf = span_formats[idx_s - 1]
                                # Check horizontal gap between end of previous span and start of current
                                prev_right = prev_sf.bbox[2]  # x1
                                curr_left = sf.bbox[0]         # x0
                                gap = curr_left - prev_right
                                avg_char_w = prev_sf.size * 0.3  # ~30% of font size = typical char width
                                
                                # If spans overlap or are very close, no space needed
                                if gap < avg_char_w:
                                    # Check if previous text ends or current starts with space
                                    if prev_sf.text.endswith(' ') or sf.text.startswith(' '):
                                        parts.append(sf.text)
                                    else:
                                        parts.append(sf.text)
                                else:
                                    # Gap detected: add space separator
                                    parts.append(" " + sf.text)
                        
                        line_text = "".join(parts)
                        merged_bbox = self._merge_bboxes(line_bboxes)
                        
                        # Calculate indentation relative to page left margin
                        line_x0 = merged_bbox[0]
                        page_left_margin = page_alignment['left_margin']
                        indent = max(0.0, line_x0 - page_left_margin)
                        
                        line_info = LineFormatInfo(
                            text=line_text,
                            spans=span_formats,
                            merged_bbox=merged_bbox,
                            rotation=rotation,
                            wmode=line_wmode,
                            text_align=page_alignment['alignment'],
                            indent=indent,
                        )
                        lines_info.append(line_info)
                        
                        # Note: bboxes are already added to areas_to_redact in the span loop above
            
            if not lines_info:
                continue
            
            # Log if block has mixed formatting (useful for debugging)
            mixed_lines = [l for l in lines_info if l.has_mixed_formatting]
            if mixed_lines:
                logging.debug(f"Block has {len(mixed_lines)} lines with mixed inline formatting")
            
            # ============================================
            # PHASE 2: Translate - PARAGRAPH BY PARAGRAPH
            # ============================================
            # Group lines into logical paragraphs, then translate each paragraph.
            # A paragraph break occurs when:
            # - The previous line ends with sentence-ending punctuation (. ! ? :)
            # - There's a significant font size change (likely a heading)
            # - The line is very short and looks like a title
            # - The line is bold/different style from surrounding lines
            
            if preserve_line_breaks:
                # Group lines into logical paragraphs
                paragraphs = self._group_lines_into_paragraphs(lines_info)
                
                logging.debug(f"Block split into {len(paragraphs)} logical paragraph(s)")
                
                for para_lines in paragraphs:
                    if not para_lines:
                        continue
                    
                    # Single line paragraph - translate directly
                    if len(para_lines) == 1:
                        line_info = para_lines[0]
                        try:
                            # Check for list item: preserve prefix, translate body only
                            prefix, body = _extract_list_prefix(line_info.text)
                            if prefix:
                                body_trans = translator.translate(body.strip())
                                if not body_trans or not body_trans.strip():
                                    body_trans = body
                                line_trans = prefix + body_trans
                            else:
                                line_trans = translator.translate(line_info.text)
                                if not line_trans or not line_trans.strip():
                                    line_trans = line_info.text
                            
                            formatted_text = self._apply_span_formatting(
                                line_info, line_trans, use_original_color
                            )
                            translations_to_insert.append({
                                'line_info': line_info,
                                'line_data': line_info.to_legacy_dict(),
                                'text': line_trans,
                                'formatted_html': formatted_text,
                                'use_html': line_info.has_mixed_formatting
                            })
                            translated_count += 1
                        except Exception as e:
                            capture_exception(e, context={"operation": "translate_line"}, tags={"component": "pdf_processor"})
                            logging.error(f"Line translation error: {e}")
                            translations_to_insert.append({
                                'line_info': line_info,
                                'line_data': line_info.to_legacy_dict(),
                                'text': line_info.text,
                                'formatted_html': line_info.text,
                                'use_html': False
                            })
                            translated_count += 1
                    else:
                        # Multi-line paragraph - translate together and insert in UNIFIED bbox
                        # This prevents overlapping text by using one merged bbox for the whole paragraph
                        
                        # Check if first line has a list prefix — preserve it
                        first_text = para_lines[0].text.strip()
                        list_prefix, first_body = _extract_list_prefix(first_text)
                        
                        if list_prefix:
                            # Join body of first line + rest of lines for translation
                            para_text = first_body.strip() + " " + " ".join(li.text for li in para_lines[1:])
                        else:
                            para_text = " ".join(li.text for li in para_lines)
                        
                        try:
                            translated_para = translator.translate(para_text)
                            
                            if not translated_para or not translated_para.strip():
                                # Fallback: translate each line separately
                                for line_info in para_lines:
                                    line_trans = translator.translate(line_info.text) or line_info.text
                                    formatted_text = self._apply_span_formatting(
                                        line_info, line_trans, use_original_color
                                    )
                                    translations_to_insert.append({
                                        'line_info': line_info,
                                        'line_data': line_info.to_legacy_dict(),
                                        'text': line_trans,
                                        'formatted_html': formatted_text,
                                        'use_html': line_info.has_mixed_formatting
                                    })
                                    translated_count += 1
                                continue
                            
                            # Re-prepend list prefix if present
                            if list_prefix:
                                translated_para = list_prefix + translated_para
                            
                            # NEW APPROACH: Insert ALL translated text in ONE unified bbox
                            # This prevents overlap caused by text wrapping into adjacent line bboxes
                            
                            # Create unified bbox covering all lines in this paragraph
                            all_bboxes = [li.merged_bbox for li in para_lines]
                            unified_bbox = self._merge_bboxes(all_bboxes)
                            
                            # If we're processing a single block, use the original block bbox
                            # This ensures we have the full height including empty lines
                            if len(block_group) == 1:
                                original_block_bbox = block_group[0]['bbox']
                                # Use original bbox if it's larger (includes empty lines)
                                if original_block_bbox[3] - original_block_bbox[1] > unified_bbox[3] - unified_bbox[1]:
                                    unified_bbox = (
                                        unified_bbox[0],  # Keep calculated x0
                                        original_block_bbox[1],  # Use original y0
                                        unified_bbox[2],  # Keep calculated x1
                                        original_block_bbox[3]   # Use original y1
                                    )
                            
                            # IMPORTANT: Add ALL original line bboxes to redaction list
                            # This ensures all original text is removed before inserting translation
                            for li in para_lines:
                                for span in li.spans:
                                    areas_to_redact.append(span.bbox)
                            
                            # Use first line's formatting as the paragraph style
                            first_line = para_lines[0]
                            
                            # Create a synthetic LineFormatInfo with unified bbox
                            unified_line_info = LineFormatInfo(
                                text=para_text,
                                spans=first_line.spans,  # Use first line's formatting
                                merged_bbox=unified_bbox,
                                rotation=first_line.rotation,
                                wmode=first_line.wmode
                            )
                            
                            # Apply formatting to translated paragraph
                            formatted_para = self._apply_span_formatting(
                                first_line, translated_para, use_original_color
                            )
                            
                            # Insert as single paragraph translation
                            translations_to_insert.append({
                                'line_info': unified_line_info,
                                'line_data': unified_line_info.to_legacy_dict(),
                                'text': translated_para,
                                'formatted_html': formatted_para,
                                'use_html': first_line.has_mixed_formatting,
                                'is_paragraph': True  # Mark as unified paragraph
                            })
                            translated_count += 1  # Count as one translated unit
                        
                        except Exception as e:
                            capture_exception(e, context={"operation": "translate_paragraph"}, tags={"component": "pdf_processor"})
                            logging.error(f"Paragraph translation error: {e}")
                            # Fallback: translate each line separately
                            for line_info in para_lines:
                                try:
                                    line_trans = translator.translate(line_info.text) or line_info.text
                                    formatted_text = self._apply_span_formatting(
                                        line_info, line_trans, use_original_color
                                    )
                                    translations_to_insert.append({
                                        'line_info': line_info,
                                        'line_data': line_info.to_legacy_dict(),
                                        'text': line_trans,
                                        'formatted_html': formatted_text,
                                        'use_html': line_info.has_mixed_formatting
                                    })
                                    translated_count += 1
                                except Exception:
                                    translations_to_insert.append({
                                        'line_info': line_info,
                                        'line_data': line_info.to_legacy_dict(),
                                        'text': line_info.text,
                                        'formatted_html': line_info.text,
                                        'use_html': False
                                    })
                                    translated_count += 1
            else:
                # LEGACY MODE: Translate entire block, then redistribute
                # (Kept for backward compatibility, but not recommended)
                block_full_text = [li.text for li in lines_info]
                block_text = " ".join(block_full_text)
                
                logging.debug(f"Block has {len(lines_info)} lines, text: {block_text[:100]}...")
                
                try:
                    translated_block = translator.translate(block_text)
                    
                    if not translated_block or not translated_block.strip():
                        # Fallback to line by line
                        for line_info in lines_info:
                            line_trans = translator.translate(line_info.text) or line_info.text
                            formatted_text = self._apply_span_formatting(
                                line_info, line_trans, use_original_color
                            )
                            translations_to_insert.append({
                                'line_info': line_info,
                                'line_data': line_info.to_legacy_dict(),
                                'text': line_trans,
                                'formatted_html': formatted_text,
                                'use_html': line_info.has_mixed_formatting
                            })
                            translated_count += 1
                        continue
                    
                    # Sentence-aware distribution
                    translated_sentences = split_into_sentences(translated_block)
                    original_line_lengths = [len(li.text) for li in lines_info]
                    line_texts = align_sentences_to_lines(
                        translated_sentences,
                        len(lines_info),
                        original_line_lengths
                    )
                    
                    for line_info, line_text in zip(lines_info, line_texts):
                        if line_text.strip():
                            formatted_text = self._apply_span_formatting(
                                line_info, line_text, use_original_color
                            )
                            translations_to_insert.append({
                                'line_info': line_info,
                                'line_data': line_info.to_legacy_dict(),
                                'text': line_text,
                                'formatted_html': formatted_text,
                                'use_html': line_info.has_mixed_formatting
                            })
                            translated_count += 1
                    
                except Exception as e:
                    capture_exception(e, context={"operation": "translate_block"}, tags={"component": "pdf_processor"})
                    logging.error(f"Block translation error: {e}, using line-by-line fallback")
                    for line_info in lines_info:
                        try:
                            line_trans = translator.translate(line_info.text)
                            formatted_text = self._apply_span_formatting(
                                line_info, line_trans or line_info.text, use_original_color
                            )
                            translations_to_insert.append({
                                'line_info': line_info,
                                'line_data': line_info.to_legacy_dict(),
                                'text': line_trans or line_info.text,
                                'formatted_html': formatted_text,
                                'use_html': line_info.has_mixed_formatting
                            })
                            translated_count += 1
                        except Exception as line_error:
                            capture_exception(line_error, context={"operation": "translate_line_fallback"}, tags={"component": "pdf_processor"})
                            logging.error(f"Line translation failed: {line_error}")
        
        # ============================================
        # PHASE 3: Apply redactions (remove ALL original text)
        # ============================================
        logging.info(f"Applying {len(areas_to_redact)} redactions to remove original text...")
        
        # Save links before redaction (redaction destroys annotations including links)
        saved_links = []
        try:
            for link in page.get_links():
                saved_links.append(link.copy())
            if saved_links:
                logging.info(f"Saved {len(saved_links)} links before redaction")
        except Exception as e:
            logging.warning(f"Failed to save links: {e}")
        
        for bbox in areas_to_redact:
            try:
                # Add redaction annotation with white fill
                rect = pymupdf.Rect(bbox)
                page.add_redact_annot(rect, fill=(1, 1, 1))
            except Exception as e:
                logging.warning(f"Failed to add redaction for {bbox}: {e}")
        
        # Apply all redactions at once (this actually removes the text)
        # IMPORTANT: Preserve images and vector graphics during redaction
        # Without these flags, apply_redactions() destroys ALL overlapping content
        page.apply_redactions(
            images=pymupdf.PDF_REDACT_IMAGE_NONE,   # Don't touch images
            graphics=pymupdf.PDF_REDACT_LINE_ART_NONE  # Don't touch vector graphics/lines
        )
        logging.info(f"Redactions applied successfully (images & graphics preserved)")
        
        # Restore links after redaction
        if saved_links:
            restored = 0
            for link in saved_links:
                try:
                    page.insert_link(link)
                    restored += 1
                except Exception as e:
                    logging.debug(f"Failed to restore link: {e}")
            logging.info(f"Restored {restored}/{len(saved_links)} links after redaction")
        
        # ============================================
        # PHASE 3: Insert translations with SPAN-LEVEL formatting
        # ============================================
        logging.info(f"Inserting {len(translations_to_insert)} translations...")
        
        for item in translations_to_insert:
            try:
                # Use new span-aware insertion if mixed formatting, else use legacy
                if item.get('use_html') and item.get('formatted_html'):
                    self._insert_formatted_translation(
                        page,
                        item['line_info'],
                        item['formatted_html'],
                        text_color,
                        use_original_color=use_original_color,
                        preserve_font_style=preserve_font_style
                    )
                else:
                    # Legacy method for simple formatting
                    self._insert_line_translation(
                        page, 
                        item['line_data'], 
                        item['text'],
                        text_color,
                        use_original_color=use_original_color,
                        preserve_font_style=preserve_font_style,
                        skip_clearing=True  # Already cleared via redaction
                    )
            except Exception as e:
                capture_exception(e, context={"operation": "insert_translation"}, tags={"component": "pdf_processor"})
                logging.error(f"Failed to insert translation: {e}")
        
        logging.info(f"Page {page_num + 1}: Successfully processed {total_blocks} blocks, translated {translated_count} lines")
        
        if translated_count == 0:
            logging.warning(f"Page {page_num + 1}: NO LINES TRANSLATED! This page may appear blank.")
        
        return new_doc
    
    def _apply_span_formatting(
        self,
        line_info: LineFormatInfo,
        translated_text: str,
        use_original_color: bool = True
    ) -> str:
        """
        Apply original span-level formatting to translated text.
        
        This is the intelligent formatting mapper that preserves inline styles
        (bold, italic, color) from the original text and applies them
        proportionally to the translated text.
        
        Algorithm:
        1. Get formatting segments from original line
        2. If no mixed formatting, return plain text (no HTML needed)
        3. Otherwise, use proportional mapping to apply formatting
        
        Args:
            line_info: Original line with span-level formatting info
            translated_text: The translated text to format
            use_original_color: Whether to preserve original colors
            
        Returns:
            HTML-formatted string if mixed formatting, else plain text
        """
        if not line_info.has_mixed_formatting:
            # No mixed formatting = no HTML needed
            return translated_text
        
        # Get formatting segments (consecutive spans with same formatting merged)
        segments = line_info.get_formatting_segments()
        
        if not segments:
            return translated_text
        
        # Use the intelligent formatting mapper
        formatted = map_formatting_to_translation(segments, translated_text)
        
        logging.debug(f"Applied span formatting: '{translated_text[:50]}...' -> '{formatted[:60]}...'")
        
        return formatted
    
    def _insert_formatted_translation(
        self,
        page: pymupdf.Page,
        line_info: LineFormatInfo,
        formatted_html: str,
        text_color: Tuple[float, float, float],
        use_original_color: bool = True,
        preserve_font_style: bool = True
    ) -> None:
        """
        Insert translated text with span-level HTML formatting.
        
        This method handles lines that have mixed inline formatting
        (e.g., some words bold, some italic) by using HTML rendering.
        
        For simple formatting (all bold, all italic, etc.), use
        _insert_line_translation instead.
        
        Args:
            page: PyMuPDF page to insert text into
            line_info: LineFormatInfo with original formatting data
            formatted_html: HTML-formatted translation text
            text_color: Default text color (used if not preserving original)
            use_original_color: Whether to use original text colors
            preserve_font_style: Whether to preserve font family style
        """
        merged_bbox = line_info.merged_bbox
        bbox_width = merged_bbox[2] - merged_bbox[0]
        bbox_height = merged_bbox[3] - merged_bbox[1]
        
        if bbox_width <= 0 or bbox_height <= 0:
            logging.warning(f"Invalid bbox dimensions: {merged_bbox}")
            return
        
        # Determine base color (dominant color from original or specified)
        if use_original_color:
            base_color = line_info.dominant_color
        else:
            base_color = text_color
        
        # Calculate optimal font size
        target_font_size = line_info.avg_size
        
        # Ensure minimum font size of 7pt for readability
        if target_font_size < 7:
            target_font_size = 7
        
        # Determine font family based on original
        if preserve_font_style:
            if line_info.is_monospace:
                font_family = '"Courier New", Courier, monospace'
                pdf_font_name = "cour"
            elif line_info.is_serif:
                font_family = 'Georgia, "Times New Roman", Times, serif'
                pdf_font_name = "tiro"
            else:
                font_family = '-apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif'
                pdf_font_name = "helv"
        else:
            font_family = 'Helvetica, Arial, sans-serif'
            pdf_font_name = "helv"
        
        # Strip HTML tags for width calculation
        plain_text = re.sub(r'<[^>]+>', '', formatted_html)
        plain_text = plain_text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"')
        
        # Accurate text width measurement using PyMuPDF Font metrics
        try:
            measure_font = pymupdf.Font(pdf_font_name)
            estimated_width = measure_font.text_length(plain_text, fontsize=target_font_size)
        except Exception:
            # Fallback to rough estimation if Font creation fails
            estimated_width = len(plain_text) * target_font_size * 0.52
        
        # Determine if text needs wrapping (translated text wider than box)
        needs_wrapping = estimated_width > bbox_width
        # No bbox expansion — insert_htmlbox's scale_low handles fitting
        # via binary search in native C code, more accurate than manual estimates
        
        # Get rotation from line_info
        rotation = line_info.rotation
        
        # Build CSS
        css_color = f"rgb({int(base_color[0]*255)}, {int(base_color[1]*255)}, {int(base_color[2]*255)})"
        
        # Determine base font weight and style (can be overridden by HTML tags)
        base_weight = 'bold' if line_info.is_bold and '<b>' not in formatted_html else 'normal'
        base_style = 'italic' if line_info.is_italic and '<i>' not in formatted_html else 'normal'
        
        if needs_wrapping:
            white_space = "normal"
            word_wrap = "break-word"
        else:
            white_space = "nowrap"
            word_wrap = "normal"
        
        # Apply text alignment from page-level detection
        text_align = getattr(line_info, 'text_align', 'left')
        
        css = f"""* {{
            font-family: {font_family};
            font-size: {target_font_size}pt;
            color: {css_color};
            font-weight: {base_weight};
            font-style: {base_style};
            line-height: 1.3;
            padding: 0;
            margin: 0;
            white-space: {white_space};
            word-wrap: {word_wrap};
            text-align: {text_align};
            font-variant-ligatures: none;
            -webkit-font-variant-ligatures: none;
            font-feature-settings: "liga" 0, "clig" 0;
        }}
        b {{ font-weight: bold; }}
        i {{ font-style: italic; }}
        sup {{ vertical-align: super; font-size: 0.7em; }}
        sub {{ vertical-align: sub; font-size: 0.7em; }}
        """
        
        try:
            # Determine scale_low based on content type
            # Footnotes (small font or bottom of page) need more aggressive scaling
            page_height = page.rect.height
            is_footnote = target_font_size < 11 or merged_bbox[1] > page_height * 0.7
            
            if is_footnote:
                # Footnotes: allow up to 60% shrinking for dense text
                scale_low = 0.4
            else:
                # Normal text: allow up to 50% shrinking
                scale_low = 0.5
            
            result = page.insert_htmlbox(merged_bbox, formatted_html, css=css, rotate=rotation, scale_low=scale_low)
            if result[0] < 0:
                # spare_height=-1 means text didn't fit even with shrinking
                logging.warning(f"Text didn't fit in bbox {merged_bbox}, scale={result[1]:.2f}")
            logging.debug(f"[OK] Formatted HTML insertion successful (rotation={rotation}°, scale={result[1]:.2f})")
        except Exception as e:
            logging.warning(f"Formatted HTML insertion failed: {e}, falling back to plain text")
            # Fallback to plain text without formatting
            try:
                page.insert_htmlbox(merged_bbox, plain_text, css=css, rotate=rotation, scale_low=0.5)
            except Exception as e2:
                capture_exception(e2, context={"operation": "insert_plain_fallback"}, tags={"component": "pdf_processor"})
                logging.error(f"Plain text fallback also failed: {e2}")
    
    def _is_heading_by_font_size(self, avg_size: float) -> str:
        """Check if a font size corresponds to a heading using IdentifyHeaders.
        
        Returns:
            Heading prefix (e.g. '# ', '## ') or '' for body text.
        """
        hdr_info = self._get_hdr_info()
        if hdr_info is None:
            return ""
        # IdentifyHeaders works with rounded font sizes
        rounded = round(avg_size)
        if rounded <= hdr_info.body_limit:
            return ""
        return hdr_info.header_id.get(rounded, "")

    def _group_lines_into_paragraphs(
        self, 
        lines_info: List[LineFormatInfo]
    ) -> List[List[LineFormatInfo]]:
        """
        Group lines into logical paragraphs for translation.
        
        This intelligently detects paragraph boundaries to ensure:
        - Titles/headings are translated separately
        - Multi-line headings of the SAME level stay grouped together
        - Paragraph text flows naturally within the group
        - Structure is preserved when line breaks are meaningful
        
        Uses pymupdf4llm.IdentifyHeaders for document-level heading detection
        (font-size frequency analysis across all pages), falling back to
        heuristics if unavailable.
        
        Paragraph break indicators:
        1. Previous line ends with sentence punctuation (. ! ? :) + gap
        2. Transition between heading and body text (or different heading levels)
        3. Current line is bold when previous wasn't (or vice versa)
        4. Current line starts with a bullet or list marker
        5. There's significant vertical gap between lines
        
        Args:
            lines_info: List of LineFormatInfo from a block
            
        Returns:
            List of paragraph groups, each containing one or more lines
        """
        if not lines_info:
            return []
        
        if len(lines_info) == 1:
            return [lines_info]
        
        paragraphs: List[List[LineFormatInfo]] = []
        current_para: List[LineFormatInfo] = [lines_info[0]]
        
        for i in range(1, len(lines_info)):
            prev_line = lines_info[i - 1]
            curr_line = lines_info[i]
            
            should_break = False
            break_reason = ""
            
            # Check vertical gap first - this is the most reliable indicator
            prev_bottom = prev_line.merged_bbox[3]  # y1
            curr_top = curr_line.merged_bbox[1]     # y0
            gap = curr_top - prev_bottom
            avg_height = (prev_line.avg_size + curr_line.avg_size) / 2
            
            # Large gap (> 1.5x font size) always indicates paragraph break
            has_large_gap = gap > avg_height * 1.5
            
            # Check 1: Previous line ends with sentence-ending punctuation
            # BUT only break if there's also a noticeable gap or style change
            prev_text = prev_line.text.strip()
            ends_with_punct = False
            if prev_text and prev_text[-1] in '.!?:':
                # Check it's not an abbreviation (single letter before period)
                words = prev_text.split()
                if words:
                    last_word = words[-1].rstrip('.!?:')
                    # Not an abbreviation if word is long or all caps
                    if len(last_word) > 2 or last_word.isupper():
                        ends_with_punct = True
            
            # Only break on punctuation if there's also a gap (moderate, not large)
            if ends_with_punct and gap > avg_height * 0.8:
                should_break = True
                break_reason = "sentence_end_with_gap"
            
            # Check 2: Heading-level transition (document-level font-size analysis)
            # Uses IdentifyHeaders: if both lines are the SAME heading level,
            # they are part of the same multi-line heading — do NOT break.
            # Break only on transitions: heading→body, body→heading, or h1→h2.
            if not should_break:
                prev_hdr = self._is_heading_by_font_size(prev_line.avg_size)
                curr_hdr = self._is_heading_by_font_size(curr_line.avg_size)
                
                if prev_hdr != curr_hdr:
                    # Transition between different levels or heading↔body
                    should_break = True
                    prev_label = prev_hdr.strip() if prev_hdr else "body"
                    curr_label = curr_hdr.strip() if curr_hdr else "body"
                    break_reason = f"heading_transition ({prev_label}→{curr_label})"
                elif not prev_hdr and not curr_hdr:
                    # Both are body text — fall through to other checks
                    pass
                # else: both are same heading level — do NOT break (multi-line heading)
            
            # Check 3: Bold status change (only for body text, not headings)
            if not should_break:
                curr_hdr = self._is_heading_by_font_size(curr_line.avg_size)
                if not curr_hdr:  # Only apply to body text
                    if curr_line.is_bold != prev_line.is_bold:
                        should_break = True
                        break_reason = "bold_change"
            
            # Check 4: Current line starts with a bullet or list marker
            # Each list item should be a separate paragraph to preserve structure
            if not should_break:
                curr_stripped = curr_line.text.strip()
                if _is_list_item(curr_stripped):
                    should_break = True
                    break_reason = "list_item"
            
            # Check 5: Large vertical gap between lines (already calculated)
            if not should_break and has_large_gap:
                should_break = True
                break_reason = f"vertical_gap ({gap:.1f} > {avg_height * 1.5:.1f})"
            
            if should_break:
                logging.debug(f"Paragraph break before line '{curr_line.text[:30]}...' reason: {break_reason}")
                paragraphs.append(current_para)
                current_para = [curr_line]
            else:
                current_para.append(curr_line)
        
        # Don't forget the last paragraph
        if current_para:
            paragraphs.append(current_para)
        
        return paragraphs
    
    def _merge_text_blocks(
        self,
        text_dict: Dict[str, Any],
        page_height: float = 800.0,
        header_zone_y: Optional[float] = None,
        footer_zone_y: Optional[float] = None,
        check_x_overlap: bool = False,
    ) -> List[List[Dict[str, Any]]]:
        """
        Merge adjacent single-line blocks into logical paragraph groups.
        
        Unified function for both the column_boxes path (where column detection
        and zone filtering are already handled) and the heuristic fallback path.
        
        When called from column_boxes regions, omit zone params and set
        check_x_overlap=False.  When called as the fallback, enable all checks.
        
        Args:
            text_dict: Page text dictionary from get_text("dict")
            page_height: Full page height (for footnote detection)
            header_zone_y: If set, y below which is the header zone
            footer_zone_y: If set, y above which is the footer zone
            check_x_overlap: Require 30% X-overlap between blocks (column guard)
            
        Returns:
            List of block groups for paragraph-level translation
        """
        # Collect all text blocks with their metadata
        text_blocks = []
        for block in text_dict.get("blocks", []):
            if "lines" not in block:
                continue
            lines = block.get("lines", [])
            if not lines:
                continue
            
            block_text = ""
            for line in lines:
                for span in line.get("spans", []):
                    block_text += span.get("text", "")
            
            if not block_text.strip():
                continue
            
            first_span = lines[0].get("spans", [{}])[0] if lines[0].get("spans") else {}
            text_blocks.append({
                'block': block,
                'text': block_text.strip(),
                'font_size': first_span.get("size", 11),
                'font': first_span.get("font", ""),
                'is_bold': 'Bold' in first_span.get("font", "") or bool(first_span.get("flags", 0) & 16),
                'bbox': block.get("bbox", [0, 0, 0, 0]),
            })
        
        if not text_blocks:
            return []
        
        check_zones = header_zone_y is not None and footer_zone_y is not None
        
        merged_groups: List[List[Dict[str, Any]]] = []
        current_group: List[Dict[str, Any]] = [text_blocks[0]]
        
        for i in range(1, len(text_blocks)):
            prev = text_blocks[i - 1]
            curr = text_blocks[i]
            should_merge = True
            
            # Check 1: Previous block ends with sentence punctuation
            prev_text = prev['text'].rstrip()
            if prev_text and prev_text[-1] in '.!?':
                words = prev_text.split()
                if words:
                    last_word = words[-1].rstrip('.!?')
                    if len(last_word) > 3 or (last_word.isupper() and len(last_word) > 1):
                        should_merge = False
            
            # Check 1b: Previous block is short metadata (date, version, etc.)
            if should_merge:
                prev_lower = prev_text.lower()
                metadata_patterns = [
                    'draft:', 'first draft', 'version:', 'date:', 'revised:',
                    'bozza:', 'prima bozza', 'versione:', 'data:', 'revisionato:'
                ]
                is_metadata = any(pat in prev_lower for pat in metadata_patterns)
                if not is_metadata and len(prev_text) < 60:
                    import re as _re
                    if _re.search(r'\b(19|20)\d{2}\b\s*$', prev_text):
                        is_metadata = True
                if is_metadata and len(prev_text) < 60:
                    should_merge = False
            
            # Check 2: Font size change (likely heading)
            if should_merge:
                size_ratio = curr['font_size'] / prev['font_size'] if prev['font_size'] > 0 else 1
                if size_ratio > 1.15 or size_ratio < 0.85:
                    should_merge = False
            
            # Check 3: Bold status change (heading detection)
            if should_merge:
                if curr['is_bold'] != prev['is_bold']:
                    should_merge = False
            
            # Check 4: Short title-like line
            if should_merge:
                curr_text = curr['text']
                if len(curr_text) < 50 and len(curr_text.split()) <= 8:
                    if curr_text[-1] not in '.,;:':
                        if curr_text.istitle() or curr_text.isupper():
                            should_merge = False
            
            # Check 4b: Footnote pattern
            if should_merge:
                curr_text = curr['text'].strip()
                curr_y = curr['bbox'][1]
                if _is_likely_footnote_marker(curr_text, curr['font_size'], page_height, curr_y):
                    should_merge = False
            
            # Check 4c: List item
            if should_merge:
                if _is_list_item(curr['text'].strip()):
                    should_merge = False
            
            # Check 4d: Header/footer zone boundary (only when not pre-clipped)
            if should_merge and check_zones:
                prev_in_header = prev['bbox'][3] < header_zone_y
                curr_in_header = curr['bbox'][1] < header_zone_y
                prev_in_footer = prev['bbox'][1] > footer_zone_y
                curr_in_footer = curr['bbox'][1] > footer_zone_y
                if prev_in_header != curr_in_header:
                    should_merge = False
                elif prev_in_footer != curr_in_footer:
                    should_merge = False
            
            # Check 5: Significant vertical gap between blocks
            if should_merge:
                prev_bottom = prev['bbox'][3]
                curr_top = curr['bbox'][1]
                gap = curr_top - prev_bottom
                avg_font_size = (prev['font_size'] + curr['font_size']) / 2
                if gap > avg_font_size * 2:
                    should_merge = False
            
            # Check 6: Column detection via X-overlap (only in fallback path)
            if should_merge and check_x_overlap:
                prev_x0, prev_x1 = prev['bbox'][0], prev['bbox'][2]
                curr_x0, curr_x1 = curr['bbox'][0], curr['bbox'][2]
                overlap_start = max(prev_x0, curr_x0)
                overlap_end = min(prev_x1, curr_x1)
                overlap = max(0, overlap_end - overlap_start)
                min_width = min(prev_x1 - prev_x0, curr_x1 - curr_x0)
                min_width = max(min_width, 1)
                overlap_ratio = overlap / min_width
                if overlap_ratio < 0.30:
                    should_merge = False
                    logging.debug(
                        f"Column break: overlap {overlap_ratio:.1%} between "
                        f"'{prev['text'][:20]}…' and '{curr['text'][:20]}…'"
                    )
            
            if should_merge:
                current_group.append(curr)
            else:
                merged_groups.append(current_group)
                current_group = [curr]
        
        if current_group:
            merged_groups.append(current_group)
        
        logging.info(f"Block merge: {len(text_blocks)} blocks -> {len(merged_groups)} paragraph groups")
        return merged_groups
    
    def _merge_bboxes(self, bboxes: List[Tuple]) -> Tuple[float, float, float, float]:
        """Merge multiple bboxes into one encompassing bbox."""
        if not bboxes:
            return (0, 0, 0, 0)
        
        x0 = min(bbox[0] for bbox in bboxes)
        y0 = min(bbox[1] for bbox in bboxes)
        x1 = max(bbox[2] for bbox in bboxes)
        y1 = max(bbox[3] for bbox in bboxes)
        
        return (x0, y0, x1, y1)
    
    def _insert_line_translation(
        self,
        page: pymupdf.Page,
        line_data: dict,
        translated_text: str,
        text_color: Tuple[float, float, float],
        use_original_color: bool = False,
        preserve_font_style: bool = True,
        skip_clearing: bool = False
    ) -> None:
        """
        Insert translated text with maximum fidelity to original styling.
        
        Features:
        - Preserves font family style (serif, sans-serif, monospace)
        - Preserves bold/italic attributes
        - Optional original color preservation
        - Smart text wrapping for long translations
        - Dynamic font scaling with readability guarantees
        - Multi-level fallback ensures nothing is lost
        
        Args:
            skip_clearing: If True, skip clearing original text (already done via redaction)
        """
        WHITE = pymupdf.pdfcolor["white"]
        
        # Normalize text for PDF rendering (preserve typographic chars for native text)
        translated_text = _normalize_text_for_pdf(translated_text, is_ocr=False)
        
        # Clear all original spans (unless already cleared via redaction)
        if not skip_clearing:
            for bbox in line_data['bboxes']:
                try:
                    page.draw_rect(bbox, color=None, fill=WHITE)
                except Exception:
                    pass
        
        merged_bbox = line_data['merged_bbox']
        bbox_width = merged_bbox[2] - merged_bbox[0]
        bbox_height = merged_bbox[3] - merged_bbox[1]
        
        if bbox_width <= 0 or bbox_height <= 0:
            logging.warning(f"Invalid bbox dimensions: {merged_bbox}")
            return
        
        # Determine final color
        if use_original_color and 'dominant_color' in line_data:
            final_color = line_data['dominant_color']
        else:
            final_color = text_color
        
        # Calculate optimal font size
        target_font_size = line_data['avg_size']
        
        # Determine font family based on original
        if preserve_font_style:
            if line_data.get('is_monospace', False):
                font_family = '"Courier New", Courier, monospace'
                pdf_font = "cour"  # Courier
            elif line_data.get('is_serif', False):
                font_family = 'Georgia, "Times New Roman", Times, serif'
                pdf_font = "tiro"  # Times Roman
            else:
                font_family = '-apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif'
                pdf_font = "helv"  # Helvetica
        else:
            font_family = 'Helvetica, Arial, sans-serif'
            pdf_font = "helv"
        
        # Accurate text width measurement using PyMuPDF Font metrics
        try:
            measure_font = pymupdf.Font(pdf_font)
            estimated_width = measure_font.text_length(translated_text, fontsize=target_font_size)
        except Exception:
            # Fallback to rough estimation if Font creation fails
            estimated_width = len(translated_text) * target_font_size * 0.52
        
        # Determine if text needs wrapping (translated text wider than box)
        needs_wrapping = estimated_width > bbox_width
        # No bbox expansion — insert_htmlbox's scale_low handles fitting
        
        # Get rotation from line_data (0, 90, 180, 270)
        rotation = line_data.get('rotation', 0)
        
        # PRIMARY METHOD: Direct text insertion (no ligatures, reliable)
        # Only use htmlbox for wrapping since insert_text doesn't wrap
        if not needs_wrapping:
            try:
                # Calculate insertion point based on rotation
                if rotation == 0:
                    # Normal horizontal: top-left, baseline below top
                    insert_point = (merged_bbox[0], merged_bbox[1] + target_font_size)
                elif rotation == 90:
                    # Rotated 90° CCW (text goes up): bottom-left corner
                    insert_point = (merged_bbox[0] + target_font_size, merged_bbox[3])
                elif rotation == 180:
                    # Upside down: bottom-right corner
                    insert_point = (merged_bbox[2], merged_bbox[3] - target_font_size)
                elif rotation == 270:
                    # Rotated 270° CCW / 90° CW (text goes down): top-right corner
                    insert_point = (merged_bbox[2] - target_font_size, merged_bbox[1])
                else:
                    # Fallback to standard
                    insert_point = (merged_bbox[0], merged_bbox[1] + target_font_size)
                
                page.insert_text(
                    insert_point,
                    translated_text,
                    fontsize=target_font_size,
                    color=final_color,
                    fontname=pdf_font,
                    rotate=rotation
                )
                
                if rotation != 0:
                    logging.debug(f"[OK] Rotated text insertion successful (rotation={rotation}°)")
                else:
                    logging.debug(f"[OK] Text insertion successful (primary)")
                return
                
            except Exception as e:
                logging.debug(f"Text insertion failed: {e}, trying HTML fallback")
        
        # FALLBACK: HTML insertion for text wrapping (may introduce ligatures)
        css_color = f"rgb({int(final_color[0]*255)}, {int(final_color[1]*255)}, {int(final_color[2]*255)})"
        font_weight = 'bold' if line_data.get('is_bold', False) else 'normal'
        font_style = 'italic' if line_data.get('is_italic', False) else 'normal'
        
        # Try HTML insertion first (best quality, supports wrapping)
        try:
            # Adjust CSS based on whether we need wrapping
            if needs_wrapping:
                # Allow text wrapping
                white_space = "normal"
                word_wrap = "break-word"
                overflow = "visible"
                text_overflow = "clip"
            else:
                # Single line, no wrap
                white_space = "nowrap"
                word_wrap = "normal"
                overflow = "hidden"
                text_overflow = "ellipsis"
            
            css = f"""* {{
                font-family: {font_family};
                font-size: {target_font_size}pt;
                color: {css_color};
                font-weight: {font_weight};
                font-style: {font_style};
                line-height: 1.15;
                padding: 0;
                margin: 0;
                white-space: {white_space};
                word-wrap: {word_wrap};
                overflow: {overflow};
                text-overflow: {text_overflow};
                text-align: {line_data.get('text_align', 'left')};
                font-variant-ligatures: none;
                -webkit-font-variant-ligatures: none;
                font-feature-settings: "liga" 0, "clig" 0;
            }}"""
            
            page.insert_htmlbox(merged_bbox, translated_text, css=css, rotate=rotation, scale_low=0.5)
            if rotation != 0:
                logging.debug(f"[OK] HTML insertion successful (wrap={needs_wrapping}, rotation={rotation}°)")
            else:
                logging.debug(f"[OK] HTML insertion successful (wrap={needs_wrapping})")
            return
            
        except Exception as e:
            logging.warning(f"HTML insertion failed: {e}")
            # Final fallback: truncated text (with rotation support)
            try:
                # Calculate insertion point based on rotation (same as primary method)
                if rotation == 0:
                    insert_point = (merged_bbox[0], merged_bbox[1] + target_font_size)
                elif rotation == 90:
                    insert_point = (merged_bbox[0] + target_font_size, merged_bbox[3])
                elif rotation == 180:
                    insert_point = (merged_bbox[2], merged_bbox[3] - target_font_size)
                elif rotation == 270:
                    insert_point = (merged_bbox[2] - target_font_size, merged_bbox[1])
                else:
                    insert_point = (merged_bbox[0], merged_bbox[1] + target_font_size)
                
                # Accurate truncation using font metrics
                try:
                    _trunc_font = pymupdf.Font(pdf_font)
                    # Find how many chars fit by measuring progressively
                    _trunc_width = _trunc_font.text_length(translated_text, fontsize=target_font_size)
                    if _trunc_width > bbox_width:
                        # Use char_lengths for precise per-character measurement
                        _char_widths = _trunc_font.char_lengths(translated_text, fontsize=target_font_size)
                        _ellipsis_w = _trunc_font.text_length("...", fontsize=target_font_size)
                        _accum = 0.0
                        max_chars = 0
                        for _cw in _char_widths:
                            if _accum + _cw + _ellipsis_w > bbox_width:
                                break
                            _accum += _cw
                            max_chars += 1
                        display_text = translated_text[:max_chars] + "..." if max_chars < len(translated_text) else translated_text
                    else:
                        display_text = translated_text
                except Exception:
                    max_chars = int(bbox_width / (target_font_size * 0.45))
                    display_text = translated_text[:max_chars-3] + "..." if len(translated_text) > max_chars else translated_text
                
                page.insert_text(
                    insert_point,
                    display_text,
                    fontsize=target_font_size,
                    color=final_color,
                    fontname=pdf_font,
                    rotate=rotation
                )
                logging.debug(f"[OK] Truncated text insertion successful (rotation={rotation}°)")
            except Exception as final_error:
                capture_exception(final_error, context={"operation": "insert_text_final"}, tags={"component": "pdf_processor"})
                logging.error(f"All insertion methods failed: {final_error}")
    
    def close(self) -> None:
        """Close document and free resources."""
        if self.document:
            self.document.close()
    
    @classmethod
    def get_ocr_language(cls, language_name: str) -> str:
        """Get language code from language name.
        
        RapidOCR handles multiple languages. Returns a standard language
        code for logging/reference purposes.
        """
        from .config import SUPPORTED_LANGUAGES
        return SUPPORTED_LANGUAGES.get(language_name, "en")
