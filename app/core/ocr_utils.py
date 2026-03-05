"""
OCR post-processing utilities.

Functions for cleaning up OCR output, correcting common errors,
and improving text quality.

Note: Some corrections are domain-specific (legal distribution contracts:
Article numbering, Exhibit references, Mimaki brand name). These are
intentional for the primary use case but may cause false positives on
unrelated document types.
"""
import re
from typing import List, Tuple


# ============================================
# Common OCR Substitutions
# ============================================

# Case-insensitive replacements for known OCR errors
# Format: (wrong_pattern, correct_replacement)
OCR_CORRECTIONS: List[Tuple[str, str]] = [
    # --- Compound all-caps words that OCR merges ---
    # These must come FIRST before word-level corrections
    (r'AUTHORIZEDDISTRIBUTION', 'AUTHORIZED DISTRIBUTION'),
    (r'DISTRIBUTIONAGREEMENT', 'DISTRIBUTION AGREEMENT'),
    (r'AUTHORISEDDISTRIBUTOR', 'AUTHORISED DISTRIBUTOR'),
    (r'NONCOMPETITION', 'NON-COMPETITION'),
    
    # Mimaki brand - fix OCR errors while preserving case
    # All-caps variants (check full uppercase first)
    (r'\bMIMAKl\b', 'MIMAKI'),   # l misread as I
    (r'\bMImakI\b', 'MIMAKI'),   # Mixed case
    (r'\bMImaki\b', 'Mimaki'),   # MI→Mi at start
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
    # Normalize Exhibit# → Exhibit #
    (r'\bExhibit\s*#\s*', 'Exhibit #'),
    
    # Article/ICE confusion (domain-specific: legal contracts)
    # Only match at line start or after period to reduce false positives
    (r'(?:^|\.\s+)ICE\s+(\d+)\b', r'Article \1'),
    # Missing space in "Article8" → "Article 8"
    (r'\bArticle(\d+)\b', r'Article \1'),
    (r'\bArticle\s*(\d+)\s*-\s*', r'Article \1 – '),  # Normalize dash to en-dash
    
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
    
    # Common ligature misreads — handle actual Unicode ligatures
    (r'\ufb00', 'ff'),  # ﬀ ligature
    (r'\ufb01', 'fi'),  # ﬁ ligature
    (r'\ufb02', 'fl'),  # ﬂ ligature
    
    # Missing spaces in OCR-merged words (camelCase)
    # Only split when both sides are at least 3 chars to avoid breaking
    # proper names like "McDonald" or "MacArthur"
    (r'(?<=[a-z]{3})(?=[A-Z][a-z]{2})', ' '),
    
    # Fix "Mimakis" (possessive without apostrophe) → "Mimaki's"
    (r'\bMimakis\b', "Mimaki's"),
    (r'\bMIMAKIS\b', "MIMAKI'S"),
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
    
    # Clean up multiple horizontal spaces (preserve newlines for line-based filters)
    text = re.sub(r'[^\S\n]+', ' ', text)
    
    # Collapse multiple blank lines into one paragraph break
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Fix spacing around punctuation (horizontal only, don't join lines)
    text = re.sub(r' +([.,;:!?])', r'\1', text)
    text = re.sub(r'([.,;:!?])(?=[A-Za-z])', r'\1 ', text)
    
    # Strip trailing spaces per line
    text = '\n'.join(line.rstrip() for line in text.split('\n'))
    
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


def remove_page_artifacts(text: str) -> str:
    """
    Remove common page artifacts from OCR text.
    
    Removes only high-confidence noise:
    - Page numbers (standalone numbers)
    - Very short non-alpha noise
    - Lines that are just punctuation
    """
    if not text:
        return text
    
    lines = text.split('\n')
    cleaned = []
    
    for line in lines:
        stripped = line.strip()
        
        # Preserve blank lines (they mark paragraph boundaries)
        if not stripped:
            cleaned.append('')
            continue
        
        # Skip standalone page numbers
        if re.match(r'^[\d]+$', stripped):
            continue
        
        # Skip very short lines that look like noise (but not short words)
        if len(stripped) < 3 and not stripped.isalpha():
            continue
        
        # Skip lines that are just punctuation
        if re.match(r'^[\W]+$', stripped):
            continue
        
        cleaned.append(stripped)
    
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
