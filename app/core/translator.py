"""
Core translation module - CTranslate2 Edition
High-performance offline translation using Helsinki-NLP OPUS-MT models
converted to CTranslate2 INT8 format for 2-4x faster CPU inference.

Inference: CTranslate2 (optimized C++ engine, INT8 quantization)
Tokenization: SentencePiece (native, lightweight)
Models: Helsinki-NLP OPUS-MT (auto-converted on first use)
"""
import logging
import os
import re
import shutil
from pathlib import Path
from typing import Optional, Dict, List, Tuple

import ctranslate2
import sentencepiece as spm

from .sentry_integration import capture_exception, add_breadcrumb


import pysbd


def split_into_sentences(text: str) -> List[str]:
    """
    Split text into sentences using pysbd (pragma sentence boundary detection).

    Handles abbreviations, numbers, quotations, and multiple languages
    out of the box — battle-tested on 100+ edge cases across languages.

    Returns:
        List of sentences (non-empty)
    """
    if not text or not text.strip():
        return []

    segmenter = pysbd.Segmenter(language="en", clean=False)
    sentences = segmenter.segment(text.strip())

    # Filter out empty/whitespace-only segments
    sentences = [s.strip() for s in sentences if s.strip()]
    return sentences if sentences else [text.strip()]


def align_sentences_to_lines(
    translated_sentences: List[str],
    num_lines: int,
    original_line_lengths: List[int]
) -> List[str]:
    """
    Intelligently distribute translated sentences across original line positions.
    
    Strategy:
    - If sentences == lines: one sentence per line (ideal case)
    - If sentences < lines: distribute words of all sentences across lines  
    - If sentences > lines: merge sentences intelligently
    
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
    
    # IDEAL CASE: same number of sentences as lines - direct mapping
    if len(translated_sentences) == num_lines:
        return translated_sentences.copy()
    
    # Case: fewer sentences than lines - distribute words evenly
    if len(translated_sentences) < num_lines:
        all_text = ' '.join(translated_sentences)
        return _distribute_single_sentence(all_text, num_lines, original_line_lengths)
    
    # Case: single sentence for multiple lines
    if len(translated_sentences) == 1:
        return _distribute_single_sentence(translated_sentences[0], num_lines, original_line_lengths)
    
    # Case: more sentences than lines - merge sentences
    # Strategy: distribute sentences as evenly as possible across lines
    sentences_per_line = len(translated_sentences) / num_lines
    
    lines = []
    sentence_idx = 0
    
    for line_idx in range(num_lines):
        # Calculate how many sentences this line should have
        start_idx = sentence_idx
        
        if line_idx == num_lines - 1:
            # Last line takes all remaining
            end_idx = len(translated_sentences)
        else:
            # Calculate end index based on even distribution
            target_end = (line_idx + 1) * sentences_per_line
            end_idx = round(target_end)
            # Ensure at least 1 sentence per line
            end_idx = max(end_idx, start_idx + 1)
        
        # Collect sentences for this line
        line_sentences = translated_sentences[start_idx:end_idx]
        lines.append(' '.join(line_sentences))
        sentence_idx = end_idx
    
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
    Distribute a single sentence across multiple lines.
    
    Uses word-based distribution to avoid breaking words and ensure
    each line has meaningful content.
    
    Strategy: distribute words evenly, with slight bias toward matching
    original proportions, but ensuring minimum words per line.
    """
    words = sentence.split()
    if not words:
        return [''] * num_lines
    
    if num_lines == 1:
        return [sentence]
    
    # If very few words, just put them on the first lines
    if len(words) <= num_lines:
        result = []
        for i in range(num_lines):
            if i < len(words):
                result.append(words[i])
            else:
                result.append('')
        return result
    
    # Calculate target words per line (at least 1 word per line)
    base_words_per_line = len(words) // num_lines
    extra_words = len(words) % num_lines
    
    lines = []
    word_idx = 0
    
    for line_idx in range(num_lines):
        # Each line gets base words, plus 1 extra if we still have remainder
        words_for_this_line = base_words_per_line
        if line_idx < extra_words:
            words_for_this_line += 1
        
        # Last line takes all remaining (safety)
        if line_idx == num_lines - 1:
            line_words = words[word_idx:]
        else:
            line_words = words[word_idx:word_idx + words_for_this_line]
            word_idx += words_for_this_line
        
        lines.append(' '.join(line_words))
    
    return lines


