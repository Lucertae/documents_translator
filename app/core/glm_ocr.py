"""
GLM-OCR integration via Ollama.

Uses the GLM-OCR model (0.9B parameters) for high-quality document OCR.
GLM-OCR achieves 94.62 on OmniDocBench V1.5, ranking #1 overall.

Architecture:
    App <-> ollama Python client (HTTP) <-> Ollama server <-> GLM-OCR model

Features:
- State-of-the-art OCR accuracy (94.62 on OmniDocBench V1.5, #1 overall)
- Text, table, and figure recognition modes
- 128K context window for large documents
- Robust on complex tables, code, seals, multi-column layouts
- Easy deployment via Ollama (CPU or GPU)
- ~2.2GB model size (0.9B parameters)

Usage:
    from app.core.glm_ocr import GlmOcrEngine

    engine = GlmOcrEngine()
    text, confidence = engine.recognize_text(image_bytes)
    structured = engine.recognize_document_page(image_bytes)
"""
import base64
import logging
import os
import platform
import shutil
import subprocess
import time
from typing import Optional, Tuple, Callable

from .sentry_integration import capture_exception

# Try to import ollama
try:
    import ollama
    from ollama import Client, ResponseError
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    logging.warning("Ollama library not installed - run: pip install ollama")


# Model configuration
GLM_OCR_MODEL = "glm-ocr:q8_0"
GLM_OCR_MODEL_SMALL = "glm-ocr:q8_0"  # Smaller quantized version (1.6GB)

# Ollama server configuration
DEFAULT_OLLAMA_HOST = "http://localhost:11434"
OLLAMA_STARTUP_TIMEOUT = 30  # seconds to wait for Ollama server to start


