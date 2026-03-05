"""
RapidDoc integration — document parsing engine for structured text extraction.

Uses RapidDoc (layout analysis + OCR + table recognition) to extract
structured Markdown from PDF pages, preserving:
- Headings (# / ## / ### detected via layout analysis)
- Tables (HTML tables with proper structure)
- Reading order (restored by PP-DocLayoutV2)
- Paragraphs (properly segmented and ordered)

Unlike plain RapidOCR (which returns flat text), RapidDoc provides
document-level understanding by combining:
- PP-DocLayoutV2: Layout element detection (title, text, table, figure, etc.)
- RapidOCR: Text recognition within each layout region
- Table models: UNET + SLANET_PLUS for wired/wireless table recognition
- Reading order: Algorithm-based reading order restoration

Usage:
    from app.core.rapid_doc_engine import RapidDocEngine

    engine = RapidDocEngine()
    if engine.is_available():
        markdown = engine.extract_page_markdown(pdf_bytes, page_num=0)
"""
import os
import io
import logging
import time
from typing import Optional, Tuple, List, Dict, Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Environment configuration (must be set BEFORE importing rapid_doc)
# ---------------------------------------------------------------------------
os.environ.setdefault('MINERU_DEVICE_MODE', 'cpu')

# ---------------------------------------------------------------------------
# Import RapidDoc components
# ---------------------------------------------------------------------------
RAPIDDOC_AVAILABLE = False
_import_error_msg = ""

try:
    from rapid_doc.cli.common import convert_pdf_bytes_to_bytes_by_pypdfium2
    from rapid_doc.backend.pipeline.pipeline_analyze import (
        doc_analyze as pipeline_doc_analyze,
    )
    from rapid_doc.backend.pipeline.pipeline_middle_json_mkcontent import (
        union_make as pipeline_union_make,
    )
    from rapid_doc.backend.pipeline.model_json_to_middle_json import (
        result_to_middle_json as pipeline_result_to_middle_json,
    )
    from rapid_doc.data.data_reader_writer import FileBasedDataWriter
    from rapid_doc.utils.enum_class import MakeMode
    from rapidocr import LangRec, OCRVersion, ModelType as OCRModelType
    RAPIDDOC_AVAILABLE = True
except ImportError as e:
    _import_error_msg = str(e)
    logger.info(f"RapidDoc not available: {e}")
except Exception as e:
    _import_error_msg = str(e)
    logger.warning(f"RapidDoc import error: {e}")


# ---------------------------------------------------------------------------
# OCR configuration for RapidDoc
# ---------------------------------------------------------------------------

def _build_rapiddoc_ocr_config() -> dict:
    """
    Build optimized OCR config for RapidDoc.

    Mirrors our tuned RapidOCR settings:
    - LATIN recognition (PP-OCRv4 SERVER) for English/Italian text
    - Box threshold 0.6 to filter weak detections from watermarks
    - CH v5 detection (best general-purpose text detection)

    Note: RapidDoc uses OpenVINO internally for OCR when available,
    which is faster than ONNX Runtime for CPU inference.
    """
    if not RAPIDDOC_AVAILABLE:
        return {}
    return {
        # LATIN recognition for English/Italian documents
        "Rec.lang_type": LangRec.LATIN,
        "Rec.ocr_version": OCRVersion.PPOCRV4,
        "Rec.model_type": OCRModelType.SERVER,
        # Detection: PP-OCRv5 CH mobile (best general-purpose)
        "Det.box_thresh": 0.6,
    }


# ---------------------------------------------------------------------------
# Temporary image output directory
# ---------------------------------------------------------------------------
_IMAGE_OUTPUT_DIR = "/tmp/rapiddoc_images"