class TranslationEngine:
    """
    High-performance translation engine using CTranslate2 + OPUS-MT.

    Models are automatically converted from HuggingFace format to
    CTranslate2 INT8 format on first use (requires torch+transformers).
    Subsequent loads are near-instant and use only CTranslate2 + SentencePiece.

    Advantages over raw PyTorch inference:
    - 2-4x faster on CPU (optimized C++ kernels)
    - ~4x less runtime memory (INT8 quantization)
    - Simpler inference path (no torch context managers)
    - Same BLEU quality (INT8 is effectively lossless for MT)
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

    # Multi-target models need a target language prefix token
    _TARGET_PREFIX: Dict[tuple, str] = {
        ("en", "pt"): ">>por<<",
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

    # CT2 model cache: lang_pair -> (Translator, sp_source, sp_target)
    _model_cache: Dict[tuple, tuple] = {}
    _model_cache_order: list = []
    _MAX_CACHED_MODELS = 4

    # Directory for converted CT2 models (persistent across runs)
    _CT2_MODELS_DIR = Path.home() / ".cache" / "lac-translate" / "ct2-models"

    def __init__(self, source_lang: str = "en", target_lang: str = "it"):
        """Initialize translation engine with CTranslate2 + OPUS-MT."""
        self.source_lang = source_lang
        self.target_lang = target_lang
        self._ensure_model(source_lang, target_lang)

    # ------------------------------------------------------------------
    # Model management
    # ------------------------------------------------------------------

    @classmethod
    def _get_ct2_path(cls, source_lang: str, target_lang: str) -> Path:
        """Return the on-disk path for a converted CT2 model."""
        return cls._CT2_MODELS_DIR / f"{source_lang}-{target_lang}"

    @classmethod
    def _ensure_model(cls, source_lang: str, target_lang: str):
        """Ensure CT2 model is converted, loaded, and cached."""
        lang_pair = (source_lang, target_lang)

        # Return cached model (move to end for LRU)
        if lang_pair in cls._model_cache:
            logging.debug(f"Using cached CT2 model: {source_lang} -> {target_lang}")
            if lang_pair in cls._model_cache_order:
                cls._model_cache_order.remove(lang_pair)
            cls._model_cache_order.append(lang_pair)
            return

        # Evict oldest model if cache is full
        while len(cls._model_cache) >= cls._MAX_CACHED_MODELS:
            if cls._model_cache_order:
                oldest = cls._model_cache_order.pop(0)
                cls._model_cache.pop(oldest, None)
                logging.info(f"Evicted cached model: {oldest[0]} -> {oldest[1]}")

        hf_name = cls.OPUS_MODEL_MAP.get(lang_pair)
        if not hf_name:
            raise ValueError(f"Language pair not supported: {source_lang} -> {target_lang}")

        ct2_path = cls._get_ct2_path(source_lang, target_lang)

        # One-time conversion from HuggingFace → CTranslate2 INT8
        if not (ct2_path / "model.bin").exists():
            cls._convert_model(hf_name, ct2_path)

        # Load CT2 translator
        logging.info(f"Loading CT2 model: {source_lang} -> {target_lang}")
        device = "cuda" if ctranslate2.get_cuda_device_count() > 0 else "cpu"

        try:
            translator = ctranslate2.Translator(
                str(ct2_path), device=device, compute_type="int8"
            )

            sp_source = spm.SentencePieceProcessor(str(ct2_path / "source.spm"))
            sp_target = spm.SentencePieceProcessor(str(ct2_path / "target.spm"))

            cls._model_cache[lang_pair] = (translator, sp_source, sp_target)
            cls._model_cache_order.append(lang_pair)

            logging.info(
                f"[OK] CT2 model loaded: {source_lang} -> {target_lang} "
                f"(device={device}, cache={len(cls._model_cache)}/{cls._MAX_CACHED_MODELS})"
            )
        except Exception as e:
            capture_exception(e, context={
                "operation": "load_ct2_model",
                "ct2_path": str(ct2_path),
                "source_lang": source_lang,
                "target_lang": target_lang,
            }, tags={"component": "translator"})
            logging.error(f"Failed to load CT2 model: {e}")
            raise

    @classmethod
    def _convert_model(cls, hf_model_name: str, output_dir: Path):
        """
        One-time conversion from HuggingFace OPUS-MT to CTranslate2 INT8.

        This imports torch + transformers lazily (only during conversion).
        After conversion, inference uses only ctranslate2 + sentencepiece.
        """
        logging.info(f"Converting {hf_model_name} -> CTranslate2 INT8 (one-time)...")
        output_dir.parent.mkdir(parents=True, exist_ok=True)

        try:
            converter = ctranslate2.converters.TransformersConverter(hf_model_name)
            converter.convert(str(output_dir), quantization="int8")

            # Ensure SentencePiece models are in the output directory
            # (CT2 converter copies them, but verify and fetch from HF if missing)
            for spm_name in ("source.spm", "target.spm"):
                if not (output_dir / spm_name).exists():
                    from huggingface_hub import hf_hub_download
                    spm_path = hf_hub_download(hf_model_name, spm_name)
                    shutil.copy2(spm_path, output_dir / spm_name)

            logging.info(f"[OK] Model converted: {output_dir}")

        except Exception as e:
            capture_exception(e, context={
                "operation": "convert_model",
                "hf_model": hf_model_name,
            }, tags={"component": "translator"})
            # Clean up partial conversion
            if output_dir.exists():
                shutil.rmtree(output_dir, ignore_errors=True)
            logging.error(f"Model conversion failed: {e}")
            raise

    @classmethod
    def clear_cache(cls):
        """Clear all cached models to free memory."""
        cls._model_cache.clear()
        cls._model_cache_order.clear()
        logging.info("Translation model cache cleared")

    @classmethod
    def get_cache_info(cls) -> dict:
        """Get information about cached models."""
        return {
            "cached_models": list(cls._model_cache.keys()),
            "count": len(cls._model_cache),
            "max_size": cls._MAX_CACHED_MODELS,
        }

    def _get_model(self):
        """Get the (translator, sp_source, sp_target) for current language pair."""
        lang_pair = (self.source_lang, self.target_lang)
        if lang_pair not in self._model_cache:
            self._ensure_model(self.source_lang, self.target_lang)
        return self._model_cache[lang_pair]

    # ------------------------------------------------------------------
    # Text pre/post-processing
    # ------------------------------------------------------------------

    def _normalize_for_translation(self, text: str) -> str:
        """
        Normalize Unicode characters that SentencePiece may map to <unk>.

        Uses NFKC for ligatures/spaces, then explicit maps for quotes/dashes.
        """
        import unicodedata

        # NFKC decomposes ligatures (ﬁ→fi), ellipsis (…→...), special spaces
        text = unicodedata.normalize('NFKC', text)

        # Curly/smart quotes → straight quotes (not handled by NFKC)
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

        # Dashes → ASCII hyphen (not handled by NFKC)
        text = text.replace('\u2013', '-')  # – en-dash
        text = text.replace('\u2014', '-')  # — em-dash
        text = text.replace('\u2212', '-')  # − minus sign

        return text

    def _protect_urls(self, text: str) -> Tuple[str, dict]:
        """
        Extract and protect URLs from being translated.

        URLs confuse the translation model and can cause hallucinations.
        Replaces them with bracketed placeholders that models tend to preserve.
        """
        url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
        placeholders = {}
        counter = [0]

        def replace_url(match):
            url = match.group(0)
            placeholder = f'[URL{counter[0]}]'
            placeholders[placeholder] = url
            counter[0] += 1
            return placeholder

        protected_text = re.sub(url_pattern, replace_url, text)
        return protected_text, placeholders

    def _restore_urls(self, text: str, placeholders: dict) -> str:
        """Restore URLs from placeholders after translation."""
        for placeholder, url in placeholders.items():
            if placeholder in text:
                text = text.replace(placeholder, url)
            else:
                # Try variations the model may have introduced
                base = placeholder.strip('[]')
                patterns = [
                    re.escape(placeholder),
                    r'\[\s*' + re.escape(base) + r'\s*\]',
                    re.escape(base),
                ]
                for pattern in patterns:
                    regex = re.compile(pattern, re.IGNORECASE)
                    if regex.search(text):
                        text = regex.sub(url, text)
                        break
        return text

    # ------------------------------------------------------------------
    # Translation
    # ------------------------------------------------------------------

    def translate(self, text: str, max_length: int = 512) -> str:
        """
        Translate text using CTranslate2 + OPUS-MT.

        Args:
            text: Text to translate
            max_length: Maximum output token length (default 512)

        Returns:
            Translated text
        """
        if not text or len(text.strip()) < 2:
            return text

        # Protect URLs (they cause hallucinations)
        text, url_placeholders = self._protect_urls(text)

        # Normalize problematic Unicode
        text = self._normalize_for_translation(text)

        try:
            translator, sp_source, sp_target = self._get_model()

            # Tokenize with SentencePiece
            tokens = sp_source.encode(text, out_type=str)

            # Prepend target language prefix for multi-target models
            prefix = self._TARGET_PREFIX.get((self.source_lang, self.target_lang))
            if prefix:
                tokens = [prefix] + tokens

            # Translate with CTranslate2
            results = translator.translate_batch(
                [tokens],
                beam_size=4,
                max_decoding_length=max_length,
            )

            # Detokenize
            output_tokens = results[0].hypotheses[0]
            translation = sp_target.decode(output_tokens)

            # Restore protected URLs
            translation = self._restore_urls(translation, url_placeholders)

            # Quality logging
            original_words = len(text.split())
            translated_words = len(translation.split())
            ratio = translated_words / original_words if original_words > 0 else 1.0
            logging.debug(
                f"CT2: '{text[:50]}...' ({original_words}w) -> "
                f"'{translation[:50]}...' ({translated_words}w, {ratio:.1%})"
            )

            return translation

        except Exception as e:
            capture_exception(e, context={
                "operation": "translate",
                "text_length": len(text) if text else 0,
                "source_lang": self.source_lang,
                "target_lang": self.target_lang,
            }, tags={"component": "translator"})
            logging.error(f"CT2 translation failed: {e}")
            return text

    def set_languages(self, source_lang: str, target_lang: str) -> None:
        """Update source and target languages (loads new model if needed)."""
        if (source_lang, target_lang) != (self.source_lang, self.target_lang):
            self.source_lang = source_lang
            self.target_lang = target_lang
            self._ensure_model(source_lang, target_lang)
            logging.info(f"Languages updated: {source_lang} -> {target_lang}")

    @classmethod
    def get_language_code(cls, language_name: str) -> str:
        """Get ISO 639-1 code from language name."""
        return cls.SUPPORTED_LANGUAGES.get(language_name, "en")

    @classmethod
    def get_supported_languages(cls) -> list:
        """Get list of supported language names."""
        return list(cls.SUPPORTED_LANGUAGES.keys())
