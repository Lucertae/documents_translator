"""
Configuration constants for PDF processing and OCR.

This module centralizes all tunable parameters and thresholds
to improve maintainability and allow easy experimentation.

PaddleOCR Configuration (v3.3.3 with PP-OCRv5):
- Requires PaddlePaddle 3.2.x (3.3.0 has ONEDNN bug on CPU)
- PP-OCRv5 provides best accuracy for scanned documents
- Supports 80+ languages: en, it, fr, de, es, pt, zh, ja, ko, ar, ru, etc.
- use_textline_orientation=True enables automatic text orientation detection
"""
from dataclasses import dataclass
from typing import Dict, Tuple


# ============================================
# OCR Configuration
# ============================================

@dataclass(frozen=True)
class OCRConfig:
    """Configuration for PaddleOCR engine (PP-OCRv5).
    
    Recommended versions:
    - PaddlePaddle: 3.2.x (3.3.0 has ONEDNN bug on CPU)
    - PaddleOCR: 3.3.3 with PP-OCRv5 models
    """
    
    # Recognition thresholds  
    min_confidence: float = 0.5  # Minimum OCR confidence to accept text
    
    # Image preprocessing
    ocr_scale: float = 2.0  # Scale factor for page-to-image conversion (2.0 = 144 DPI)
    ocr_scale_fallback: float = 1.5  # Fallback scale if memory issues
    
    # Column detection
    column_gap_ratio: float = 0.15  # Gap > 15% page width = column boundary
    min_column_gap_pts: float = 30  # Minimum gap in points for column detection
    
    # Line grouping
    line_height_factor: float = 0.6  # Lines within this factor of height are same line
    
    # Paragraph detection
    para_threshold_factor: float = 1.5  # Gap > 1.5x line height = new paragraph


# ============================================
# Text Quality Assessment
# ============================================

@dataclass(frozen=True)
class TextQualityConfig:
    """Configuration for text quality assessment."""
    
    # Quality thresholds
    min_acceptable_quality: float = 0.5  # Below this, use OCR
    min_word_count: int = 15  # Below this word count, consider OCR
    
    # Quality penalties
    special_char_threshold: float = 0.15  # High special chars ratio
    single_char_word_threshold: float = 0.3  # Fragmented text
    vowel_ratio_min: float = 0.1  # Too few vowels = encoding issue
    
    # Word length bounds
    min_avg_word_length: float = 2.5
    max_avg_word_length: float = 15.0


# ============================================
# Scanned Page Detection
# ============================================

@dataclass(frozen=True)
class ScanDetectionConfig:
    """Configuration for detecting scanned pages."""
    
    # Image coverage thresholds
    large_image_coverage: float = 0.5  # Image covering 50%+ = large
    high_image_coverage: float = 0.7  # 70%+ coverage with few words
    full_page_image_coverage: float = 0.9  # 90%+ = definitely scanned
    
    # Word count thresholds
    min_words_large_image: int = 10  # With large image, need >10 words for native
    min_words_high_coverage: int = 20  # With 70% coverage, need >20 words
    min_chars_no_text: int = 5  # Below this = no text at all


# ============================================
# Paragraph Detection
# ============================================

@dataclass(frozen=True)
class ParagraphConfig:
    """Configuration for paragraph boundary detection."""
    
    # Font size change threshold (20% = heading detection)
    size_change_ratio: float = 1.2
    
    # Vertical gap threshold (1.5x font = paragraph break)
    vertical_gap_factor: float = 1.5
    
    # Title detection
    max_title_chars: int = 50
    max_title_words: int = 6
    
    # Cross-block merge thresholds
    cross_block_size_ratio: float = 1.15  # 15% size change = new para
    cross_block_gap_factor: float = 2.0  # 2x font size gap = new para


# ============================================
# Font Family Detection
# ============================================

MONO_FONT_PATTERNS = [
    'Courier', 'Mono', 'Consolas', 'Monaco', 'Menlo', 'Source Code'
]

SERIF_FONT_PATTERNS = [
    'Times', 'Serif', 'Georgia', 'Garamond', 'Palatino', 'Cambria'
]


# ============================================
# Language Mappings
# ============================================

