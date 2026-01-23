"""
Core package initialization

This package provides:
- PDFProcessor: PDF processing with OCR support
- TranslationEngine: OPUS-MT based translation
- Config classes: Centralized configuration
- Formatting classes: Text formatting preservation
- Sentry integration: Error tracking and monitoring
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
from .sentry_integration import (
    init_sentry,
    capture_exception,
    capture_message,
    add_breadcrumb,
    set_user,
    set_tag,
    set_context,
    is_initialized,
    flush,
    track_pdf_operation,
    track_translation,
    configure_qt_exception_hook,
)

__all__ = [
    # Core processors
    'TranslationEngine', 
    'PDFProcessor',
    # Config
    'OCRConfig',
    'TextQualityConfig',
    'ScanDetectionConfig', 
    'ParagraphConfig',
    'DEFAULT_OCR_CONFIG',
    'DEFAULT_TEXT_QUALITY_CONFIG',
    'DEFAULT_SCAN_DETECTION_CONFIG',
    'DEFAULT_PARAGRAPH_CONFIG',
    # Formatting
    'SpanFormat',
    'LineFormatInfo',
    'map_formatting_to_translation',
    'normalize_text_for_pdf',
    'escape_html',
    'detect_title_or_heading',
    # Sentry
    'init_sentry',
    'capture_exception',
    'capture_message',
    'add_breadcrumb',
    'set_user',
    'set_tag',
    'set_context',
    'is_initialized',
    'flush',
    'track_pdf_operation',
    'track_translation',
    'configure_qt_exception_hook',
]
