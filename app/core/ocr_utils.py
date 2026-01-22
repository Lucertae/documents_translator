"""
OCR post-processing utilities.

Functions for cleaning up OCR output, correcting common errors,
and improving text quality.
"""
import re
from typing import List, Dict, Tuple


# ============================================
# Common OCR Substitutions
# ============================================

# Case-insensitive replacements for known OCR errors
# Format: (wrong_pattern, correct_replacement)
OCR_CORRECTIONS: List[Tuple[str, str]] = [
    # Mimaki brand - fix OCR errors while preserving case
    # All-caps variants (check full uppercase first)
    (r'\bMIMAKl\b', 'MIMAKI'),   # l misread as I
    # Title-case variants (uppercase M, lowercase rest except last char)
    (r'\bMimaKI\b', 'Mimaki'),   # Capital K followed by capital I
    (r'\bMimakI\b', 'Mimaki'),   # Capital I at end
    (r'\bMimakl\b', 'Mimaki'),   # lowercase l at end
    (r'\bMimak1\b', 'Mimaki'),   # digit 1 at end
    # Lowercase variants (all lowercase except possibly wrong last char)
    (r'\bmimakl\b', 'mimaki'),   # l misread
    (r'\bmimak1\b', 'mimaki'),   # 1 misread
    
    # I/l/1 confusion in Exhibit
    (r'\bExhlbit\b', 'Exhibit'),
    (r'\bExhiblt\b', 'Exhibit'),
    (r'\bexhlbit\b', 'exhibit'),
    (r'\bExhlblt\b', 'Exhibit'),
    (r'\bnibit\b', 'Exhibit'),
    (r'\bNibit\b', 'Exhibit'),
    (r'\bibit\b', 'Exhibit'),
    (r'\bExhibit\s*#\s*', 'Exhibit #'),  # Normalize spacing
    
    # Article/ICE confusion  
    (r'\bICE\s+(\d+)\b', r'Article \1'),
    (r'\bIce\s+(\d+)\b', r'Article \1'),
    # Truncated "Article" (OCR sometimes misses "Artic")
    (r'\ble\s+(\d+)\s*-', r'Article \1 -'),  # "le 4 -" -> "Article 4 -"
    
    # Common word confusions
    (r'\bArtlcle\b', 'Article'),
    (r'\bartlcle\b', 'article'),
    (r'\bARTlCLE\b', 'ARTICLE'),
    
    # O/0 confusion in words
    (r'\bAuth0rized\b', 'Authorized'),
    (r'\bDistribut0r\b', 'Distributor'),
    
    # S/5 confusion
    (r'\b5ection\b', 'Section'),
    (r'\b5igned\b', 'Signed'),
    
    # Common ligature misreads
    (r'\bff\b(?=[a-z])', 'ff'),  # ff at word start
    (r'(?<=[a-z])ff\b', 'ff'),  # ff at word end
]

# Numbers that should remain as-is (don't correct these)
PRESERVE_PATTERNS = [
    r'\d+\.\d+',  # Decimal numbers
    r'#\d+',      # Reference numbers
    r'§\d+',      # Section symbols
]


def clean_ocr_text(text: str) -> str:
    """
    Clean and correct common OCR errors in text.
    
    Applies pattern-based corrections for known OCR confusions
    like I/l/1, O/0, S/5, etc.
    
    Args:
        text: Raw OCR text
        
    Returns:
        Cleaned text with common errors corrected
    """
    if not text:
        return text
    
    # Apply corrections - no IGNORECASE flag, patterns must be explicit
    for pattern, replacement in OCR_CORRECTIONS:
        text = re.sub(pattern, replacement, text)
    
    # Clean table of contents dots (e.g., "Article 1 ........... 5" -> "Article 1 ... 5")
    # Multiple dots (4+) are likely TOC leaders
    text = re.sub(r'\.{4,}', ' ... ', text)
    
    # Clean up multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    # Fix spacing around punctuation
    text = re.sub(r'\s+([.,;:!?])', r'\1', text)
    text = re.sub(r'([.,;:!?])(?=[A-Za-z])', r'\1 ', text)
    
    return text.strip()