# PaddleOCR language codes
PADDLEOCR_LANGUAGES: Dict[str, str] = {
    "Italiano": "it",
    "English": "en",
    "Español": "es",
    "Français": "fr",
    "Deutsch": "de",
    "Português": "pt",
    "Nederlands": "nl",
}

# OPUS-MT model mapping
OPUS_MODEL_MAP: Dict[Tuple[str, str], str] = {
    ("en", "it"): "Helsinki-NLP/opus-mt-en-it",
    ("it", "en"): "Helsinki-NLP/opus-mt-it-en",
    ("en", "es"): "Helsinki-NLP/opus-mt-en-es",
    ("es", "en"): "Helsinki-NLP/opus-mt-es-en",
    ("en", "fr"): "Helsinki-NLP/opus-mt-en-fr",
    ("fr", "en"): "Helsinki-NLP/opus-mt-fr-en",
    ("en", "de"): "Helsinki-NLP/opus-mt-en-de",
    ("de", "en"): "Helsinki-NLP/opus-mt-de-en",
    ("en", "pt"): "Helsinki-NLP/opus-mt-en-roa",
    ("pt", "en"): "Helsinki-NLP/opus-mt-roa-en",
    ("en", "nl"): "Helsinki-NLP/opus-mt-en-nl",
    ("nl", "en"): "Helsinki-NLP/opus-mt-nl-en",
}

SUPPORTED_LANGUAGES: Dict[str, str] = {
    "Italiano": "it",
    "English": "en",
    "Español": "es",
    "Français": "fr",
    "Deutsch": "de",
    "Português": "pt",
    "Nederlands": "nl",
}


# ============================================
# Text Normalization Maps
# ============================================

# Ligature replacements for PDF rendering
LIGATURE_MAP: Dict[str, str] = {
    '\ufb00': 'ff',
    '\ufb01': 'fi',
    '\ufb02': 'fl',
    '\ufb03': 'ffi',
    '\ufb04': 'ffl',
    '\ufb05': 'ft',
    '\ufb06': 'st',
}

# Typographic quotes to standard
QUOTE_MAP: Dict[str, str] = {
    '\u201c': '"',  # Left double "
    '\u201d': '"',  # Right double "
    '\u2018': "'",  # Left single '
    '\u2019': "'",  # Right single '
    '\u00ab': '"',  # Left guillemet «
    '\u00bb': '"',  # Right guillemet »
    '\u201e': '"',  # Low double „
    '\u201a': "'",  # Low single ‚
}

# Dashes and spaces to standard
DASH_SPACE_MAP: Dict[str, str] = {
    '\u2013': '-',  # En-dash
    '\u2014': '-',  # Em-dash
    '\u2012': '-',  # Figure dash
    '\u2015': '-',  # Horizontal bar
    '\u2212': '-',  # Minus sign
    '\u2026': '...',  # Ellipsis
    '\u00a0': ' ',  # Non-breaking space
    '\u2003': ' ',  # Em space
    '\u2002': ' ',  # En space
    '\u2009': ' ',  # Thin space
}


# ============================================
# Abbreviations (for sentence splitting)
# ============================================

ABBREVIATIONS = {
    # English
    'mr', 'mrs', 'ms', 'dr', 'prof', 'sr', 'jr', 'vs', 'etc', 'inc', 'ltd',
    'fig', 'vol', 'no', 'pp', 'ed', 'eds', 'rev', 'col', 'gen', 'gov',
    'hon', 'lt', 'sgt', 'rep', 'sen', 'st', 'co', 'corp', 'dept', 'div',
    # Italian
    'dott', 'sig', 'sig.ra', 'prof', 'avv', 'ing', 'arch', 'geom',
    # German
    'nr', 'str', 'tel', 'bzw',
    # French
    'av', 'bd', 'env', 'm', 'mme', 'mlle',
}


# ============================================
# Default Instances
# ============================================

DEFAULT_OCR_CONFIG = OCRConfig()
DEFAULT_TEXT_QUALITY_CONFIG = TextQualityConfig()
DEFAULT_SCAN_DETECTION_CONFIG = ScanDetectionConfig()
DEFAULT_PARAGRAPH_CONFIG = ParagraphConfig()
