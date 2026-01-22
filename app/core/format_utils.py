"""
Text formatting utilities for PDF translation.

Functions for mapping original formatting to translated text,
HTML generation, and text normalization.
"""
import re
from typing import List, Tuple, Optional, Dict

from .formatting import SpanFormat
from .config import LIGATURE_MAP, QUOTE_MAP, DASH_SPACE_MAP


def escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return (text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;"))


def normalize_text_for_pdf(text: str) -> str:
    """
    Normalize text for proper PDF rendering.
    
    Handles:
    - Unicode ligatures (fi, fl, ff, ffi, ffl) → individual chars
    - Typographic quotes → standard quotes
    - Special dashes → standard dashes
    """
    if not text:
        return text
    
    for old, new in LIGATURE_MAP.items():
        text = text.replace(old, new)
    
    for old, new in QUOTE_MAP.items():
        text = text.replace(old, new)
    
    for old, new in DASH_SPACE_MAP.items():
        text = text.replace(old, new)
    
    return text


def map_formatting_to_translation(
    original_segments: List[Tuple[str, SpanFormat]],
    translated_text: str
) -> str:
    """
    Intelligently map original formatting to translated text.
    
    Strategies (in order of preference):
    1. KEYWORD MATCHING: If a formatted segment is a single word that appears
       (or has a similar form) in the translation, format that word directly.
    2. PROPORTIONAL MAPPING: Distribute formatting based on word ratios.
    
    Args:
        original_segments: List of (text, SpanFormat) from original line
        translated_text: The translated text to apply formatting to
        
    Returns:
        HTML-formatted string with inline formatting preserved
    """
    if not original_segments:
        return translated_text
    
    # Single segment with no special formatting = no HTML needed
    if len(original_segments) == 1:
        fmt = original_segments[0][1]
        if not fmt.is_bold and not fmt.is_italic:
            return translated_text
        return fmt.to_html_open_tag() + escape_html(translated_text) + fmt.to_html_close_tag()
    
    # Merge consecutive segments with same formatting
    merged_segments = _merge_adjacent_formats(original_segments)
    
    # If all merged into one, check if we need formatting
    if len(merged_segments) == 1:
        fmt = merged_segments[0][1]
        if not fmt.is_bold and not fmt.is_italic:
            return translated_text
        return fmt.to_html_open_tag() + escape_html(translated_text) + fmt.to_html_close_tag()
    
    # Try keyword matching first
    result = _try_keyword_matching(merged_segments, translated_text)
    if result is not None:
        return result
    
    # Fallback to proportional mapping
    return _proportional_word_mapping(merged_segments, translated_text)


def _try_keyword_matching(
    segments: List[Tuple[str, SpanFormat]],
    translated_text: str
) -> Optional[str]:
    """
    Try to match formatted keywords in the translated text.
    
    Works best when:
    - A formatted segment is a single word or short phrase
    - That word/phrase appears (or is similar) in the translation
    """
    translated_words = translated_text.split()
    
    # Find formatted segments that are single words or short phrases
    formatted_segments = [
        (text, fmt, i) for i, (text, fmt) in enumerate(segments)
        if (fmt.is_bold or fmt.is_italic) and len(text.split()) <= 3
    ]
    
    if not formatted_segments:
        return None
    
    # Track which translated words should be formatted
    word_formats: Dict[int, SpanFormat] = {}
    matched_any = False
    
    for orig_text, fmt, seg_idx in formatted_segments:
        orig_lower = orig_text.lower().strip()
        
        for t_idx, t_word in enumerate(translated_words):
            t_lower = t_word.lower().strip('.,;:!?"\'"()-')
            
            if (_is_word_match(orig_lower, t_lower) and 
                t_idx not in word_formats):
                word_formats[t_idx] = fmt
                matched_any = True
                break
    
    if not matched_any:
        return None
    
    # Build output with matched formatting
    result_parts = []
    current_words = []
    
    for i, word in enumerate(translated_words):
        fmt = word_formats.get(i)
        
        if fmt is not None:
            if current_words:
                result_parts.append(escape_html(" ".join(current_words)))
                current_words = []
            result_parts.append(
                fmt.to_html_open_tag() + escape_html(word) + fmt.to_html_close_tag()
            )
        else:
            current_words.append(word)
    
    if current_words:
        result_parts.append(escape_html(" ".join(current_words)))
    
    return " ".join(result_parts)


def _is_word_match(word1: str, word2: str) -> bool:
    """Check if two words match (exact, prefix, or similar)."""
    if not word1 or not word2:
        return False
    
    # Exact match
    if word1 == word2:
        return True
    
    # Start match
    min_prefix = min(4, len(word1))
    if word2.startswith(word1[:min_prefix]):
        return True
    
    # Contained
    if word1 in word2 or word2 in word1:
        return True
    
    # Similar prefix (for cognates)
    min_len = min(len(word1), len(word2))
    if min_len >= 4:
        prefix_len = min(6, min_len)
        if word1[:prefix_len] == word2[:prefix_len]:
            return True
    
    return False


def _proportional_word_mapping(
    merged_segments: List[Tuple[str, SpanFormat]],
    translated_text: str
) -> str:
    """Distribute formatting proportionally based on word counts."""
    original_word_counts = [len(text.split()) for text, _ in merged_segments]
    total_original_words = sum(original_word_counts)
    
    if total_original_words == 0:
        return translated_text
    
    translated_words = translated_text.split()
    if not translated_words:
        return translated_text
    
    total_translated_words = len(translated_words)
    
    # Calculate ideal distribution
    ideal_distribution = []
    for i, (orig_text, fmt) in enumerate(merged_segments):
        proportion = original_word_counts[i] / total_original_words
        ideal_distribution.append(proportion * total_translated_words)
    
    # Allocate words
    word_distribution = []
    allocated = 0
    
    for i, ideal in enumerate(ideal_distribution):
        if i == len(ideal_distribution) - 1:
            word_count = total_translated_words - allocated
        else:
            word_count = max(1, round(ideal))
            max_available = total_translated_words - allocated - (len(ideal_distribution) - i - 1)
            word_count = min(word_count, max_available)
        
        word_distribution.append(word_count)
        allocated += word_count
    
    # Build HTML output
    html_parts = []
    word_idx = 0
    
    for i, (orig_text, fmt) in enumerate(merged_segments):
        words_for_segment = word_distribution[i]
        segment_words = translated_words[word_idx:word_idx + words_for_segment]
        word_idx += words_for_segment
        
        if not segment_words:
            continue
        
        segment_text = " ".join(segment_words)
        
        if fmt.is_bold or fmt.is_italic:
            html_parts.append(
                fmt.to_html_open_tag() + escape_html(segment_text) + fmt.to_html_close_tag()
            )
        else:
            html_parts.append(escape_html(segment_text))
    
    return " ".join(html_parts)


def _merge_adjacent_formats(
    segments: List[Tuple[str, SpanFormat]]
) -> List[Tuple[str, SpanFormat]]:
    """Merge adjacent segments with same formatting."""
    if len(segments) <= 1:
        return segments
    
    merged = []
    current_text, current_fmt = segments[0]
    
    for text, fmt in segments[1:]:
        if fmt.format_key() == current_fmt.format_key():
            current_text = current_text + " " + text
        else:
            merged.append((current_text, current_fmt))
            current_text, current_fmt = text, fmt
    
    merged.append((current_text, current_fmt))
    return merged


def detect_title_or_heading(
    line_avg_size: float,
    overall_avg_size: float,
    is_bold: bool,
    text: str
) -> bool:
    """
    Detect if a line is likely a title or heading.
    
    Heuristics:
    - Larger font size than average
    - Bold formatting
    - All caps or title case
    - Short length
    - No ending punctuation
    """
    indicators = 0
    
    # Larger font (at least 20% bigger)
    if line_avg_size > overall_avg_size * 1.2:
        indicators += 2
    
    # Bold
    if is_bold:
        indicators += 1
    
    # Short text
    if len(text) < 60:
        indicators += 1
    
    # All caps or Title Case
    text = text.strip()
    if text.isupper() and len(text) > 3:
        indicators += 2
    elif text.istitle() and len(text.split()) <= 8:
        indicators += 1
    
    # No ending punctuation
    if text and text[-1] not in '.!?;:':
        indicators += 1
    
    return indicators >= 3
