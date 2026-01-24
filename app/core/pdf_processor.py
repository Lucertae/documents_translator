"""
PDF processing module - PaddleOCR Edition
Handles PDF loading, text extraction, OCR, and manipulation with superior quality.

SPAN-LEVEL FORMATTING PRESERVATION:
This module now preserves formatting at the span level, not just line level.
This means bold, italic, color, and size are tracked per-segment and
intelligently mapped to the translated text using proportional allocation.

PaddleOCR Configuration (v3.3.3 with PP-OCRv5):
- Requires PaddlePaddle 3.2.x (3.3.0 has ONEDNN bug on CPU)
- PP-OCRv5 provides best accuracy for scanned documents
- Supports 80+ languages via 'lang' parameter
- use_textline_orientation=True enables automatic text orientation detection
"""
import logging
import math
import io
import os
import re
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
import pymupdf
from PIL import Image
import numpy as np

# Environment setup for PaddlePaddle CPU (must be before PaddleOCR import)
os.environ.setdefault('DISABLE_MODEL_SOURCE_CHECK', 'True')

# Import sentence-aware translation helpers
from .translator import split_into_sentences, align_sentences_to_lines

# Import centralized configuration
from .config import (
    DEFAULT_OCR_CONFIG,
    DEFAULT_TEXT_QUALITY_CONFIG,
    DEFAULT_SCAN_DETECTION_CONFIG,
    DEFAULT_PARAGRAPH_CONFIG,
    PADDLEOCR_LANGUAGES,
    LIGATURE_MAP,
    QUOTE_MAP,
    DASH_SPACE_MAP,
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
from .ocr_utils import clean_ocr_text, post_process_ocr_text

# Import Sentry integration
from .sentry_integration import capture_exception, add_breadcrumb, set_context


# NOTE: SpanFormat and LineFormatInfo classes moved to formatting.py
# NOTE: map_formatting_to_translation and helpers moved to format_utils.py
# NOTE: detect_title_or_heading moved to format_utils.py (simplified version)


# OCR and Document Analysis imports
try:
    from paddleocr import PaddleOCR, LayoutDetection
    OCR_AVAILABLE = True
    LAYOUT_DETECTION_AVAILABLE = True
except ImportError:
    try:
        from paddleocr import PaddleOCR
        OCR_AVAILABLE = True
        LAYOUT_DETECTION_AVAILABLE = False
    except ImportError:
        OCR_AVAILABLE = False
        LAYOUT_DETECTION_AVAILABLE = False
        logging.warning("OCR not available - install paddleocr for scanned PDF support")

# DocPreprocessor for automatic image correction (rotation, dewarping)
try:
    from paddleocr import DocPreprocessor
    DOC_PREPROCESSOR_AVAILABLE = True
except ImportError:
    DOC_PREPROCESSOR_AVAILABLE = False
    logging.debug("DocPreprocessor not available - install paddleocr[doc-parser] for better preprocessing")

# PPStructureV3 for advanced document structure analysis
try:
    from paddleocr import PPStructureV3
    PP_STRUCTURE_AVAILABLE = True
except ImportError:
    PP_STRUCTURE_AVAILABLE = False
    logging.debug("PPStructureV3 not available - install paddleocr[doc-parser] for advanced structure analysis")


class PDFProcessor:
    """
    Professional PDF processor with PaddleOCR (superior to Tesseract).
    Supports normal PDFs and scanned documents via state-of-the-art OCR.
    
    Advantages of PaddleOCR:
    - 3-5x faster than Tesseract
    - Higher accuracy (~95% vs ~85%)
    - Better handling of complex layouts
    - Automatic text detection (finds text regions)
    """
    
    # Singleton PaddleOCR instance (lazy loading)
    _ocr_engine = None
    _current_lang = None
    
    # Singleton LayoutDetection instance
    _layout_engine = None
    
    # Singleton DocPreprocessor instance
    _doc_preprocessor = None
    
    # Singleton PPStructureV3 instance
    _pp_structure = None
    
    def __init__(self, pdf_path: str):
        """
        Initialize PDF processor.
        
        Args:
            pdf_path: Path to PDF file
        """
        self.pdf_path = pdf_path
        self.document = None
        self.page_count = 0
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
            ocr_language: Language code for OCR (PaddleOCR format)
            
        Returns:
            Extracted text with best possible quality
        """
        page = self.get_page(page_num)
        
        # Step 1: Analyze page structure
        is_scanned, scan_reason = self._is_likely_scanned_page(page)
        
        if is_scanned:
            logging.info(f"Page {page_num + 1}: Detected as scanned ({scan_reason}), using OCR directly")
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
    
    @classmethod
    def _get_ocr_engine(cls, language: str):
        """Get or create PaddleOCR engine (singleton with language caching).
        
        Uses PP-OCRv5 models for best accuracy on CPU.
        Requires PaddlePaddle 3.2.x (3.3.0 has ONEDNN bug).
        """
        if cls._ocr_engine is None or cls._current_lang != language:
            logging.info(f"Initializing PaddleOCR PP-OCRv5 for language: {language}")
            try:
                # PaddleOCR 3.3.3 API with PP-OCRv5 (best quality on CPU)
                cls._ocr_engine = PaddleOCR(
                    lang=language,
                    use_textline_orientation=True,  # Auto-detect text orientation
                )
                cls._current_lang = language
                logging.info(f"[OK] PaddleOCR PP-OCRv5 initialized for {language}")
            except Exception as e:
                error_msg = str(e)
                capture_exception(e, context={
                    "operation": "init_paddleocr",
                    "language": language,
                    "error_type": "dependency" if "dependency" in error_msg.lower() else "other",
                }, tags={"component": "ocr"})
                logging.error(f"Failed to initialize PaddleOCR: {error_msg}")
                if "dependency error" in error_msg.lower() or "predictor creation" in error_msg.lower():
                    logging.error("=" * 60)
                    logging.error("PaddleOCR DEPENDENCY ERROR - Scanned PDFs not supported")
                    logging.error("This document appears to be a scanned image.")
                    logging.error("OCR requires additional Windows dependencies.")
                    logging.error("")
                    logging.error("SOLUTION: Use the Python version instead of the EXE:")
                    logging.error("  1. Install Python 3.11")
                    logging.error("  2. pip install -r requirements.txt")
                    logging.error("  3. python app/main_qt.py")
                    logging.error("=" * 60)
                cls._ocr_engine = None
        return cls._ocr_engine
    
    @classmethod
    def _get_layout_engine(cls):
        """Get or create LayoutDetection engine (singleton)."""
        if not LAYOUT_DETECTION_AVAILABLE:
            return None
        if cls._layout_engine is None:
            logging.info("Initializing LayoutDetection engine...")
            try:
                cls._layout_engine = LayoutDetection()
                logging.info("[OK] LayoutDetection initialized")
            except Exception as e:
                error_msg = str(e)
                if "dependency error" not in error_msg.lower():
                    capture_exception(e, context={"operation": "init_layout_detection"}, tags={"component": "ocr"})
                    logging.error(f"Failed to initialize LayoutDetection: {e}")
                cls._layout_engine = None
                cls._layout_engine = None
        return cls._layout_engine
    
    @classmethod
    def _get_doc_preprocessor(cls):
        """Get or create DocPreprocessor engine (singleton) for automatic image correction."""
        if not DOC_PREPROCESSOR_AVAILABLE:
            return None
        if cls._doc_preprocessor is None:
            logging.info("Initializing DocPreprocessor engine...")
            try:
                cls._doc_preprocessor = DocPreprocessor()
                logging.info("[OK] DocPreprocessor initialized")
            except Exception as e:
                capture_exception(e, context={"operation": "init_doc_preprocessor"}, tags={"component": "ocr"})
                logging.error(f"Failed to initialize DocPreprocessor: {e}")
                cls._doc_preprocessor = None
        return cls._doc_preprocessor
    
    @classmethod
    def _get_pp_structure(cls):
        """Get or create PPStructureV3 engine (singleton) for advanced document parsing."""
        if not PP_STRUCTURE_AVAILABLE:
            return None
        if cls._pp_structure is None:
            logging.info("Initializing PPStructureV3 engine...")
            try:
                cls._pp_structure = PPStructureV3()
                logging.info("[OK] PPStructureV3 initialized")
            except Exception as e:
                capture_exception(e, context={"operation": "init_pp_structure"}, tags={"component": "ocr"})
                logging.error(f"Failed to initialize PPStructureV3: {e}")
                cls._pp_structure = None
        return cls._pp_structure
    
    def _extract_via_ocr(self, page: pymupdf.Page, language: str) -> str:
        """
        Extract text using PaddleOCR v3+ with intelligent segmentation.
        
        Features:
        - Reading order detection (top-to-bottom, left-to-right)
        - Paragraph grouping based on vertical distance
        - Multi-column layout support
        - Preserves document structure with proper line breaks
        """
        try:
            logging.info(f"Attempting PaddleOCR extraction (language: {language})")
            
            # Convert PDF page to high-resolution image
            pix = page.get_pixmap(matrix=pymupdf.Matrix(2.0, 2.0))  # 2x scale for better quality
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            
            # Convert to numpy array (PaddleOCR input format)
            img_array = np.array(img)
            img_height, img_width = img_array.shape[:2]
            
            # Get PaddleOCR engine
            ocr = self._get_ocr_engine(language)
            if ocr is None:
                logging.warning("PaddleOCR engine not available")
                return ""
            
            # Run OCR with modern API
            result = ocr.predict(img_array)
            
            # Extract text from result (PaddleOCR v3+ format)
            if result and len(result) > 0:
                ocr_result = result[0]
                
                # Get texts, scores, and polygons
                texts = ocr_result.get('rec_texts', [])
                scores = ocr_result.get('rec_scores', [])
                polys = ocr_result.get('rec_polys', [])
                
                # Build text regions with position data
                MIN_CONFIDENCE = 0.5
                text_regions = []
                
                for i, (text, score, poly) in enumerate(zip(texts, scores, polys)):
                    if score >= MIN_CONFIDENCE and text.strip():
                        # Extract bounding box from polygon
                        # poly is typically [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                        try:
                            if hasattr(poly, 'tolist'):
                                poly = poly.tolist()
                            xs = [p[0] for p in poly]
                            ys = [p[1] for p in poly]
                            bbox = {
                                'x0': min(xs),
                                'y0': min(ys),
                                'x1': max(xs),
                                'y1': max(ys),
                                'center_x': sum(xs) / len(xs),
                                'center_y': sum(ys) / len(ys),
                                'height': max(ys) - min(ys),
                                'width': max(xs) - min(xs),
                            }
                            text_regions.append({
                                'text': text.strip(),
                                'score': score,
                                'bbox': bbox,
                            })
                        except Exception as e:
                            logging.debug(f"Failed to parse polygon {i}: {e}")
                            # Still include text without position
                            text_regions.append({
                                'text': text.strip(),
                                'score': score,
                                'bbox': None,
                            })
                
                if not text_regions:
                    logging.warning("PaddleOCR returned no valid text regions")
                    return ""
                
                # Apply intelligent segmentation
                extracted_text = self._segment_ocr_text(text_regions, img_width, img_height)
                logging.info(f"PaddleOCR successful: {len(extracted_text)} chars, {len(text_regions)} text regions")
                return extracted_text
            
            logging.warning("PaddleOCR returned no results")
            
        except Exception as e:
            capture_exception(e, context={"operation": "ocr_extract"}, tags={"component": "ocr"})
            logging.warning(f"PaddleOCR failed: {e}")
        return ""
    
    def _segment_ocr_text(
        self, 
        text_regions: List[dict], 
        img_width: int, 
        img_height: int
    ) -> str:
        """
        Intelligent text segmentation for OCR results.
        
        Algorithm:
        1. Detect columns by analyzing x-position distribution
        2. Sort text by reading order (column-aware)
        3. Group into paragraphs by vertical proximity
        4. Join with appropriate separators
        
        Args:
            text_regions: List of {'text': str, 'score': float, 'bbox': dict}
            img_width: Image width for column detection
            img_height: Image height for spacing calculations
            
        Returns:
            Properly segmented text with paragraph breaks
        """
        if not text_regions:
            return ""
        
        # Separate regions with and without position data
        positioned = [r for r in text_regions if r['bbox'] is not None]
        unpositioned = [r for r in text_regions if r['bbox'] is None]
        
        if not positioned:
            # No position data, just join texts
            return ' '.join(r['text'] for r in text_regions)
        
        # Step 1: Detect columns
        columns = self._detect_columns(positioned, img_width)
        logging.debug(f"Detected {len(columns)} column(s)")
        
        # Step 2: Process each column
        all_paragraphs = []
        
        for col_idx, column_regions in enumerate(columns):
            # Sort by vertical position (top to bottom)
            column_regions.sort(key=lambda r: r['bbox']['y0'])
            
            # Step 3: Group into paragraphs
            paragraphs = self._group_into_paragraphs(column_regions)
            all_paragraphs.extend(paragraphs)
        
        # Step 4: Build final text with OCR post-processing
        result_parts = []
        for para in all_paragraphs:
            para_text = ' '.join(para)
            if para_text.strip():
                # Apply OCR post-processing to fix common errors (MimakI -> Mimaki, etc.)
                para_text = clean_ocr_text(para_text.strip())
                result_parts.append(para_text)
        
        # Add unpositioned text at the end
        if unpositioned:
            unpositioned_text = ' '.join(r['text'] for r in unpositioned)
            unpositioned_text = clean_ocr_text(unpositioned_text)
            result_parts.append(unpositioned_text)
        
        # Join paragraphs with double newline
        return '\n\n'.join(result_parts)
    
    def _detect_columns(
        self, 
        text_regions: List[dict], 
        img_width: int
    ) -> List[List[dict]]:
        """
        Detect column layout by analyzing x-position distribution.
        
        Uses gap analysis to find column boundaries.
        """
        if not text_regions or len(text_regions) < 3:
            return [text_regions]
        
        # Get all center x positions
        x_positions = sorted(r['bbox']['center_x'] for r in text_regions)
        
        # Find large gaps that might indicate column boundaries
        # A gap larger than 15% of page width suggests columns
        min_gap = img_width * 0.15
        
        gaps = []
        for i in range(len(x_positions) - 1):
            gap = x_positions[i + 1] - x_positions[i]
            if gap > min_gap:
                # Store gap position (midpoint)
                gaps.append((x_positions[i] + x_positions[i + 1]) / 2)
        
        if not gaps:
            # Single column layout
            return [text_regions]
        
        # Sort gaps and use them as column boundaries
        gaps.sort()
        
        # Assign regions to columns
        boundaries = [0] + gaps + [img_width]
        columns = [[] for _ in range(len(boundaries) - 1)]
        
        for region in text_regions:
            center_x = region['bbox']['center_x']
            for col_idx in range(len(boundaries) - 1):
                if boundaries[col_idx] <= center_x < boundaries[col_idx + 1]:
                    columns[col_idx].append(region)
                    break
        
        # Remove empty columns
        columns = [col for col in columns if col]
        
        return columns if columns else [text_regions]
    
    def _group_into_paragraphs(
        self, 
        sorted_regions: List[dict]
    ) -> List[List[str]]:
        """
        Group text lines into paragraphs based on vertical spacing.
        
        Uses adaptive threshold based on average line height.
        """
        if not sorted_regions:
            return []
        
        if len(sorted_regions) == 1:
            return [[sorted_regions[0]['text']]]
        
        # Calculate average line height
        heights = [r['bbox']['height'] for r in sorted_regions if r['bbox']['height'] > 0]
        avg_height = sum(heights) / len(heights) if heights else 20
        
        # Paragraph break threshold: 1.5x average line height
        para_threshold = avg_height * 1.5
        
        paragraphs = []
        current_para = [sorted_regions[0]['text']]
        prev_region = sorted_regions[0]
        
        for region in sorted_regions[1:]:
            # Calculate vertical gap from previous region
            vertical_gap = region['bbox']['y0'] - prev_region['bbox']['y1']
            
            if vertical_gap > para_threshold:
                # Start new paragraph
                if current_para:
                    paragraphs.append(current_para)
                current_para = [region['text']]
            else:
                # Continue current paragraph
                current_para.append(region['text'])
            
            prev_region = region
        
        # Don't forget the last paragraph
        if current_para:
            paragraphs.append(current_para)
        
        return paragraphs
    
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
        Translate a scanned (image-based) page using CLEAN SLATE approach.
        
        Strategy (CLEAN SLATE - no overlapping issues):
        1. Create a NEW BLANK PAGE with same dimensions
        2. Use LayoutDetection to identify columns and text regions  
        3. Run PaddleOCR to extract all text with positions
        4. Group text by COLUMN to respect layout
        5. Translate each column separately
        6. Insert translated text into column boundaries on blank page
        
        This approach avoids:
        - Text overlapping (each column has its own space)
        - Original text showing through (blank page)
        - Redaction failures
        
        Args:
            new_doc: Document to modify (will be replaced with clean page)
            page: Original page to translate
            page_num: Page number (for logging)
            translator: Translation engine
            text_color: Color for translated text
            ocr_language: Language code for OCR
            
        Returns:
            New document with translated content on clean page
        """
        if not OCR_AVAILABLE:
            logging.warning(f"Page {page_num + 1}: OCR not available, cannot translate scanned page")
            return new_doc
        
        try:
            # ============================================
            # STEP 0: Get page dimensions
            # ============================================
            page_rect = page.rect
            page_width = page_rect.width
            page_height = page_rect.height
            
            # Convert page to image for OCR
            ocr_scale = 2.0
            pix = page.get_pixmap(matrix=pymupdf.Matrix(ocr_scale, ocr_scale))
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            img_array = np.array(img)
            img_array_original = img_array.copy()  # Keep original for layout detection
            
            # ============================================
            # STEP 1: Layout Detection - AUTOMATIC column detection
            # Run on ORIGINAL image to get accurate column coordinates
            # ============================================
            layout_engine = self._get_layout_engine()
            num_columns = 1
            column_boundaries = [(0, page_width)]  # List of (x0, x1) tuples
            
            if layout_engine and LAYOUT_DETECTION_AVAILABLE:
                logging.info(f"Page {page_num + 1}: Running LayoutDetection...")
                try:
                    layout_result = layout_engine.predict(img_array_original)
                    if layout_result and len(layout_result) > 0:
                        boxes = layout_result[0].get('boxes', [])
                        text_boxes = [b for b in boxes if b.get('label') in ['text', 'title', 'content'] and b.get('score', 0) > 0.5]
                        
                        if text_boxes:
                            # Auto-detect columns by clustering X centers
                            x_centers = []
                            for box in text_boxes:
                                coord = box['coordinate']
                                x0 = coord[0] / ocr_scale
                                x1 = coord[2] / ocr_scale
                                x_centers.append({
                                    'center': (x0 + x1) / 2,
                                    'x0': x0,
                                    'x1': x1
                                })
                            
                            # Sort by center X
                            x_centers.sort(key=lambda c: c['center'])
                            
                            # Find gaps to identify column boundaries
                            # Gap = significant horizontal space between regions
                            # Use adaptive gap: smaller of 3% page width or 30pts
                            MIN_GAP = min(page_width * 0.03, 30)
                            column_clusters = []
                            current_cluster = [x_centers[0]]
                            
                            for i in range(1, len(x_centers)):
                                prev_right = max(c['x1'] for c in current_cluster)
                                curr_left = x_centers[i]['x0']
                                gap = curr_left - prev_right
                                
                                if gap > MIN_GAP:
                                    # New column detected
                                    column_clusters.append(current_cluster)
                                    current_cluster = [x_centers[i]]
                                else:
                                    current_cluster.append(x_centers[i])
                            
                            column_clusters.append(current_cluster)
                            num_columns = len(column_clusters)
                            
                            # Calculate boundaries for each column
                            column_boundaries = []
                            for cluster in column_clusters:
                                col_x0 = min(c['x0'] for c in cluster) - 5
                                col_x1 = max(c['x1'] for c in cluster) + 5
                                column_boundaries.append((max(0, col_x0), min(page_width, col_x1)))
                            
                            logging.info(f"Page {page_num + 1}: Auto-detected {num_columns} columns: {[(int(b[0]), int(b[1])) for b in column_boundaries]}")
                except Exception as e:
                    logging.warning(f"Page {page_num + 1}: LayoutDetection failed: {e}")
            
            # ============================================
            # STEP 2: Preprocess image (rotation, dewarping) - for OCR only
            # Note: We use original coordinates for layout, but preprocessed image for better OCR
            # ============================================
            doc_preprocessor = self._get_doc_preprocessor()
            if doc_preprocessor and DOC_PREPROCESSOR_AVAILABLE:
                logging.info(f"Page {page_num + 1}: Running DocPreprocessor...")
                try:
                    preprocess_result = doc_preprocessor.predict(img_array)
                    if preprocess_result and len(preprocess_result) > 0:
                        result_data = preprocess_result[0]
                        angle = result_data.get('angle', 0)
                        if angle != 0:
                            logging.info(f"Page {page_num + 1}: Detected rotation of {angle}°, correcting...")
                        if 'output_img' in result_data and result_data['output_img'] is not None:
                            # Only use preprocessed image if dimensions match (no rotation)
                            preprocessed = result_data['output_img']
                            if preprocessed.shape == img_array.shape:
                                img_array = preprocessed
                                logging.info(f"Page {page_num + 1}: Image preprocessing applied")
                            else:
                                logging.warning(f"Page {page_num + 1}: Skipping preprocessing (shape mismatch)")
                except Exception as e:
                    logging.warning(f"Page {page_num + 1}: DocPreprocessor failed: {e}")
            
            # ============================================
            # STEP 3: Run OCR
            # ============================================
            ocr = self._get_ocr_engine(ocr_language)
            if ocr is None:
                logging.error(f"Page {page_num + 1}: Failed to get OCR engine")
                return new_doc
            
            logging.info(f"Page {page_num + 1}: Running PaddleOCR...")
            result = None
            for attempt in range(2):
                try:
                    result = ocr.predict(img_array)
                    break
                except RuntimeError as e:
                    logging.warning(f"Page {page_num + 1}: OCR attempt {attempt + 1} failed: {e}")
                    if attempt == 0:
                        pix_low = page.get_pixmap(matrix=pymupdf.Matrix(1.5, 1.5))
                        img_low = Image.open(io.BytesIO(pix_low.tobytes("png")))
                        img_array = np.array(img_low)
                        ocr_scale = 1.5
            
            if not result or len(result) == 0:
                logging.warning(f"Page {page_num + 1}: OCR returned no results")
                return new_doc
            
            ocr_result = result[0]
            texts = ocr_result.get('rec_texts', [])
            scores = ocr_result.get('rec_scores', [])
            polys = ocr_result.get('rec_polys', [])
            
            if not texts:
                logging.warning(f"Page {page_num + 1}: No text found by OCR")
                return new_doc
            
            logging.info(f"Page {page_num + 1}: OCR found {len(texts)} text regions")
            
            # ============================================
            # STEP 4: Build text regions and assign columns dynamically
            # ============================================
            MIN_CONFIDENCE = 0.5
            text_regions = []
            
            for text, score, poly in zip(texts, scores, polys):
                if score < MIN_CONFIDENCE or not text.strip():
                    continue
                try:
                    if hasattr(poly, 'tolist'):
                        poly = poly.tolist()
                    xs = [p[0] / ocr_scale for p in poly]
                    ys = [p[1] / ocr_scale for p in poly]
                    
                    bbox = pymupdf.Rect(min(xs), min(ys), max(xs), max(ys))
                    center_x = (min(xs) + max(xs)) / 2
                    center_y = (min(ys) + max(ys)) / 2
                    
                    # Find which column this region belongs to
                    column = 0
                    for col_idx, (col_x0, col_x1) in enumerate(column_boundaries):
                        if col_x0 <= center_x <= col_x1:
                            column = col_idx
                            break
                    else:
                        # If not in any boundary, find closest column
                        min_dist = float('inf')
                        for col_idx, (col_x0, col_x1) in enumerate(column_boundaries):
                            col_center = (col_x0 + col_x1) / 2
                            dist = abs(center_x - col_center)
                            if dist < min_dist:
                                min_dist = dist
                                column = col_idx
                    
                    text_regions.append({
                        'text': text.strip(),
                        'bbox': bbox,
                        'center_x': center_x,
                        'center_y': center_y,
                        'height': max(ys) - min(ys),
                        'x0': min(xs),
                        'column': column
                    })
                except Exception:
                    continue
            
            if not text_regions:
                logging.warning(f"Page {page_num + 1}: No valid text regions")
                return new_doc
            
            # ============================================
            # STEP 5: Group into lines BY COLUMN
            # ============================================
            columns_data = {}
            for region in text_regions:
                col = region['column']
                if col not in columns_data:
                    columns_data[col] = []
                columns_data[col].append(region)
            
            all_lines = []
            for col_idx in sorted(columns_data.keys()):
                col_regions = columns_data[col_idx]
                col_regions.sort(key=lambda r: (r['center_y'], r['x0']))
                
                lines = []
                if col_regions:
                    current_line = [col_regions[0]]
                    LINE_THRESHOLD = col_regions[0]['height'] * 0.6
                    
                    for region in col_regions[1:]:
                        if abs(region['center_y'] - current_line[0]['center_y']) < LINE_THRESHOLD:
                            current_line.append(region)
                        else:
                            lines.append((col_idx, current_line))
                            current_line = [region]
                            LINE_THRESHOLD = region['height'] * 0.6
                    lines.append((col_idx, current_line))
                all_lines.extend(lines)
            
            logging.info(f"Page {page_num + 1}: {len(all_lines)} lines in {len(columns_data)} column(s)")
            
            # ============================================
            # STEP 5.5: Group lines into PARAGRAPHS and fix hyphenation
            # ============================================
            import re
            
            def is_section_number(text):
                """Check if text is just a section number like '4.6', '5.7', '2.1'"""
                text = text.strip()
                return bool(re.match(r'^\d+\.?\d*\.?\s*$', text))
            
            def is_title_or_heading(text):
                """Detect if text is a title/heading (Article X, numbered sections, etc.)"""
                text = text.strip()
                # Article headers: "Article 1", "Article 2 - Title"
                if re.match(r'^Article\s+\d+', text, re.IGNORECASE):
                    return True
                # Section numbers alone: "2.1", "4.6", "5.7" - these are headings
                if re.match(r'^\d+\.\d+\.?\s*$', text):
                    return True
                # All caps titles
                if text.isupper() and len(text) > 3:
                    return True
                return False
            
            def ends_sentence(text):
                """Check if text ends with sentence-ending punctuation"""
                text = text.strip()
                return text.endswith('.') or text.endswith('!') or text.endswith('?') or text.endswith(':')
            
            def fix_hyphenation(line1, line2):
                """Join hyphenated words across lines: 're-' + 'sponsible' -> 'responsible'"""
                if line1.rstrip().endswith('-'):
                    # Remove the hyphen and join with next word
                    line1_fixed = line1.rstrip()[:-1]
                    # Find first word of line2
                    words = line2.split(None, 1)
                    if words:
                        first_word = words[0]
                        rest = words[1] if len(words) > 1 else ''
                        return line1_fixed + first_word, rest
                return line1, line2
            
            def clean_inline_section_numbers(text):
                """Remove section numbers that appear inline within text (margin annotations)"""
                # Remove patterns like " 4.6 " or " 5.7 " that appear mid-text
                # Pattern 1: number.number surrounded by text (not at line start)
                cleaned = re.sub(r'(?<=\S)\s+\d+\.\d+\s+(?=\S)', ' ', text)
                # Pattern 2: standalone single digit like " 5 " mid-sentence (page numbers, etc)
                cleaned = re.sub(r'(?<=[a-zA-Z])\s+\d\s+(?=[A-Z])', ' ', cleaned)
                # Pattern 3: number.number after punctuation and space
                cleaned = re.sub(r'([.!?])\s+\d+\.\d+\s+', r'\1 ', cleaned)
                # Also clean up multiple spaces
                cleaned = re.sub(r'\s+', ' ', cleaned)
                return cleaned.strip()
            
            # Build paragraphs from lines, respecting column boundaries
            paragraphs_by_column = {i: [] for i in range(num_columns)}
            
            for col_idx in sorted(columns_data.keys()):
                col_lines = [(idx, regions) for idx, regions in all_lines if idx == col_idx]
                
                if not col_lines:
                    continue
                
                current_paragraph_texts = []
                current_paragraph_regions = []
                
                for _, line_regions in col_lines:
                    line_regions_sorted = sorted(line_regions, key=lambda r: r['x0'])
                    line_text = ' '.join(r['text'] for r in line_regions_sorted)
                    
                    # Skip lines that are just section numbers (margin annotations)
                    if is_section_number(line_text):
                        continue
                    
                    # Check if this is a title/heading - start new paragraph
                    if is_title_or_heading(line_text):
                        # Save current paragraph if exists
                        if current_paragraph_texts:
                            paragraphs_by_column[col_idx].append({
                                'texts': current_paragraph_texts,
                                'regions': current_paragraph_regions
                            })
                        # Title is its own paragraph
                        paragraphs_by_column[col_idx].append({
                            'texts': [line_text],
                            'regions': line_regions_sorted
                        })
                        current_paragraph_texts = []
                        current_paragraph_regions = []
                        continue
                    
                    # Handle hyphenation with previous line
                    if current_paragraph_texts:
                        prev_text = current_paragraph_texts[-1]
                        fixed_prev, fixed_current = fix_hyphenation(prev_text, line_text)
                        current_paragraph_texts[-1] = fixed_prev
                        line_text = fixed_current if fixed_current else line_text
                    
                    current_paragraph_texts.append(line_text)
                    current_paragraph_regions.extend(line_regions_sorted)
                    
                    # Check if paragraph ends (sentence ends)
                    if ends_sentence(line_text):
                        paragraphs_by_column[col_idx].append({
                            'texts': current_paragraph_texts,
                            'regions': current_paragraph_regions
                        })
                        current_paragraph_texts = []
                        current_paragraph_regions = []
                
                # Don't forget remaining text
                if current_paragraph_texts:
                    paragraphs_by_column[col_idx].append({
                        'texts': current_paragraph_texts,
                        'regions': current_paragraph_regions
                    })
            
            total_paragraphs = sum(len(p) for p in paragraphs_by_column.values())
            logging.info(f"Page {page_num + 1}: {total_paragraphs} paragraphs grouped from {len(all_lines)} lines")
            
            # ============================================
            # STEP 6: Translate PARAGRAPHS and prepare column content
            # ============================================
            column_content = {i: [] for i in range(num_columns)}
            
            for col_idx in sorted(paragraphs_by_column.keys()):
                paragraphs = paragraphs_by_column[col_idx]
                
                for para in paragraphs:
                    # Join all lines in paragraph with space
                    para_text = ' '.join(para['texts'])
                    # Clean up inline section numbers and extra spaces
                    para_text = clean_inline_section_numbers(para_text)
                    # Apply OCR post-processing to fix common errors
                    para_text = clean_ocr_text(para_text)
                    
                    if not para_text:
                        continue
                    
                    # Calculate bounding box for entire paragraph
                    regions = para['regions']
                    if not regions:
                        continue
                    
                    para_bbox = pymupdf.Rect(
                        min(r['bbox'].x0 for r in regions),
                        min(r['bbox'].y0 for r in regions),
                        max(r['bbox'].x1 for r in regions),
                        max(r['bbox'].y1 for r in regions)
                    )
                    avg_height = sum(r['height'] for r in regions) / len(regions)
                    
                    # Translate the whole paragraph
                    translated = translator.translate(para_text)
                    if translated and translated.strip():
                        column_content[col_idx].append({
                            'y': para_bbox.y0,
                            'text': translated.strip(),
                            'height': avg_height,
                            'original_bbox': para_bbox,
                            'para_height': para_bbox.height  # Full paragraph height for text box
                        })
            
            # ============================================
            # STEP 7: CREATE CLEAN PAGE and insert text
            # ============================================
            # Delete existing page content and create blank
            new_page = new_doc[0]
            
            # Clear everything - draw white rectangle over entire page
            new_page.draw_rect(page_rect, color=(1, 1, 1), fill=(1, 1, 1))
            
            # Use detected column boundaries with small margin adjustments
            margin_top = 30
            line_spacing = 1.3
            
            # Insert translated text column by column
            total_inserted = 0
            
            # Track current Y position per column to avoid overlaps
            column_y_tracker = {}
            
            for col_idx in sorted(column_content.keys()):
                content = column_content[col_idx]
                if not content:
                    continue
                
                # Get column boundaries from auto-detected list
                if col_idx < len(column_boundaries):
                    col_x0, col_x1 = column_boundaries[col_idx]
                else:
                    # Fallback if column index out of range
                    continue
                
                col_width = col_x1 - col_x0
                if col_width < 50:
                    continue
                
                # Initialize Y tracker for this column
                current_y = None
                
                # Insert each paragraph in column
                for item in content:
                    original_y = item['y']
                    text = item['text']
                    height = item['height']
                    # Use full paragraph height if available
                    para_height = item.get('para_height', height * line_spacing)
                    
                    # Prevent overlaps: use max of original position and current tracker
                    if current_y is None:
                        y_pos = original_y
                    else:
                        # Add small gap between blocks (3pt)
                        y_pos = max(original_y, current_y + 3)
                    
                    # Font size: minimum 8pt for readability, max 12pt
                    font_size = max(8, min(height * 0.85, 12))
                    
                    try:
                        # Calculate text box height
                        box_height = max(para_height, height * 2)
                        text_rect = pymupdf.Rect(col_x0, y_pos, col_x1, y_pos + box_height)
                        
                        excess = new_page.insert_textbox(
                            text_rect,
                            text,
                            fontsize=font_size,
                            fontname="helv",
                            color=text_color,
                            align=0
                        )
                        
                        if excess < 0:
                            # Text didn't fit, try smaller font and expand box
                            box_height = para_height * 1.5
                            expanded_rect = pymupdf.Rect(col_x0, y_pos, col_x1, y_pos + box_height)
                            new_page.insert_textbox(
                                expanded_rect,
                                text,
                                fontsize=max(7, font_size * 0.8),  # Min 7pt fallback
                                fontname="helv",
                                color=text_color,
                                align=0
                            )
                        
                        # Update Y tracker to end of this block
                        current_y = y_pos + box_height
                        total_inserted += 1
                    except Exception as e:
                        logging.debug(f"Failed to insert paragraph: {e}")
            
            logging.info(f"Page {page_num + 1}: Clean page created with {total_inserted} translated lines")
            return new_doc
            
        except Exception as e:
            capture_exception(e, context={
                "operation": "translate_ocr_page",
                "page_num": page_num,
            }, tags={"component": "pdf_processor"})
            logging.error(f"Page {page_num + 1}: OCR translation failed: {e}", exc_info=True)
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
        - Uses PaddleOCR to extract text with bounding boxes
        - Overlays translated text on top of the scanned image
        
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
            logging.info(f"Page {page_num + 1}: Detected as scanned ({scan_reason}), using OCR translation mode")
            return self._translate_scanned_page(
                new_doc, page, page_num, translator, 
                text_color, ocr_language
            )
        
        text_dict = page.get_text("dict")
        
        # Collect ALL areas to redact (will be applied in bulk before insertions)
        areas_to_redact = []
        # Collect all translations to insert (after redaction)
        translations_to_insert = []
        
        translated_count = 0
        total_blocks = len([b for b in text_dict.get("blocks", []) if "lines" in b])
        
        logging.info(f"Page {page_num + 1}: Found {total_blocks} text blocks to process (preserve_line_breaks={preserve_line_breaks})")
        
        # ============================================
        # PHASE 0: Pre-merge single-line blocks into paragraph groups
        # ============================================
        # Many PDFs have each line as a separate block, which defeats paragraph-level
        # translation. We first merge adjacent blocks that belong to the same paragraph.
        merged_block_groups = self._merge_single_line_blocks(text_dict)
        
        # ============================================
        # PHASE 1: Extract structure with SPAN-LEVEL formatting
        # ============================================
        for group_idx, block_group in enumerate(merged_block_groups):
            # Collect lines_info from ALL blocks in this group
            lines_info: List[LineFormatInfo] = []
            
            for block_data in block_group:
                block = block_data['block']
                
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
                        line_text = " ".join(s.text for s in span_formats)
                        merged_bbox = self._merge_bboxes(line_bboxes)
                        
                        line_info = LineFormatInfo(
                            text=line_text,
                            spans=span_formats,
                            merged_bbox=merged_bbox,
                            rotation=rotation,
                            wmode=line_wmode
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
        
        for bbox in areas_to_redact:
            try:
                # Add redaction annotation with white fill
                rect = pymupdf.Rect(bbox)
                page.add_redact_annot(rect, fill=(1, 1, 1))
            except Exception as e:
                logging.warning(f"Failed to add redaction for {bbox}: {e}")
        
        # Apply all redactions at once (this actually removes the text)
        page.apply_redactions()
        logging.info(f"Redactions applied successfully")
        
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
                char_width_factor = 0.6
            elif line_info.is_serif:
                font_family = 'Georgia, "Times New Roman", Times, serif'
                char_width_factor = 0.5
            else:
                font_family = '-apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif'
                char_width_factor = 0.52
        else:
            font_family = 'Helvetica, Arial, sans-serif'
            char_width_factor = 0.52
        
        # Strip HTML tags for width calculation
        plain_text = re.sub(r'<[^>]+>', '', formatted_html)
        plain_text = plain_text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"')
        
        # Character width estimation
        avg_char_width = target_font_size * char_width_factor
        estimated_width = len(plain_text) * avg_char_width
        
        # Determine if we need text wrapping
        needs_wrapping = estimated_width > bbox_width * 1.5
        
        # IMPORTANT: Keep original font size - do NOT scale
        # The original size is preserved to maintain document appearance
        # If text doesn't fit, we use wrapping instead of shrinking
        if estimated_width > bbox_width and not needs_wrapping:
            # Allow wrapping for long text rather than shrinking
            needs_wrapping = True
        
        # Expand bbox height if text needs wrapping (Italian ~15-20% longer than English)
        if needs_wrapping:
            estimated_lines = max(1, estimated_width / bbox_width)
            line_height = target_font_size * 1.2  # slightly more than CSS line-height for safety
            required_height = estimated_lines * line_height
            if required_height > bbox_height:
                # Expand bbox downward to fit wrapped text
                # Use 30% buffer and allow up to 3x height for very long translations
                expanded_height = min(required_height * 1.3, bbox_height * 3.0)
                merged_bbox = (merged_bbox[0], merged_bbox[1], merged_bbox[2], merged_bbox[1] + expanded_height)
                bbox_height = expanded_height
                logging.debug(f"Expanded bbox height: {required_height:.1f} -> {expanded_height:.1f}pt")
        
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
                # Footnotes: allow up to 50% shrinking for dense text
                scale_low = 0.5
            else:
                # Normal text: allow up to 40% shrinking
                scale_low = 0.6
            
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
    
    def _group_lines_into_paragraphs(
        self, 
        lines_info: List[LineFormatInfo]
    ) -> List[List[LineFormatInfo]]:
        """
        Group lines into logical paragraphs for translation.
        
        This intelligently detects paragraph boundaries to ensure:
        - Titles/headings are translated separately
        - Paragraph text flows naturally within the group
        - Structure is preserved when line breaks are meaningful
        
        Paragraph break indicators:
        1. Previous line ends with sentence punctuation (. ! ? :)
        2. Current line has significantly different font size (±20%)
        3. Current line is bold when previous wasn't (or vice versa)
        4. Current line is very short (< 40 chars) and looks like a title
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
            
            # Check 2: Significant font size change (likely heading)
            if not should_break:
                size_ratio = curr_line.avg_size / prev_line.avg_size if prev_line.avg_size > 0 else 1
                if size_ratio > 1.2 or size_ratio < 0.8:
                    should_break = True
                    break_reason = f"size_change ({size_ratio:.2f})"
            
            # Check 3: Bold status change (heading detection)
            if not should_break:
                if curr_line.is_bold != prev_line.is_bold:
                    # Current line is bold (start of heading) or previous was bold (end of heading)
                    should_break = True
                    break_reason = "bold_change"
            
            # Check 4: Short line that looks like a title
            if not should_break:
                curr_text = curr_line.text.strip()
                # Short, possibly title-case, no ending punctuation
                if (len(curr_text) < 50 and 
                    len(curr_text.split()) <= 6 and
                    curr_text and 
                    curr_text[-1] not in '.,;'):
                    # Additional check: is it title case or all caps?
                    if curr_text.istitle() or curr_text.isupper():
                        should_break = True
                        break_reason = "title_pattern"
            
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
    
    def _merge_single_line_blocks(
        self,
        text_dict: Dict[str, Any]
    ) -> List[List[Dict[str, Any]]]:
        """
        Merge adjacent single-line blocks into logical paragraph groups.
        
        Many PDFs (especially those from LaTeX) have each line as a separate block.
        This defeats paragraph-level translation. This function pre-merges blocks
        that should be translated together.
        
        Merge conditions (consecutive blocks are merged if ALL are true):
        1. Previous block does NOT end with sentence punctuation (.!?)
        2. Font size is similar (within 15%)
        3. Font style (bold) is the same
        4. Not a short title-like line
        
        Break conditions (start new paragraph):
        1. Previous line ends with .!?
        2. Significant font size change (heading)
        3. Bold status changes
        4. Current line looks like a title (short, title case, no ending punct)
        
        Args:
            text_dict: The page text dictionary from get_text("dict")
            
        Returns:
            List of block groups, where each group is a list of blocks
            that should be translated together as one paragraph
        """
        # First collect all text blocks with their lines
        text_blocks = []
        for block in text_dict.get("blocks", []):
            if "lines" not in block:
                continue
            
            lines = block.get("lines", [])
            if not lines:
                continue
            
            # Get combined text from all spans in all lines
            block_text = ""
            for line in lines:
                for span in line.get("spans", []):
                    block_text += span.get("text", "")
            
            if not block_text.strip():
                continue
            
            # Get formatting info from first span of first line
            first_span = lines[0].get("spans", [{}])[0] if lines[0].get("spans") else {}
            
            text_blocks.append({
                'block': block,
                'text': block_text.strip(),
                'font_size': first_span.get("size", 11),
                'font': first_span.get("font", ""),
                'is_bold': 'Bold' in first_span.get("font", "") or bool(first_span.get("flags", 0) & 16),
                'bbox': block.get("bbox", [0, 0, 0, 0])
            })
        
        if not text_blocks:
            return []
        
        # Now merge consecutive blocks based on paragraph logic
        merged_groups: List[List[Dict[str, Any]]] = []
        current_group: List[Dict[str, Any]] = [text_blocks[0]]
        
        for i in range(1, len(text_blocks)):
            prev = text_blocks[i - 1]
            curr = text_blocks[i]
            
            should_merge = True
            
            # Check 1: Previous block ends with sentence punctuation
            prev_text = prev['text'].rstrip()
            if prev_text and prev_text[-1] in '.!?':
                # Check it's not an abbreviation (e.g., "Dr." "Fig." "etc.")
                words = prev_text.split()
                if words:
                    last_word = words[-1].rstrip('.!?')
                    # Not an abbreviation if word is longer than 3 chars
                    # or if it's all caps (likely acronym sentence end)
                    if len(last_word) > 3 or (last_word.isupper() and len(last_word) > 1):
                        should_merge = False
            
            # Check 1b: Previous block is short metadata (date, version, etc.)
            # These standalone lines should NOT merge with body text
            if should_merge:
                prev_lower = prev_text.lower()
                # Pattern: short line with date/version indicators
                metadata_patterns = [
                    'draft:', 'first draft', 'version:', 'date:', 'revised:',
                    'bozza:', 'prima bozza', 'versione:', 'data:', 'revisionato:'
                ]
                is_metadata = any(pat in prev_lower for pat in metadata_patterns)
                # Also catch lines ending with a year (e.g., "April 11, 2015")
                if not is_metadata and len(prev_text) < 60:
                    import re
                    if re.search(r'\b(19|20)\d{2}\b\s*$', prev_text):
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
                # Short, title-case or all caps, no ending punctuation
                if len(curr_text) < 50 and len(curr_text.split()) <= 8:
                    if curr_text[-1] not in '.,;:':
                        if curr_text.istitle() or curr_text.isupper():
                            should_merge = False
            
            # Check 4b: Footnote pattern - current text starts with number
            # (e.g., "3 Rakoff 1983" or "2 Throughout...")
            if should_merge:
                import re
                curr_text = curr['text'].strip()
                if re.match(r'^\d+\s', curr_text):
                    # Looks like a footnote, don't merge
                    should_merge = False
            
            # Check 5: Significant vertical gap between blocks
            if should_merge:
                prev_bottom = prev['bbox'][3]  # y1
                curr_top = curr['bbox'][1]      # y0
                gap = curr_top - prev_bottom
                avg_font_size = (prev['font_size'] + curr['font_size']) / 2
                
                # Gap larger than 2x font size suggests paragraph break
                if gap > avg_font_size * 2:
                    should_merge = False
            
            # Check 6: COLUMN DETECTION - blocks must have X overlap to merge
            # This prevents merging blocks from different columns
            if should_merge:
                prev_x0, prev_x1 = prev['bbox'][0], prev['bbox'][2]
                curr_x0, curr_x1 = curr['bbox'][0], curr['bbox'][2]
                
                # Calculate horizontal overlap
                overlap_start = max(prev_x0, curr_x0)
                overlap_end = min(prev_x1, curr_x1)
                overlap = max(0, overlap_end - overlap_start)
                
                # Calculate widths
                prev_width = prev_x1 - prev_x0
                curr_width = curr_x1 - curr_x0
                min_width = min(prev_width, curr_width) if min(prev_width, curr_width) > 0 else 1
                
                # Require at least 30% overlap of the narrower block
                # This allows for slight indentation but catches different columns
                overlap_ratio = overlap / min_width
                
                if overlap_ratio < 0.30:
                    should_merge = False
                    logging.debug(f"Column break detected: overlap {overlap_ratio:.1%} between '{prev['text'][:20]}...' and '{curr['text'][:20]}...'")
            
            if should_merge:
                current_group.append(curr)
            else:
                merged_groups.append(current_group)
                current_group = [curr]
        
        # Don't forget the last group
        if current_group:
            merged_groups.append(current_group)
        
        logging.info(f"Cross-block merge: {len(text_blocks)} blocks → {len(merged_groups)} paragraph groups")
        
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
    
    def _normalize_text_for_pdf(self, text: str) -> str:
        """
        Normalize text for proper PDF rendering.
        
        Handles:
        - Unicode ligatures (fi, fl, ff, ffi, ffl) → individual chars
        - Typographic quotes → standard quotes
        - Special dashes → standard dashes
        - Other problematic Unicode characters
        
        Note: Some ligatures may still be created by the PDF renderer
        when using insert_htmlbox. This is generally acceptable as they
        display correctly in most PDF viewers.
        """
        if not text:
            return text
        
        # Ligature replacements (these cause rendering issues in base PDF fonts)
        ligature_map = {
            '\ufb00': 'ff',   # ff ligature
            '\ufb01': 'fi',   # fi ligature
            '\ufb02': 'fl',   # fl ligature
            '\ufb03': 'ffi',  # ffi ligature
            '\ufb04': 'ffl',  # ffl ligature
            '\ufb05': 'ft',   # ft ligature (rare)
            '\ufb06': 'st',   # st ligature (rare)
        }
        
        # Typographic quotes → standard (optional - keeps readability)
        quote_map = {
            '\u201c': '"',    # Left double quotation mark "
            '\u201d': '"',    # Right double quotation mark "
            '\u2018': "'",    # Left single quotation mark '
            '\u2019': "'",    # Right single quotation mark ' (also apostrophe)
            '\u00ab': '"',    # Left guillemet «
            '\u00bb': '"',    # Right guillemet »
            '\u201e': '"',    # Double low quotation mark „
            '\u201a': "'",    # Single low quotation mark ‚
        }
        
        # Dashes and spaces
        dash_map = {
            '\u2013': '-',    # En-dash –
            '\u2014': '-',    # Em-dash —
            '\u2012': '-',    # Figure dash
            '\u2015': '-',    # Horizontal bar
            '\u00a0': ' ',    # Non-breaking space
            '\u2003': ' ',    # Em space
            '\u2002': ' ',    # En space
            '\u2009': ' ',    # Thin space
        }
        
        # Apply all replacements
        for old, new in ligature_map.items():
            text = text.replace(old, new)
        
        for old, new in quote_map.items():
            text = text.replace(old, new)
        
        for old, new in dash_map.items():
            text = text.replace(old, new)
        
        return text
    
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
        
        # Normalize text for PDF rendering (handle ligatures, special chars)
        translated_text = self._normalize_text_for_pdf(translated_text)
        
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
                char_width_factor = 0.6  # Monospace is wider
            elif line_data.get('is_serif', False):
                font_family = 'Georgia, "Times New Roman", Times, serif'
                pdf_font = "tiro"  # Times Roman
                char_width_factor = 0.5
            else:
                font_family = '-apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif'
                pdf_font = "helv"  # Helvetica
                char_width_factor = 0.52
        else:
            font_family = 'Helvetica, Arial, sans-serif'
            pdf_font = "helv"
            char_width_factor = 0.52
        
        # Character width estimation
        avg_char_width = target_font_size * char_width_factor
        estimated_width = len(translated_text) * avg_char_width
        
        # Determine if we need text wrapping
        needs_wrapping = estimated_width > bbox_width * 1.5
        
        # IMPORTANT: Keep original font size - do NOT scale
        # The original size is preserved to maintain document appearance
        # If text doesn't fit, we use wrapping instead of shrinking
        if estimated_width > bbox_width and not needs_wrapping:
            # Allow wrapping for long text rather than shrinking
            needs_wrapping = True
        
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
                font-variant-ligatures: none;
                -webkit-font-variant-ligatures: none;
                font-feature-settings: "liga" 0, "clig" 0;
            }}"""
            
            page.insert_htmlbox(merged_bbox, translated_text, css=css, rotate=rotation)
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
        """Get PaddleOCR language code from language name."""
        return PADDLEOCR_LANGUAGES.get(language_name, "en")