class OllamaServerManager:
    """
    Manages the Ollama server lifecycle (start/stop/check).

    For bundled builds, can start Ollama from a local binary.
    For development, assumes Ollama is installed system-wide.
    """

    _process: Optional[subprocess.Popen] = None
    _managed: bool = False  # True if we started the server ourselves

    @classmethod
    def is_running(cls, host: str = DEFAULT_OLLAMA_HOST) -> bool:
        """Check if Ollama server is responding."""
        try:
            client = Client(host=host)
            client.list()
            return True
        except Exception:
            return False

    @classmethod
    def start(cls, host: str = DEFAULT_OLLAMA_HOST) -> bool:
        """
        Start Ollama server if not already running.

        Tries in order:
        1. Check if already running
        2. Start from bundled binary (PyInstaller build)
        3. Start from system-installed ollama

        Returns:
            True if server is running after this call
        """
        if cls.is_running(host):
            logging.info("Ollama server already running")
            return True

        # Find ollama binary
        ollama_bin = cls._find_ollama_binary()
        if not ollama_bin:
            logging.error(
                "Ollama binary not found. Install from https://ollama.com/download"
            )
            return False

        logging.info(f"Starting Ollama server from: {ollama_bin}")
        try:
            env = os.environ.copy()
            # Suppress Ollama's own logging to stdout
            env["OLLAMA_HOST"] = host.replace("http://", "")

            cls._process = subprocess.Popen(
                [ollama_bin, "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env=env,
            )
            cls._managed = True

            # Wait for server to be ready
            for i in range(OLLAMA_STARTUP_TIMEOUT):
                time.sleep(1)
                if cls.is_running(host):
                    logging.info(f"Ollama server started (pid={cls._process.pid})")
                    return True

            logging.error("Ollama server failed to start within timeout")
            cls.stop()
            return False

        except Exception as e:
            capture_exception(e, context={"operation": "start_ollama"})
            logging.error(f"Failed to start Ollama: {e}")
            return False

    @classmethod
    def stop(cls) -> None:
        """Stop Ollama server if we started it."""
        if cls._process and cls._managed:
            logging.info("Stopping managed Ollama server...")
            try:
                cls._process.terminate()
                cls._process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                cls._process.kill()
            except Exception as e:
                logging.warning(f"Error stopping Ollama: {e}")
            finally:
                cls._process = None
                cls._managed = False

    @classmethod
    def _find_ollama_binary(cls) -> Optional[str]:
        """Find the Ollama binary, checking bundled location first."""
        # 1. Check bundled binary (PyInstaller _MEIPASS or relative to exe)
        bundled_paths = []
        if hasattr(__import__('sys'), '_MEIPASS'):
            import sys
            meipass = sys._MEIPASS
            if platform.system() == "Windows":
                bundled_paths.append(os.path.join(meipass, "ollama", "ollama.exe"))
            else:
                bundled_paths.append(os.path.join(meipass, "ollama", "ollama"))

        for p in bundled_paths:
            if os.path.isfile(p):
                return p

        # 2. Check system PATH
        system_bin = shutil.which("ollama")
        if system_bin:
            return system_bin

        # 3. Common install locations
        common_paths = []
        if platform.system() == "Windows":
            common_paths = [
                os.path.expandvars(r"%LOCALAPPDATA%\Ollama\ollama.exe"),
                os.path.expandvars(r"%PROGRAMFILES%\Ollama\ollama.exe"),
            ]
        elif platform.system() == "Darwin":
            common_paths = ["/usr/local/bin/ollama"]
        else:
            common_paths = ["/usr/local/bin/ollama", "/usr/bin/ollama"]

        for p in common_paths:
            if os.path.isfile(p):
                return p

        return None


class GlmOcrEngine:
    """
    GLM-OCR engine using Ollama for document OCR.

    GLM-OCR is a multimodal OCR model for complex document understanding,
    built on the GLM-V encoder-decoder architecture. It provides:
    - 94.62 score on OmniDocBench V1.5 (#1 overall)
    - Robust performance on complex tables, code, seals
    - Text, table, and figure recognition modes
    - 128K context window
    - Only 0.9B parameters for efficient inference
    """

    _instance: Optional['GlmOcrEngine'] = None
    _client: Optional['Client'] = None
    _model_name: Optional[str] = None  # Actual model name found on server
    _model_verified: bool = False
    _host: str = DEFAULT_OLLAMA_HOST

    def __new__(cls) -> 'GlmOcrEngine':
        """Singleton pattern for OCR engine."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, host: str = DEFAULT_OLLAMA_HOST):
        """
        Initialize GLM-OCR engine.

        Args:
            host: Ollama server URL (default: localhost:11434)
        """
        if not OLLAMA_AVAILABLE:
            logging.error("Ollama library not available")
            return

        if self._client is None:
            self._client = Client(host=host)
            self._host = host
            logging.info(f"GLM-OCR engine initialized (Ollama host: {host})")

    def is_available(self) -> bool:
        """Check if GLM-OCR is available and ready."""
        if not OLLAMA_AVAILABLE:
            return False

        if self._model_verified:
            return True

        try:
            # Ollama Python client returns objects, not dicts
            response = self._client.list()
            models = response.models if hasattr(response, 'models') else []
            model_names = []
            for m in models:
                # Each model has .model attribute (e.g. "glm-ocr:latest")
                name = getattr(m, 'model', None) or getattr(m, 'name', '')
                if name:
                    model_names.append(name)

            for target in [GLM_OCR_MODEL, GLM_OCR_MODEL_SMALL]:
                if target in model_names:
                    self._model_verified = True
                    self._model_name = target
                    logging.info(f"GLM-OCR model verified: {target}")
                    return True

            logging.warning(f"GLM-OCR model not found. Available: {model_names}")
            return False

        except Exception as e:
            logging.warning(f"Cannot connect to Ollama: {e}")
            return False

    def ensure_model(self) -> bool:
        """
        Ensure GLM-OCR model is pulled and ready.
        Starts Ollama server if needed.

        Returns:
            True if model is ready, False otherwise
        """
        if self.is_available():
            return True

        if not OLLAMA_AVAILABLE:
            logging.error("Ollama library not installed")
            return False

        # Try to start server if not running
        if not OllamaServerManager.is_running(self._host):
            if not OllamaServerManager.start(self._host):
                return False
            # Re-create client after server start
            self._client = Client(host=self._host)

        # Check again after server start
        if self.is_available():
            return True

        logging.info(f"Pulling GLM-OCR model ({GLM_OCR_MODEL})...")
        try:
            self._client.pull(GLM_OCR_MODEL)
            self._model_verified = True
            self._model_name = GLM_OCR_MODEL
            logging.info("GLM-OCR model pulled successfully")
            return True
        except Exception as e:
            capture_exception(
                e, context={"operation": "pull_glm_ocr"}, tags={"component": "ocr"}
            )
            logging.error(f"Failed to pull GLM-OCR model: {e}")
            return False

    def recognize_text(
        self,
        image_data: bytes,
        mode: str = "text",
    ) -> Tuple[str, float]:
        """
        Recognize text from image using GLM-OCR.

        GLM-OCR supports three recognition modes:
        - "text": General text recognition (default)
        - "table": Table structure recognition (returns markdown tables)
        - "figure": Figure/chart description

        Args:
            image_data: Image bytes (PNG, JPEG, etc.)
            mode: Recognition mode - "text", "table", or "figure"

        Returns:
            Tuple of (recognized_text, confidence_score)
            confidence_score is estimated based on response quality
        """
        if not OLLAMA_AVAILABLE:
            return "", 0.0

        if not self.is_available():
            if not self.ensure_model():
                return "", 0.0

        # Convert image to base64
        image_b64 = base64.b64encode(image_data).decode('utf-8')

        # GLM-OCR official prompts (from model documentation)
        prompts = {
            "text": "Text Recognition:",
            "table": "Table Recognition:",
            "figure": "Figure Recognition:",
        }
        prompt = prompts.get(mode, "Text Recognition:")
        model = self._model_name or GLM_OCR_MODEL

        try:
            # Call GLM-OCR via Ollama chat API
            # Ollama Python client returns ChatResponse objects (attribute access)
            response = self._client.chat(
                model=model,
                messages=[{
                    'role': 'user',
                    'content': prompt,
                    'images': [image_b64],
                }],
                options={
                    'temperature': 0.1,  # Low temp for deterministic OCR output
                    'num_predict': 16384,  # 16K tokens for long documents
                    'num_ctx': 8192,  # Context window
                },
            )

            # ChatResponse has .message.content (object attributes, not dict)
            text = response.message.content if response.message else ''

            # Estimate confidence based on response quality
            confidence = self._estimate_confidence(text)

            logging.debug(
                f"GLM-OCR [{mode}]: {len(text)} chars, confidence={confidence:.2f}"
            )
            return text.strip(), confidence

        except ResponseError as e:
            capture_exception(
                e,
                context={"operation": "glm_ocr_recognize", "mode": mode},
                tags={"component": "ocr"},
            )
            logging.error(f"GLM-OCR request failed: {e}")
            return "", 0.0
        except Exception as e:
            capture_exception(
                e,
                context={"operation": "glm_ocr_recognize", "mode": mode},
                tags={"component": "ocr"},
            )
            logging.error(f"GLM-OCR error: {e}")
            return "", 0.0

    def _estimate_confidence(self, text: str) -> float:
        """
        Estimate OCR confidence based on output quality.

        GLM-OCR doesn't return per-character confidence scores, so we estimate
        based on:
        - Text length (very short = low confidence)
        - Character distribution (too many special chars = low confidence)
        - Word structure (reasonable word lengths = high confidence)
        """
        if not text or len(text.strip()) < 5:
            return 0.0

        text = text.strip()

        # Base confidence - GLM-OCR is generally high quality
        confidence = 0.85

        # Bonus for substantial output
        if len(text) > 100:
            confidence += 0.05

        # Penalty for very short output
        if len(text) < 20:
            confidence -= 0.2

        # Penalty for high special character ratio
        special_chars = sum(1 for c in text if not c.isalnum() and not c.isspace())
        if len(text) > 0:
            special_ratio = special_chars / len(text)
            if special_ratio > 0.3:
                confidence -= 0.2

        # Penalty for fragmented text (many single-char words)
        words = text.split()
        if words:
            single_char_ratio = sum(1 for w in words if len(w) == 1) / len(words)
            if single_char_ratio > 0.4:
                confidence -= 0.15

        return max(0.0, min(1.0, confidence))

    def recognize_document_page(
        self,
        image_data: bytes,
        detect_tables: bool = True,
    ) -> str:
        """
        Recognize a full document page with automatic mode selection.

        Strategy:
        1. Run text recognition (primary)
        2. If tables detected in output, also run table recognition
        3. Return the best-quality result

        GLM-OCR handles multi-column layouts, headers, footers, and
        mixed content internally - no separate layout detection needed.

        Args:
            image_data: Image bytes of the document page
            detect_tables: Whether to attempt table detection

        Returns:
            Recognized text from the page
        """
        # Primary: text recognition
        text, confidence = self.recognize_text(image_data, mode="text")

        if not text:
            return ""

        # If tables might be present, try table recognition
        if detect_tables and self._might_contain_table(text):
            table_text, table_conf = self.recognize_text(image_data, mode="table")

            # Use table result if it's better structured
            if table_text and table_conf > confidence:
                logging.info("Using table recognition result (higher confidence)")
                return table_text

        return text

    def _might_contain_table(self, text: str) -> bool:
        """
        Heuristic to detect if text might contain tables.

        Looks for patterns like:
        - Pipe characters (markdown tables)
        - Tab-separated values
        - Aligned columns (multiple consecutive spaces)
        - Numeric patterns in columns
        """
        # Check for pipe characters (markdown tables)
        if '|' in text and text.count('|') > 4:
            return True

        # Check for tab-separated values
        if '\t' in text:
            return True

        # Check for aligned columns (multiple spaces between words)
        lines = text.split('\n')
        aligned_lines = sum(1 for line in lines if '   ' in line.strip())
        if aligned_lines > 3:
            return True

        return False


def check_ollama_status() -> Tuple[bool, str]:
    """
    Check if Ollama is running and GLM-OCR is available.

    Returns:
        Tuple of (is_ready, status_message)
    """
    if not OLLAMA_AVAILABLE:
        return False, "Ollama library not installed. Run: pip install ollama"

    try:
        client = Client()
        response = client.list()
        models = response.models if hasattr(response, 'models') else []
        model_names = []
        for m in models:
            name = getattr(m, 'model', None) or getattr(m, 'name', '')
            if name:
                model_names.append(name)

        if GLM_OCR_MODEL in model_names:
            return True, f"GLM-OCR ready ({GLM_OCR_MODEL})"
        elif GLM_OCR_MODEL_SMALL in model_names:
            return True, f"GLM-OCR ready ({GLM_OCR_MODEL_SMALL})"
        else:
            return False, f"GLM-OCR not installed. Run: ollama pull {GLM_OCR_MODEL}"

    except Exception as e:
        return False, f"Ollama not running: {e}. Start with: ollama serve"


def install_glm_ocr(
    progress_callback: Optional[Callable[[str, float], None]] = None,
) -> bool:
    """
    Install GLM-OCR model via Ollama.

    Args:
        progress_callback: Optional callback(status_msg, percent_complete)

    Returns:
        True if installation successful
    """
    if not OLLAMA_AVAILABLE:
        logging.error("Ollama library not installed")
        return False

    try:
        logging.info(f"Installing GLM-OCR model ({GLM_OCR_MODEL})...")

        # Ensure server is running
        if not OllamaServerManager.is_running():
            if not OllamaServerManager.start():
                logging.error("Cannot start Ollama server for model installation")
                return False

        client = Client()

        # Pull with progress logging
        for progress in client.pull(GLM_OCR_MODEL, stream=True):
            status = getattr(progress, 'status', '') or progress.get('status', '')
            completed = getattr(progress, 'completed', 0) or progress.get('completed', 0)
            total = getattr(progress, 'total', 0) or progress.get('total', 0)

            if total and completed:
                pct = completed / total * 100
                msg = f"{status}: {pct:.1f}%"
                logging.info(f"  {msg}")
                if progress_callback:
                    progress_callback(msg, pct)
            else:
                logging.info(f"  {status}")
                if progress_callback:
                    progress_callback(status, 0)

        logging.info("GLM-OCR installation complete")
        return True

    except Exception as e:
        capture_exception(
            e, context={"operation": "install_glm_ocr"}, tags={"component": "ocr"}
        )
        logging.error(f"Failed to install GLM-OCR: {e}")
        return False


# Convenience function for direct usage
def ocr_image(image_data: bytes, mode: str = "text") -> str:
    """
    Quick OCR function for single image.

    Args:
        image_data: Image bytes
        mode: "text", "table", or "figure"

    Returns:
        Recognized text
    """
    engine = GlmOcrEngine()
    text, _ = engine.recognize_text(image_data, mode)
    return text