def fix_line_breaks(text: str) -> str:
    """
    Fix incorrectly broken lines from OCR.
    
    Handles:
    - Words broken across lines (hyphenation)
    - Sentences split across lines
    - Paragraph detection
    """
    if not text:
        return text
    
    lines = text.split('\n')
    fixed_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if not line:
            fixed_lines.append('')
            i += 1
            continue
        
        # Check if line ends with hyphen (word continuation)
        if line.endswith('-') and i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            if next_line:
                # Join hyphenated word
                words_next = next_line.split(None, 1)
                if words_next:
                    line = line[:-1] + words_next[0]
                    if len(words_next) > 1:
                        lines[i + 1] = words_next[1]
                    else:
                        lines[i + 1] = ''
        
        fixed_lines.append(line)
        i += 1
    
    return '\n'.join(fixed_lines)


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace in OCR text.
    
    - Collapse multiple spaces
    - Remove leading/trailing whitespace per line
    - Preserve paragraph breaks (double newlines)
    """
    if not text:
        return text
    
    # Split into paragraphs (preserve double newlines)
    paragraphs = re.split(r'\n\s*\n', text)
    
    normalized = []
    for para in paragraphs:
        # Normalize spaces within paragraph
        para = re.sub(r'[ \t]+', ' ', para)
        # Remove single newlines (join lines)
        para = re.sub(r'\n', ' ', para)
        para = para.strip()
        if para:
            normalized.append(para)
    
    return '\n\n'.join(normalized)


def detect_and_fix_columns(text_regions: List[Dict], page_width: float) -> List[Dict]:
    """
    Detect column layout and reorder text regions for proper reading order.
    
    Args:
        text_regions: List of {'text': str, 'bbox': dict, ...}
        page_width: Page width for column detection
        
    Returns:
        Reordered text regions in reading order
    """
    if not text_regions:
        return text_regions
    
    # Detect columns by clustering x positions
    positioned = [r for r in text_regions if r.get('bbox')]
    
    if not positioned:
        return text_regions
    
    # Find column boundaries using gap analysis
    x_positions = sorted(set(r['bbox'].get('center_x', 0) for r in positioned))
    
    if len(x_positions) < 2:
        return text_regions
    
    # Find large gaps (> 10% page width)
    min_gap = page_width * 0.10
    columns = []
    current_col = [x_positions[0]]
    
    for i in range(1, len(x_positions)):
        gap = x_positions[i] - x_positions[i-1]
        if gap > min_gap:
            columns.append(current_col)
            current_col = [x_positions[i]]
        else:
            current_col.append(x_positions[i])
    columns.append(current_col)
    
    if len(columns) <= 1:
        # Single column - sort by y position
        return sorted(text_regions, key=lambda r: r.get('bbox', {}).get('y0', 0))
    
    # Multi-column: assign regions to columns and sort
    column_bounds = []
    for col in columns:
        col_min = min(col) - min_gap/2
        col_max = max(col) + min_gap/2
        column_bounds.append((col_min, col_max))
    
    # Assign and sort
    result = []
    for col_idx, (col_min, col_max) in enumerate(column_bounds):
        col_regions = [
            r for r in positioned 
            if col_min <= r['bbox'].get('center_x', 0) <= col_max
        ]
        col_regions.sort(key=lambda r: r['bbox'].get('y0', 0))
        result.extend(col_regions)
    
    # Add unpositioned regions at the end
    unpositioned = [r for r in text_regions if not r.get('bbox')]
    result.extend(unpositioned)
    
    return result


def remove_page_artifacts(text: str) -> str:
    """
    Remove common page artifacts from OCR text.
    
    Removes:
    - Page numbers (standalone numbers)
    - Headers/footers (repeated patterns)
    - Watermarks
    """
    if not text:
        return text
    
    lines = text.split('\n')
    cleaned = []
    
    for line in lines:
        line = line.strip()
        
        # Skip standalone page numbers
        if re.match(r'^[\d]+$', line):
            continue
        
        # Skip very short lines that look like headers
        if len(line) < 3 and not line.isalpha():
            continue
        
        # Skip lines that are just punctuation
        if re.match(r'^[\W]+$', line):
            continue
        
        cleaned.append(line)
    
    return '\n'.join(cleaned)


def post_process_ocr_text(text: str) -> str:
    """
    Apply full post-processing pipeline to OCR text.
    
    Steps:
    1. Clean common OCR errors
    2. Fix line breaks
    3. Remove artifacts
    4. Normalize whitespace
    
    Args:
        text: Raw OCR text
        
    Returns:
        Cleaned and corrected text
    """
    if not text:
        return text
    
    # Step 1: Clean OCR errors
    text = clean_ocr_text(text)
    
    # Step 2: Fix line breaks
    text = fix_line_breaks(text)
    
    # Step 3: Remove artifacts
    text = remove_page_artifacts(text)
    
    # Step 4: Normalize whitespace
    text = normalize_whitespace(text)
    
    return text
