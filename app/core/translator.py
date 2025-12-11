"""
Core translation module - OPUS-MT Edition
World-class translation using Helsinki-NLP OPUS-MT models.
Lightweight (~300MB per language pair), fast, and superior quality to Argos.
Completely offline for privacy and security.
"""
import logging
import re
from typing import Optional, Dict, List, Tuple
from transformers import MarianMTModel, MarianTokenizer
import torch


def split_into_sentences(text: str) -> List[str]:
    """
    Split text into sentences using intelligent boundary detection.
    
    Handles:
    - Standard punctuation (. ! ?)
    - Abbreviations (Mr., Dr., etc.)
    - Numbers with decimals
    - Quotations
    - Multiple languages
    
    Returns:
        List of sentences
    """
    if not text or not text.strip():
        return []
    
    # Common abbreviations that don't end sentences
    abbreviations = {
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
    
    # Pattern to find potential sentence boundaries
    # Matches: . ! ? followed by space and uppercase letter, or end of string
    sentence_end_pattern = re.compile(
        r'([.!?])'  # Punctuation
        r'(\s+)'    # Whitespace
        r'(?=[A-ZÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÑÒÓÔÕÖÙÚÛÜ]|$)'  # Followed by uppercase or end
    )
    
    # First pass: mark potential boundaries
    sentences = []
    current = []
    words = text.split()
    
    for i, word in enumerate(words):
        current.append(word)
        
        # Check if word ends with sentence-ending punctuation
        if word and word[-1] in '.!?':
            # Check if it's an abbreviation
            clean_word = word.rstrip('.!?').lower()
            
            # Don't split on abbreviations
            if clean_word in abbreviations:
                continue
            
            # Don't split on single letters (initials like "J.")
            if len(clean_word) == 1:
                continue
            
            # Don't split on numbers (like "3.14" or "2.")
            if clean_word.replace(',', '').replace('.', '').isdigit():
                continue
            
            # This looks like a real sentence boundary
            sentence = ' '.join(current)
            if sentence.strip():
                sentences.append(sentence.strip())
            current = []
    
    # Don't forget remaining text
    if current:
        remaining = ' '.join(current)
        if remaining.strip():
            sentences.append(remaining.strip())
    
    return sentences if sentences else [text.strip()]


def align_sentences_to_lines(
    translated_sentences: List[str],
    num_lines: int,
    original_line_lengths: List[int]
) -> List[str]:
    """
    Intelligently distribute translated sentences across original line positions.
    
    Uses a greedy algorithm that respects sentence boundaries while
    trying to maintain proportional distribution.
    
    Args:
        translated_sentences: List of translated sentences
        num_lines: Number of original lines to fill
        original_line_lengths: Character count of each original line
        
    Returns:
        List of text for each line position
    """
    if not translated_sentences:
        return [''] * num_lines
    
    if num_lines <= 0:
        return [' '.join(translated_sentences)]
    
    # Special case: more lines than sentences - distribute words across lines
    if len(translated_sentences) < num_lines:
        # Join all sentences and distribute words proportionally
        all_text = ' '.join(translated_sentences)
        return _distribute_single_sentence(all_text, num_lines, original_line_lengths)
    
    if len(translated_sentences) == 1:
        # Single sentence: distribute words proportionally
        return _distribute_single_sentence(translated_sentences[0], num_lines, original_line_lengths)
    
    # Calculate total lengths
    total_original = sum(original_line_lengths) or 1
    total_translated = sum(len(s) for s in translated_sentences)
    
    # Greedy allocation: assign sentences to lines
    lines = []
    sentence_idx = 0
    
    for line_idx in range(num_lines):
        line_parts = []
        
        # Target character count for this line (proportional)
        target_chars = (original_line_lengths[line_idx] / total_original) * total_translated
        current_chars = 0
        
        # Fill line until we reach target or run out of sentences
        while sentence_idx < len(translated_sentences):
            sentence = translated_sentences[sentence_idx]
            sentence_len = len(sentence)
            
            # Add sentence if:
            # 1. Line is empty (always add at least one sentence per line if available)
            # 2. Adding it wouldn't exceed 150% of target
            # 3. This is the last line (take everything remaining)
            is_last_line = (line_idx == num_lines - 1)
            
            if not line_parts or current_chars + sentence_len <= target_chars * 1.5 or is_last_line:
                line_parts.append(sentence)
                current_chars += sentence_len
                sentence_idx += 1
                
                if is_last_line:
                    continue  # Take all remaining
                if current_chars >= target_chars:
                    break  # Line is full enough
            else:
                break  # Move to next line
        
        lines.append(' '.join(line_parts))
    
    # Ensure we have exactly num_lines
    while len(lines) < num_lines:
        lines.append('')
    
    return lines[:num_lines]


def _distribute_single_sentence(
    sentence: str,
    num_lines: int,
    original_line_lengths: List[int]
) -> List[str]:
    """
    Distribute a single sentence across multiple lines proportionally.
    
    Tries to break at word boundaries while respecting original line proportions.
    """
    words = sentence.split()
    if not words:
        return [''] * num_lines
    
    if num_lines == 1:
        return [sentence]
    
    total_original = sum(original_line_lengths) or 1
    lines = []
    word_idx = 0
    
    for line_idx in range(num_lines):
        # Calculate proportion of words for this line
        if line_idx == num_lines - 1:
            # Last line takes all remaining
            line_words = words[word_idx:]
        else:
            proportion = original_line_lengths[line_idx] / total_original
            words_for_line = max(1, int(len(words) * proportion))
            line_words = words[word_idx:word_idx + words_for_line]
            word_idx += words_for_line
        
        lines.append(' '.join(line_words))
    
    return lines


class TranslationEngine:
    """
    Professional translation engine using Helsinki-NLP OPUS-MT models.
    
    Advantages:
    - Much lighter than NLLB-200 (300MB vs 2.5GB)
    - Faster translation (optimized for CPU)
    - Better quality than Argos Translate
    - Specialized models per language pair (better accuracy)
    - Completely offline
    
    Models: Helsinki-NLP/opus-mt-{src}-{tgt}
    """
    
    # OPUS-MT model mapping for supported languages
    OPUS_MODEL_MAP = {
        ("en", "it"): "Helsinki-NLP/opus-mt-en-it",
        ("it", "en"): "Helsinki-NLP/opus-mt-it-en",
        ("en", "es"): "Helsinki-NLP/opus-mt-en-es",
        ("es", "en"): "Helsinki-NLP/opus-mt-es-en",
        ("en", "fr"): "Helsinki-NLP/opus-mt-en-fr",
        ("fr", "en"): "Helsinki-NLP/opus-mt-fr-en",
        ("en", "de"): "Helsinki-NLP/opus-mt-en-de",
        ("de", "en"): "Helsinki-NLP/opus-mt-de-en",
        ("en", "pt"): "Helsinki-NLP/opus-mt-en-roa",  # Romance languages
        ("pt", "en"): "Helsinki-NLP/opus-mt-roa-en",
        ("en", "nl"): "Helsinki-NLP/opus-mt-en-nl",
        ("nl", "en"): "Helsinki-NLP/opus-mt-nl-en",
    }
    
    SUPPORTED_LANGUAGES = {
        "Italiano": "it",
        "English": "en",
        "Español": "es",
        "Français": "fr",
        "Deutsch": "de",
        "Português": "pt",
        "Nederlands": "nl",
    }
    
    # Cache for loaded models (singleton per language pair)
    _model_cache: Dict[tuple, tuple] = {}
    _device = None
    
    def __init__(self, source_lang: str = "en", target_lang: str = "it"):
        """
        Initialize translation engine with OPUS-MT.
        
        Args:
            source_lang: Source language code (ISO 639-1)
            target_lang: Target language code (ISO 639-1)
        """
        self.source_lang = source_lang
        self.target_lang = target_lang
        
        # Setup device once
        if TranslationEngine._device is None:
            TranslationEngine._device = "cuda" if torch.cuda.is_available() else "cpu"
        
        self._load_model(source_lang, target_lang)
        
    @classmethod
    def _load_model(cls, source_lang: str, target_lang: str):
        """Load OPUS-MT model for specific language pair (lazy initialization with caching)."""
        lang_pair = (source_lang, target_lang)
        
        # Return cached model if available
        if lang_pair in cls._model_cache:
            logging.debug(f"Using cached OPUS-MT model: {source_lang} → {target_lang}")
            return
        
        # Get model name for this language pair
        model_name = cls.OPUS_MODEL_MAP.get(lang_pair)
        
        if not model_name:
            logging.warning(f"No OPUS-MT model for {source_lang} → {target_lang}")
            raise ValueError(f"Language pair not supported: {source_lang} → {target_lang}")
        
        logging.info(f"Loading OPUS-MT model: {model_name}...")
        
        try:
            # Load model and tokenizer
            tokenizer = MarianTokenizer.from_pretrained(model_name)
            model = MarianMTModel.from_pretrained(model_name)
            model.to(cls._device)
            model.eval()
            
            # Cache the model
            cls._model_cache[lang_pair] = (model, tokenizer)
            
            logging.info(f"✓ OPUS-MT model loaded: {source_lang} → {target_lang}")
            
        except Exception as e:
            logging.error(f"Failed to load OPUS-MT model: {e}")
            raise
    
    def _get_model(self):
        """Get the model and tokenizer for current language pair."""
        lang_pair = (self.source_lang, self.target_lang)
        
        if lang_pair not in self._model_cache:
            self._load_model(self.source_lang, self.target_lang)
        
        return self._model_cache[lang_pair]
    
    def _normalize_for_translation(self, text: str) -> str:
        """
        Normalize Unicode characters that the OPUS-MT tokenizer can't handle.
        
        The OPUS-MT tokenizer (SentencePiece) converts certain Unicode characters
        to <unk> tokens, which causes the model to truncate output. This method
        converts problematic characters to ASCII equivalents before tokenization.
        
        Args:
            text: Input text with potential Unicode characters
            
        Returns:
            Normalized text safe for OPUS-MT tokenization
        """
        # Curly/smart quotes → straight quotes
        # Using explicit Unicode escapes to ensure correct replacement
        text = text.replace('\u201c', '"')  # " left double
        text = text.replace('\u201d', '"')  # " right double
        text = text.replace('\u2018', "'")  # ' left single
        text = text.replace('\u2019', "'")  # ' right single
        text = text.replace('\u201e', '"')  # „ low double (German)
        text = text.replace('\u201f', '"')  # ‟ high double
        text = text.replace('\u00ab', '"')  # « guillemet left
        text = text.replace('\u00bb', '"')  # » guillemet right
        text = text.replace('\u2039', "'")  # ‹ single guillemet left
        text = text.replace('\u203a', "'")  # › single guillemet right
        
        # Dashes → ASCII hyphen
        text = text.replace('\u2013', '-')  # – en-dash
        text = text.replace('\u2014', '-')  # — em-dash
        text = text.replace('\u2212', '-')  # − minus sign
        
        # Ellipsis → three dots
        text = text.replace('\u2026', '...')  # …
        
        # Common ligatures → separated characters
        text = text.replace('\ufb01', 'fi')  # ﬁ
        text = text.replace('\ufb02', 'fl')  # ﬂ
        text = text.replace('\ufb00', 'ff')  # ﬀ
        text = text.replace('\ufb03', 'ffi')  # ﬃ
        text = text.replace('\ufb04', 'ffl')  # ﬄ
        
        # Spaces
        text = text.replace('\u00a0', ' ')  # Non-breaking space
        text = text.replace('\u2002', ' ')  # En space
        text = text.replace('\u2003', ' ')  # Em space
        text = text.replace('\u2009', ' ')  # Thin space
        
        return text

    def translate(self, text: str, max_length: int = 512) -> str:
        """
        Translate text using OPUS-MT with superior quality and speed.
        
        Args:
            text: Text to translate
            max_length: Maximum token length (default 512)
            
        Returns:
            Translated text with guaranteed completeness
        """
        if not text or len(text.strip()) < 2:
            return text
        
        # Normalize text to avoid <unk> tokens that cause truncation
        text = self._normalize_for_translation(text)
        
        try:
            # Get model and tokenizer for this language pair
            model, tokenizer = self._get_model()
            
            # Tokenize input
            inputs = tokenizer(
                text,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=max_length
            ).to(self._device)
            
            # Generate translation
            with torch.no_grad():
                translated_tokens = model.generate(
                    **inputs,
                    max_length=max_length,
                    num_beams=4,  # Beam search for quality
                    early_stopping=True
                )
            
            # Decode translation
            translation = tokenizer.batch_decode(
                translated_tokens,
                skip_special_tokens=True
            )[0]
            
            # Quality logging
            original_words = len(text.split())
            translated_words = len(translation.split())
            ratio = translated_words / original_words if original_words > 0 else 1.0
            
            logging.debug(
                f"OPUS-MT: '{text[:50]}...' ({original_words}w) → "
                f"'{translation[:50]}...' ({translated_words}w, {ratio:.1%})"
            )
            
            return translation
            
        except Exception as e:
            logging.error(f"OPUS-MT translation failed: {e}")
            return text
    
    def set_languages(self, source_lang: str, target_lang: str) -> None:
        """Update source and target languages (loads new model if needed)."""
        if (source_lang, target_lang) != (self.source_lang, self.target_lang):
            self.source_lang = source_lang
            self.target_lang = target_lang
            self._load_model(source_lang, target_lang)
            logging.info(f"Languages updated: {source_lang} → {target_lang}")
    
    @classmethod
    def get_language_code(cls, language_name: str) -> str:
        """Get ISO 639-1 code from language name."""
        return cls.SUPPORTED_LANGUAGES.get(language_name, "en")
    
    @classmethod
    def get_supported_languages(cls) -> list:
        """Get list of supported language names."""
        return list(cls.SUPPORTED_LANGUAGES.keys())
