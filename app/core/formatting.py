"""
Data classes for PDF text formatting preservation.

This module contains dataclasses for representing text formatting
at the span and line level, enabling intelligent format preservation
during translation.
"""
from dataclasses import dataclass
from typing import Tuple, List, Dict

from .config import MONO_FONT_PATTERNS, SERIF_FONT_PATTERNS


@dataclass
class SpanFormat:
    """
    Represents the formatting attributes of a single text span.
    
    Used to preserve inline formatting (bold, italic, color, size)
    at the character/word level rather than the line level.
    
    Superscript/Subscript detection:
    - PyMuPDF flag bit 0 (1) = superscript
    - Subscript detected by: smaller font + positioned below baseline
    - Also detected by relative size (< 80% of line average)
    """
    text: str
    bbox: Tuple[float, float, float, float]
    size: float
    font: str
    color: Tuple[float, float, float]  # RGB 0.0-1.0
    flags: int = 0
    line_avg_size: float = 0  # Average size of the line
    origin_y: float = 0  # Y position of text origin (baseline)
    line_origin_y: float = 0  # Average baseline Y of the line
    
    @property
    def is_bold(self) -> bool:
        """Check if span is bold (flag bit 16 or 'Bold' in font name)."""
        return bool(self.flags & 16) or 'Bold' in self.font or 'bold' in self.font.lower()
    
    @property
    def is_italic(self) -> bool:
        """Check if span is italic (flag bit 2 or 'Italic' in font name)."""
        return bool(self.flags & 2) or 'Italic' in self.font or 'italic' in self.font.lower()
    
    @property
    def is_superscript(self) -> bool:
        """
        Check if span is superscript.
        
        Detection methods:
        1. PyMuPDF flag bit 0 (1) = superscript
        2. Font size significantly smaller (< 80%) AND positioned above baseline
        3. Font name contains 'Super' or 'Sup'
        """
        # Method 1: Flag
        if bool(self.flags & 1):
            return True
        
        # Method 2: Size + position based detection
        if self.line_avg_size > 0 and self.size < self.line_avg_size * 0.8:
            if self.line_origin_y > 0 and self.origin_y > 0:
                # In PDF, Y increases downward, so superscript has SMALLER y
                if self.origin_y < self.line_origin_y - self.size * 0.3:
                    return True
        
        # Method 3: Font name
        font_lower = self.font.lower()
        if 'super' in font_lower or 'sup' in font_lower:
            return True
        
        return False
    
    @property
    def is_subscript(self) -> bool:
        """
        Check if span is subscript.
        
        Detection methods:
        1. Font size significantly smaller (< 80%) AND positioned below baseline
        2. Font name contains 'Sub'
        """
        # Method 1: Size + position based detection
        if self.line_avg_size > 0 and self.size < self.line_avg_size * 0.8:
            if self.line_origin_y > 0 and self.origin_y > 0:
                # In PDF, Y increases downward, so subscript has LARGER y
                if self.origin_y > self.line_origin_y + self.size * 0.2:
                    return True
        
        # Method 2: Font name
        font_lower = self.font.lower()
        if 'sub' in font_lower and 'subhead' not in font_lower:
            return True
        
        return False
    
    @property
    def is_monospace(self) -> bool:
        """Check if font is monospace."""
        return any(p.lower() in self.font.lower() for p in MONO_FONT_PATTERNS)
    
    @property
    def is_serif(self) -> bool:
        """Check if font is serif."""
        return any(p.lower() in self.font.lower() for p in SERIF_FONT_PATTERNS)
    
    @property
    def char_count(self) -> int:
        """Number of characters in this span."""
        return len(self.text)
    
    @property
    def word_count(self) -> int:
        """Number of words in this span."""
        return len(self.text.split())
    
    def format_key(self) -> str:
        """
        Generate a unique key for this formatting style.
        Used to detect when formatting changes between spans.
        """
        return f"{self.is_bold}|{self.is_italic}|{self.size:.1f}|{self.color}|{self.font[:10]}"
    
    def to_css_style(self) -> str:
        """Generate inline CSS for this span's formatting."""
        styles = []
        
        if self.is_bold:
            styles.append("font-weight: bold")
        if self.is_italic:
            styles.append("font-style: italic")
        
        r, g, b = self.color
        styles.append(f"color: rgb({int(r*255)}, {int(g*255)}, {int(b*255)})")
        
        return "; ".join(styles)
    
    def to_html_open_tag(self) -> str:
        """Generate opening HTML tags for formatting."""
        tags = []
        if self.is_superscript:
            tags.append("<sup>")
        if self.is_subscript:
            tags.append("<sub>")
        if self.is_bold:
            tags.append("<b>")
        if self.is_italic:
            tags.append("<i>")
        return "".join(tags)
    
    def to_html_close_tag(self) -> str:
        """Generate closing HTML tags (reverse order)."""
        tags = []
        if self.is_italic:
            tags.append("</i>")
        if self.is_bold:
            tags.append("</b>")
        if self.is_subscript:
            tags.append("</sub>")
        if self.is_superscript:
            tags.append("</sup>")
        return "".join(tags)