class RapidDocEngine:
    """
    Document parsing engine using RapidDoc.

    Provides structured Markdown extraction from PDF pages, with:
    - Heading detection (PP-DocLayoutV2 layout analysis)
    - Table recognition (UNET + SLANET_PLUS)
    - Reading order restoration
    - Proper paragraph segmentation

    Singleton: one shared instance. Models are downloaded
    automatically on first use (~250 MB total).
    """

    _instance: Optional["RapidDocEngine"] = None
    _initialized: bool = False
    _available: Optional[bool] = None

    def __new__(cls) -> "RapidDocEngine":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._ocr_config = _build_rapiddoc_ocr_config()
        # Ensure temp directory exists
        os.makedirs(_IMAGE_OUTPUT_DIR, exist_ok=True)
        logger.info("RapidDocEngine initialized")

    def is_available(self) -> bool:
        """Check if RapidDoc is available and functional."""
        if self._available is not None:
            return self._available

        if not RAPIDDOC_AVAILABLE:
            self._available = False
            logger.info(f"RapidDoc not available: {_import_error_msg}")
            return False

        # Verify that the pipeline can be imported (lazy model init)
        try:
            # The actual model download happens on first analyze call
            self._available = True
            logger.info("RapidDoc engine available")
        except Exception as e:
            self._available = False
            logger.warning(f"RapidDoc availability check failed: {e}")

        return self._available

    def extract_page_markdown(
        self,
        pdf_bytes: bytes,
        page_num: int = 0,
        parse_method: str = 'auto',
        table_enable: bool = True,
        formula_enable: bool = False,
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Extract structured Markdown from a single PDF page.

        Args:
            pdf_bytes: Full PDF file as bytes
            page_num: 0-based page number to extract
            parse_method: 'auto', 'txt', or 'ocr'
                - 'auto': tries text extraction first, falls back to OCR
                - 'txt': text-only extraction (no OCR)
                - 'ocr': force OCR on all regions
            table_enable: Whether to recognize tables
            formula_enable: Whether to recognize formulas (slower)

        Returns:
            Tuple of (markdown_string, metadata_dict) where metadata contains:
                - 'language': detected language
                - 'ocr_enabled': whether OCR was used
                - 'elapsed': processing time in seconds
                - 'num_elements': number of content elements detected
        """
        if not self.is_available():
            raise RuntimeError("RapidDoc is not available")

        t0 = time.time()

        try:
            # Extract single page as a new PDF
            single_page_pdf = convert_pdf_bytes_to_bytes_by_pypdfium2(
                pdf_bytes, page_num, page_num
            )

            # Run the full pipeline
            infer_results, all_image_lists, all_page_dicts, lang_list, ocr_enabled_list = (
                pipeline_doc_analyze(
                    [single_page_pdf],
                    parse_method=parse_method,
                    formula_enable=formula_enable,
                    table_enable=table_enable,
                    ocr_config=self._ocr_config,
                )
            )

            # Convert to middle JSON
            model_list = infer_results[0]
            images_list = all_image_lists[0]
            pdf_dict = all_page_dicts[0]
            _lang = lang_list[0]
            _ocr_enable = ocr_enabled_list[0]

            image_writer = FileBasedDataWriter(_IMAGE_OUTPUT_DIR)

            middle_json = pipeline_result_to_middle_json(
                model_list, images_list, pdf_dict, image_writer,
                _lang, _ocr_enable, formula_enable,
                ocr_config=self._ocr_config,
            )

            pdf_info = middle_json["pdf_info"]

            # Generate Markdown
            md_content = pipeline_union_make(pdf_info, MakeMode.MM_MD, "images")

            elapsed = time.time() - t0

            metadata = {
                'language': _lang,
                'ocr_enabled': _ocr_enable,
                'elapsed': elapsed,
                'num_elements': self._count_elements(pdf_info),
                'block_bboxes': self._extract_block_bboxes(pdf_info),
                'page_size': self._extract_page_size(pdf_info),
            }

            logger.info(
                f"RapidDoc page {page_num + 1}: {len(md_content)} chars, "
                f"{metadata['num_elements']} elements, "
                f"lang={_lang}, ocr={_ocr_enable}, {elapsed:.1f}s"
            )

            return md_content, metadata

        except Exception as e:
            elapsed = time.time() - t0
            logger.error(f"RapidDoc extraction failed for page {page_num + 1}: {e}")
            raise

    def extract_page_text(
        self,
        pdf_bytes: bytes,
        page_num: int = 0,
        parse_method: str = 'auto',
    ) -> str:
        """
        Extract plain text from a single PDF page via RapidDoc.

        This strips Markdown formatting and returns clean text,
        useful as a fallback or for text extraction (not translation).

        Args:
            pdf_bytes: Full PDF file as bytes
            page_num: 0-based page number
            parse_method: 'auto', 'txt', or 'ocr'

        Returns:
            Plain text string (Markdown markers stripped)
        """
        md_content, _ = self.extract_page_markdown(
            pdf_bytes, page_num, parse_method,
            table_enable=False, formula_enable=False,
        )
        return self._strip_markdown(md_content)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _count_elements(pdf_info) -> int:
        """Count total content elements across all pages.
        
        pdf_info is a list of page dicts, each with keys like
        'preproc_blocks', 'para_blocks', 'discarded_blocks', 'page_size'.
        """
        count = 0
        pages = pdf_info if isinstance(pdf_info, list) else pdf_info.get("pages", [])
        for page_info in pages:
            if not isinstance(page_info, dict):
                continue
            for block in page_info.get("para_blocks", []):
                count += 1
            for block in page_info.get("preproc_blocks", []):
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        if span.get("type") not in ("discarded",):
                            count += 1
        return count

    @staticmethod
    def _strip_markdown(md_text: str) -> str:
        """
        Strip Markdown formatting markers, returning plain text.

        Handles:
        - Headings (# / ## / ###)
        - Bold (**text**)
        - Italic (*text*)
        - Links [text](url)
        - Images ![alt](url)
        - HTML tags
        """
        import re
        text = md_text

        # Remove images
        text = re.sub(r'!\[.*?\]\(.*?\)', '', text)

        # Convert links to just text
        text = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', text)

        # Remove heading markers
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)

        # Remove bold/italic markers
        text = re.sub(r'\*{1,3}(.*?)\*{1,3}', r'\1', text)

        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)

        # Normalize whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)

        return text.strip()

    @staticmethod
    def _extract_block_bboxes(pdf_info) -> List[Dict[str, Any]]:
        """
        Extract bounding boxes and types from layout blocks.

        Returns a list of dicts, each with 'bbox' (x0,y0,x1,y1) and 'type'.
        Used for multi-column layout detection.
        """
        blocks = []
        pages = pdf_info if isinstance(pdf_info, list) else pdf_info.get("pages", [])
        for page_info in pages:
            if not isinstance(page_info, dict):
                continue
            for block in page_info.get("para_blocks", []):
                if isinstance(block, dict) and 'bbox' in block:
                    blocks.append({
                        'bbox': block['bbox'],
                        'type': block.get('type', 'text'),
                    })
        return blocks

    @staticmethod
    def _extract_page_size(pdf_info) -> Optional[Tuple[float, float]]:
        """
        Extract page dimensions (width, height) from pdf_info.
        """
        pages = pdf_info if isinstance(pdf_info, list) else pdf_info.get("pages", [])
        for page_info in pages:
            if isinstance(page_info, dict) and 'page_size' in page_info:
                ps = page_info['page_size']
                if isinstance(ps, (list, tuple)) and len(ps) >= 2:
                    return (float(ps[0]), float(ps[1]))
        return None

    @staticmethod
    def detect_column_count(
        block_bboxes: List[Dict[str, Any]],
        page_size: Optional[Tuple[float, float]] = None,
    ) -> Tuple[int, List[Tuple[float, float]]]:
        """
        Detect multi-column layout using a two-strategy approach:

        1. **Gap-based**: project blocks onto the x-axis, find contiguous
           covered regions separated by gaps ≥ 2 % of page width.
           Works for clearly separated columns (e.g. bilingual contracts).

        2. **Center-x clustering** (fallback): sort the center-x values of
           all content blocks and look for natural breaks ≥ 8 % of page
           width between consecutive values.
           Works for touching/adjacent columns (e.g. newspapers).

        Args:
            block_bboxes: List of dicts with 'bbox' [x0,y0,x1,y1] and 'type'
            page_size: Optional (width, height) of the page

        Returns:
            (n_columns, col_x_ranges) where col_x_ranges is a list of
            (x0, x1) tuples in page coordinates.
            If n_columns == 1, col_x_ranges is empty.
        """
        if not block_bboxes or len(block_bboxes) < 3:
            return 1, []

        # Filter to content blocks — skip images and discarded
        CONTENT_TYPES = ('text', 'title', 'paragraph_title', 'list')
        content_blocks = [
            b for b in block_bboxes
            if b.get('type') in CONTENT_TYPES
        ]
        if len(content_blocks) < 3:
            return 1, []

        # Get page width
        if page_size:
            page_width = page_size[0]
        else:
            page_width = max(b['bbox'][2] for b in content_blocks) * 1.1
        if page_width < 100:
            return 1, []

        # Collect x-intervals, skipping blocks that span >70 % of page
        intervals = []
        for b in content_blocks:
            x0, _, x1, _ = b['bbox']
            if (x1 - x0) < page_width * 0.7:
                intervals.append((x0, x1))

        if len(intervals) < 3:
            return 1, []

        BIN = 5.0  # bin resolution in pt

        # ── Strategy 1: gap-based detection ──
        n_bins = int(page_width / BIN) + 2
        hits = [0] * n_bins
        for x0, x1 in intervals:
            i0 = max(0, int(x0 / BIN))
            i1 = min(n_bins - 1, int(x1 / BIN))
            for i in range(i0, i1 + 1):
                hits[i] += 1

        min_gap_width = max(page_width * 0.02, 15.0)
        min_gap_bins = max(2, int(min_gap_width / BIN))

        columns_bins: List[Tuple[int, int]] = []
        col_start: Optional[int] = None
        gap_len = 0

        for i in range(n_bins):
            if hits[i] > 0:
                if col_start is None:
                    col_start = i
                gap_len = 0
            else:
                gap_len += 1
                if col_start is not None and gap_len >= min_gap_bins:
                    col_end = i - gap_len
                    columns_bins.append((col_start, col_end))
                    col_start = None

        if col_start is not None:
            col_end = col_start
            for i in range(n_bins - 1, col_start - 1, -1):
                if hits[i] > 0:
                    col_end = i
                    break
            columns_bins.append((col_start, col_end))

        col_x_ranges = [(s * BIN, (e + 1) * BIN) for s, e in columns_bins]

        valid_gap: List[Tuple[float, float]] = []
        for cx0, cx1 in col_x_ranges:
            n_blk = sum(
                1 for x0, x1 in intervals
                if cx0 - BIN <= (x0 + x1) / 2 <= cx1 + BIN
            )
            if n_blk >= 2:
                valid_gap.append((cx0, cx1))

        if 2 <= len(valid_gap) <= 6:
            return len(valid_gap), valid_gap

        # ── Strategy 2: center-x clustering (fallback for touching cols) ──
        # Sort blocks by center-x, then find natural breaks
        block_data = sorted(
            ((x0 + x1) / 2, x0, x1) for x0, x1 in intervals
        )
        sorted_cx = [d[0] for d in block_data]

        min_cx_gap = max(page_width * 0.08, 50.0)
        breaks = [
            i for i in range(1, len(sorted_cx))
            if sorted_cx[i] - sorted_cx[i - 1] > min_cx_gap
        ]

        n_clusters = len(breaks) + 1
        if n_clusters < 2 or n_clusters > 6:
            return 1, []

        # Build clusters and derive x-ranges
        bounds = [0] + breaks + [len(block_data)]
        valid_cx: List[Tuple[float, float]] = []
        for ci in range(n_clusters):
            cluster = block_data[bounds[ci]:bounds[ci + 1]]
            if len(cluster) >= 2:
                cx0 = min(d[1] for d in cluster)
                cx1 = max(d[2] for d in cluster)
                if (cx1 - cx0) >= page_width * 0.08:
                    valid_cx.append((cx0, cx1))

        # Reject if column ranges overlap significantly — a sign of
        # mixed-width blocks in a single-column layout, not real columns
        for i in range(len(valid_cx) - 1):
            _, r1 = valid_cx[i]
            l2, _ = valid_cx[i + 1]
            overlap = r1 - l2
            min_w = min(
                valid_cx[i][1] - valid_cx[i][0],
                valid_cx[i + 1][1] - valid_cx[i + 1][0],
            )
            if overlap > min_w * 0.15:  # >15 % overlap → not real columns
                return 1, []

        if 2 <= len(valid_cx) <= 6:
            return len(valid_cx), valid_cx

        return 1, []


def check_rapiddoc_status() -> Tuple[bool, str]:
    """
    Check if RapidDoc is available and return status message.

    Returns:
        Tuple of (available: bool, status_message: str)
    """
    if not RAPIDDOC_AVAILABLE:
        return False, f"RapidDoc not installed: {_import_error_msg}"

    try:
        engine = RapidDocEngine()
        if engine.is_available():
            return True, "RapidDoc available (PP-DocLayoutV2 + RapidOCR + Table recognition)"
        return False, "RapidDoc installed but not functional"
    except Exception as e:
        return False, f"RapidDoc error: {e}"
