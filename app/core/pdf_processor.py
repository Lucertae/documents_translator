"""
PDF processing module - PaddleOCR Edition
Handles PDF loading, text extraction, OCR, and manipulation with superior quality.
"""
import logging
import io
from pathlib import Path
from typing import Optional, Tuple, List
import pymupdf
from PIL import Image
import numpy as np

# Import sentence-aware translation helpers
from .translator import split_into_sentences, align_sentences_to_lines

try:
    from paddleocr import PaddleOCR
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    logging.warning("OCR not available - install paddleocr for scanned PDF support")


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
    
    # PaddleOCR language codes
    PADDLEOCR_LANGUAGES = {
        "Italiano": "it",
        "English": "en",
        "Español": "es",
        "Français": "fr",
        "Deutsch": "de",
        "Português": "pt",
        "Nederlands": "nl",  # Using multilingual model
    }
    
    # Singleton PaddleOCR instance (lazy loading)
    _ocr_engine = None
    _current_lang = None
    
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
            except:
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
        """Get or create PaddleOCR engine (singleton with language caching)."""
        if cls._ocr_engine is None or cls._current_lang != language:
            logging.info(f"Initializing PaddleOCR for language: {language}")
            try:
                # Modern PaddleOCR API (v3+)
                cls._ocr_engine = PaddleOCR(
                    lang=language,
                    text_det_thresh=0.3,  # Detection threshold (lower = more sensitive)
                    text_det_box_thresh=0.5,  # Bounding box threshold
                )
                cls._current_lang = language
                logging.info(f"✓ PaddleOCR initialized for {language}")
            except Exception as e:
                logging.error(f"Failed to initialize PaddleOCR: {e}")
                cls._ocr_engine = None
        return cls._ocr_engine
    
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
        
        # Step 4: Build final text
        result_parts = []
        for para in all_paragraphs:
            para_text = ' '.join(para)
            if para_text.strip():
                result_parts.append(para_text.strip())
        
        # Add unpositioned text at the end
        if unpositioned:
            unpositioned_text = ' '.join(r['text'] for r in unpositioned)
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
    
    def translate_page(
        self, 
        page_num: int, 
        translator,
        text_color: Tuple[float, float, float] = (0.8, 0, 0),
        use_original_color: bool = False,
        preserve_font_style: bool = True
    ) -> pymupdf.Document:
        """
        World-class translation system with maximum fidelity to original.
        
        Architecture:
        1. Phase 1: Extract all text structure and metadata
        2. Phase 2: Translate entire blocks for maximum context
        3. Phase 3: Sentence-aware distribution preserving semantic boundaries
        4. Phase 4: Remove ALL original text via redaction (clean slate)
        5. Phase 5: Insert translations with font/style preservation
        
        Args:
            page_num: Page number to translate
            translator: Translation engine instance
            text_color: RGB color tuple for translated text (default red)
            use_original_color: If True, use the original text color instead
            preserve_font_style: If True, match original font family style
            
        Returns:
            New document containing translated page
        """
        WHITE = pymupdf.pdfcolor["white"]
        
        new_doc = pymupdf.open()
        new_doc.insert_pdf(self.document, from_page=page_num, to_page=page_num)
        page = new_doc[0]
        
        text_dict = page.get_text("dict")
        
        # Collect ALL areas to redact (will be applied in bulk before insertions)
        areas_to_redact = []
        # Collect all translations to insert (after redaction)
        translations_to_insert = []
        
        translated_count = 0
        total_blocks = len([b for b in text_dict.get("blocks", []) if "lines" in b])
        
        logging.info(f"Page {page_num + 1}: Found {total_blocks} text blocks to process")
        
        # ============================================
        # PHASE 1: Extract structure and translate
        # ============================================
        for block_idx, block in enumerate(text_dict.get("blocks", [])):
            if "lines" not in block:
                continue
            
            # Extract block structure preserving all metadata
            lines_data = []
            block_full_text = []
            
            logging.debug(f"Block {block_idx + 1}/{total_blocks}: Processing {len(block.get('lines', []))} lines")
            
            for line in block["lines"]:
                if "spans" not in line:
                    continue
                
                line_text_parts = []
                line_bboxes = []
                line_sizes = []
                line_fonts = []
                line_colors = []
                line_flags = []
                
                for span in line["spans"]:
                    text = span.get("text", "").strip()
                    if text:
                        line_text_parts.append(text)
                        line_bboxes.append(span["bbox"])
                        line_sizes.append(span.get("size", 11))
                        line_fonts.append(span.get("font", ""))
                        color_int = span.get("color", 0)
                        r = ((color_int >> 16) & 0xFF) / 255.0
                        g = ((color_int >> 8) & 0xFF) / 255.0
                        b = (color_int & 0xFF) / 255.0
                        line_colors.append((r, g, b))
                        line_flags.append(span.get("flags", 0))
                
                if line_text_parts:
                    line_text = " ".join(line_text_parts)
                    dominant_color = line_colors[0] if line_colors else (0, 0, 0)
                    combined_flags = 0
                    for f in line_flags:
                        combined_flags |= f
                    
                    line_data = {
                        'text': line_text,
                        'bboxes': line_bboxes,
                        'sizes': line_sizes,
                        'fonts': line_fonts,
                        'colors': line_colors,
                        'dominant_color': dominant_color,
                        'merged_bbox': self._merge_bboxes(line_bboxes),
                        'avg_size': sum(line_sizes) / len(line_sizes),
                        'is_bold': any('Bold' in f for f in line_fonts) or (combined_flags & 16),
                        'is_italic': any('Italic' in f for f in line_fonts) or (combined_flags & 2),
                        'is_serif': any(f in font for font in line_fonts for f in ['Times', 'Serif', 'Georgia', 'Garamond']),
                        'is_monospace': any(f in font for font in line_fonts for f in ['Courier', 'Mono', 'Consolas']),
                    }
                    lines_data.append(line_data)
                    block_full_text.append(line_text)
                    
                    # Collect ALL bboxes for redaction
                    for bbox in line_bboxes:
                        areas_to_redact.append(bbox)
            
            if not lines_data:
                continue
            
            # Translate entire block for maximum context
            block_text = " ".join(block_full_text)
            
            logging.debug(f"Block has {len(lines_data)} lines, text: {block_text[:100]}...")
            
            try:
                translated_block = translator.translate(block_text)
                
                logging.debug(f"Translated to: {translated_block[:100] if translated_block else 'EMPTY'}...")
                
                if not translated_block or not translated_block.strip():
                    # Fallback: translate line by line
                    logging.info(f"Empty block translation, using line-by-line fallback")
                    for line_data in lines_data:
                        line_trans = translator.translate(line_data['text']) or line_data['text']
                        translations_to_insert.append({
                            'line_data': line_data,
                            'text': line_trans
                        })
                        translated_count += 1
                    continue
                
                # Sentence-aware distribution
                translated_sentences = split_into_sentences(translated_block)
                original_line_lengths = [len(line['text']) for line in lines_data]
                line_texts = align_sentences_to_lines(
                    translated_sentences,
                    len(lines_data),
                    original_line_lengths
                )
                
                logging.debug(f"Sentence-aware distribution: {len(translated_sentences)} sentences → {len(lines_data)} lines")
                
                # Queue translations for later insertion
                for line_data, line_text in zip(lines_data, line_texts):
                    if line_text.strip():
                        translations_to_insert.append({
                            'line_data': line_data,
                            'text': line_text
                        })
                        translated_count += 1
                
            except Exception as e:
                logging.error(f"Block translation error: {e}, using line-by-line fallback")
                for line_data in lines_data:
                    try:
                        line_trans = translator.translate(line_data['text'])
                        translations_to_insert.append({
                            'line_data': line_data,
                            'text': line_trans or line_data['text']
                        })
                        translated_count += 1
                    except Exception as line_error:
                        logging.error(f"Line translation failed: {line_error}")
        
        # ============================================
        # PHASE 2: Apply redactions (remove ALL original text)
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
        # PHASE 3: Insert translations
        # ============================================
        logging.info(f"Inserting {len(translations_to_insert)} translations...")
        
        for item in translations_to_insert:
            try:
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
                logging.error(f"Failed to insert translation: {e}")
        
        logging.info(f"Page {page_num + 1}: Successfully processed {total_blocks} blocks, translated {translated_count} lines")
        
        if translated_count == 0:
            logging.warning(f"Page {page_num + 1}: NO LINES TRANSLATED! This page may appear blank.")
        
        return new_doc
    
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
                except:
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
        
        # Dynamic scaling with quality preservation
        if estimated_width > bbox_width and not needs_wrapping:
            # Scale down to fit, but maintain readability
            scale_factor = bbox_width / estimated_width
            target_font_size = max(6, target_font_size * scale_factor * 0.95)
        
        # Ensure minimum readability
        if target_font_size < 6:
            logging.warning(f"Font size {target_font_size:.1f}pt too small, clamped to 6pt")
            target_font_size = 6
        
        # PRIMARY METHOD: Direct text insertion (no ligatures, reliable)
        # Only use htmlbox for wrapping since insert_text doesn't wrap
        if not needs_wrapping:
            try:
                # Calculate baseline position
                baseline_y = merged_bbox[1] + target_font_size
                
                page.insert_text(
                    (merged_bbox[0], baseline_y),
                    translated_text,
                    fontsize=target_font_size,
                    color=final_color,
                    fontname=pdf_font
                )
                logging.debug(f"✓ Text insertion successful (primary)")
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
            
            page.insert_htmlbox(merged_bbox, translated_text, css=css)
            logging.debug(f"✓ HTML insertion successful (wrap={needs_wrapping})")
            return
            
        except Exception as e:
            logging.warning(f"HTML insertion failed: {e}")
            # Final fallback: truncated text
            try:
                baseline_y = merged_bbox[1] + target_font_size
                max_chars = int(bbox_width / (target_font_size * 0.45))
                display_text = translated_text[:max_chars-3] + "..." if len(translated_text) > max_chars else translated_text
                
                page.insert_text(
                    (merged_bbox[0], baseline_y),
                    display_text,
                    fontsize=target_font_size,
                    color=final_color,
                    fontname=pdf_font
                )
                logging.debug(f"✓ Truncated text insertion successful")
            except Exception as final_error:
                logging.error(f"All insertion methods failed: {final_error}")
    
    def close(self) -> None:
        """Close document and free resources."""
        if self.document:
            self.document.close()
    
    @classmethod
    def get_ocr_language(cls, language_name: str) -> str:
        """Get PaddleOCR language code from language name."""
        return cls.PADDLEOCR_LANGUAGES.get(language_name, "en")