@dataclass
class LineFormatInfo:
    """
    Complete formatting information for a line, preserving span-level details.
    
    Replaces the old line_data dict with a proper structure that
    maintains full span information for intelligent format mapping.
    """
    text: str
    spans: List[SpanFormat]
    merged_bbox: Tuple[float, float, float, float]
    rotation: int = 0
    wmode: int = 0
    
    @property
    def avg_size(self) -> float:
        """Average font size across all spans."""
        if not self.spans:
            return 11.0
        total_chars = sum(s.char_count for s in self.spans)
        if total_chars == 0:
            return sum(s.size for s in self.spans) / len(self.spans)
        return sum(s.size * s.char_count for s in self.spans) / total_chars
    
    @property
    def dominant_color(self) -> Tuple[float, float, float]:
        """Most common color in the line (by character count)."""
        if not self.spans:
            return (0, 0, 0)
        color_chars: Dict[Tuple, int] = {}
        for span in self.spans:
            key = span.color
            color_chars[key] = color_chars.get(key, 0) + span.char_count
        return max(color_chars.keys(), key=lambda c: color_chars[c])
    
    @property
    def has_mixed_formatting(self) -> bool:
        """Check if line has multiple different formatting styles."""
        if len(self.spans) <= 1:
            return False
        first_key = self.spans[0].format_key()
        return any(s.format_key() != first_key for s in self.spans[1:])
    
    @property
    def is_bold(self) -> bool:
        """Check if majority of text is bold."""
        if not self.spans:
            return False
        bold_chars = sum(s.char_count for s in self.spans if s.is_bold)
        total_chars = sum(s.char_count for s in self.spans)
        return bold_chars > total_chars / 2 if total_chars > 0 else False
    
    @property
    def is_italic(self) -> bool:
        """Check if majority of text is italic."""
        if not self.spans:
            return False
        italic_chars = sum(s.char_count for s in self.spans if s.is_italic)
        total_chars = sum(s.char_count for s in self.spans)
        return italic_chars > total_chars / 2 if total_chars > 0 else False
    
    @property
    def is_monospace(self) -> bool:
        """Check if any span is monospace."""
        return any(s.is_monospace for s in self.spans)
    
    @property
    def is_serif(self) -> bool:
        """Check if majority of text is serif."""
        if not self.spans:
            return False
        serif_chars = sum(s.char_count for s in self.spans if s.is_serif)
        total_chars = sum(s.char_count for s in self.spans)
        return serif_chars > total_chars / 2 if total_chars > 0 else False
    
    def get_formatting_segments(self) -> List[Tuple[str, SpanFormat]]:
        """
        Get list of (text, format) pairs for each span.
        Consecutive spans with same formatting are merged.
        """
        if not self.spans:
            return []
        
        segments = []
        current_format = self.spans[0]
        current_text = self.spans[0].text
        
        for span in self.spans[1:]:
            if span.format_key() == current_format.format_key():
                # Same formatting, merge text
                current_text += " " + span.text
            else:
                # Different formatting, save current and start new
                segments.append((current_text, current_format))
                current_format = span
                current_text = span.text
        
        # Don't forget the last segment
        segments.append((current_text, current_format))
        return segments
    
    def to_legacy_dict(self) -> dict:
        """
        Convert to legacy line_data dict format for backward compatibility.
        """
        return {
            'text': self.text,
            'bboxes': [s.bbox for s in self.spans],
            'sizes': [s.size for s in self.spans],
            'fonts': [s.font for s in self.spans],
            'colors': [s.color for s in self.spans],
            'dominant_color': self.dominant_color,
            'merged_bbox': self.merged_bbox,
            'avg_size': self.avg_size,
            'is_bold': self.is_bold,
            'is_italic': self.is_italic,
            'is_serif': self.is_serif,
            'is_monospace': self.is_monospace,
            'rotation': self.rotation,
            'wmode': self.wmode,
            'spans': self.spans,
            'has_mixed_formatting': self.has_mixed_formatting,
        }
