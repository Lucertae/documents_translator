"""
Core package initialization

This package provides:
- PDFProcessor: PDF processing with OCR support
- TranslationEngine: OPUS-MT based translation
- Config classes: Centralized configuration
- Formatting classes: Text formatting preservation
"""
from .translator import TranslationEngine
from .pdf_processor import PDFProcessor
from .config import (
    OCRConfig, 
    TextQualityConfig, 
    ScanDetectionConfig,
    ParagraphConfig,
    DEFAULT_OCR_CONFIG,
    DEFAULT_TEXT_QUALITY_CONFIG,
    DEFAULT_SCAN_DETECTION_CONFIG,
    DEFAULT_PARAGRAPH_CONFIG,
)
from .formatting import SpanFormat, LineFormatInfo
from .format_utils import (
    map_formatting_to_translation,
    normalize_text_for_pdf,
    escape_html,
    detect_title_or_heading,
)

__all__ = [
    'TranslationEngine', 
    'PDFProcessor',
    'OCRConfig',
    'TextQualityConfig',
    'ScanDetectionConfig', 
    'ParagraphConfig',
    'DEFAULT_OCR_CONFIG',
    'DEFAULT_TEXT_QUALITY_CONFIG',
    'DEFAULT_SCAN_DETECTION_CONFIG',
    'DEFAULT_PARAGRAPH_CONFIG',
    'SpanFormat',
    'LineFormatInfo',
    'map_formatting_to_translation',
    'normalize_text_for_pdf',
    'escape_html',
    'detect_title_or_heading',
]
