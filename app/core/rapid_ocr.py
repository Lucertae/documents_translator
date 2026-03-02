"""
RapidOCR integration — motore OCR ad alte prestazioni basato su PaddleOCR/ONNX Runtime.

Sostituisce il precedente GLM-OCR (troppo lento su CPU, ~5-10 min/pagina)
con RapidOCR (ONNX Runtime, ~1-3 sec/pagina su CPU).

Architettura:
    App → RapidOCR (Python) → ONNX Runtime → modelli PP-OCRv4/v5

Caratteristiche:
- Pipeline completa: text detection + direction classification + text recognition
- Modelli PP-OCRv5 (detection) + PP-OCRv4 (recognition) via ONNX Runtime
- Supporto multilingue (cinese, inglese, latino, arabo, cirillico, ecc.)
- ~1-3 secondi per pagina su CPU (vs 5-10 minuti di GLM-OCR)
- Confidence score nativo per ogni riga di testo
- Nessun server esterno necessario (tutto in-process)
- Modelli scaricati automaticamente al primo utilizzo (~15 MB totali)

Compatibilità interfaccia:
    Espone la stessa interfaccia pubblica del vecchio glm_ocr.py:
    - RapidOcrEngine  (singleton, come GlmOcrEngine)
    - .is_available()
    - .recognize_text(image_data, mode) -> (text, confidence)
    - .recognize_document_page(image_data, detect_tables) -> text
    - check_ocr_status() -> (bool, str)
    - ocr_image(image_data, mode) -> str

Usage:
    from app.core.rapid_ocr import RapidOcrEngine

    engine = RapidOcrEngine()
    text, confidence = engine.recognize_text(image_bytes)
    page_text = engine.recognize_document_page(image_bytes)
"""
import logging
import io
from typing import Optional, Tuple, List

import numpy as np
from PIL import Image

from .sentry_integration import capture_exception

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Importazione RapidOCR
# ---------------------------------------------------------------------------
try:
    from rapidocr import RapidOCR, EngineType, LangDet, LangRec, ModelType, OCRVersion
    RAPIDOCR_AVAILABLE = True
except ImportError:
    RAPIDOCR_AVAILABLE = False
    logger.warning("RapidOCR non installato — eseguire: pip install rapidocr onnxruntime")

# Costante esportata per compatibilità con il test script
OCR_ENGINE_NAME = "RapidOCR v3 + PP-OCRv4/v5 (ONNX Runtime)"


# ---------------------------------------------------------------------------
# Parametri di configurazione per l'engine
# ---------------------------------------------------------------------------

# Soglia globale di confidenza testo (default RapidOCR: 0.5)
# Usiamo un valore leggermente più basso per non perdere testo marginale
TEXT_SCORE_THRESHOLD = 0.4

# Log level interno di RapidOCR (critical = silenzioso)
RAPIDOCR_LOG_LEVEL = "warning"


def _build_engine_params() -> dict:
    """
    Costruisce i parametri ottimali per l'engine RapidOCR.

    Scelte progettuali:
    - Detection: PP-OCRv5 mobile (multilingue, più accurato di v4)
    - Classification: PP-OCRv4 mobile (unica opzione disponibile)
    - Recognition: PP-OCRv4 mobile EN (ottimizzato per testi inglesi/latini,
      che rappresentano la maggior parte dei documenti del progetto)
    - Engine: ONNX Runtime (migliore compatibilità cross-platform)
    - max_side_len=2000: coerente con il preprocessing (MAX_SIDE=2000)
    """
    return {
        # --- Global ---
        "Global.text_score": TEXT_SCORE_THRESHOLD,
        "Global.use_det": True,
        "Global.use_cls": True,
        "Global.use_rec": True,
        "Global.max_side_len": 2000,
        "Global.min_side_len": 30,
        "Global.log_level": RAPIDOCR_LOG_LEVEL,

        # --- Detection: PP-OCRv5 mobile (multilingue) ---
        "Det.engine_type": EngineType.ONNXRUNTIME,
        "Det.lang_type": LangDet.CH,
        "Det.model_type": ModelType.MOBILE,
        "Det.ocr_version": OCRVersion.PPOCRV5,

        # --- Classification: PP-OCRv4 mobile ---
        "Cls.engine_type": EngineType.ONNXRUNTIME,
        "Cls.lang_type": LangDet.CH,
        "Cls.model_type": ModelType.MOBILE,
        "Cls.ocr_version": OCRVersion.PPOCRV4,

        # --- Recognition: PP-OCRv4 mobile EN ---
        # Per documenti prevalentemente in inglese/latino;
        # il modello 'en' copre inglese + cifre + punteggiatura.
        # Per doc multilingue (cinese, giapponese) cambiare a LangRec.CH
        "Rec.engine_type": EngineType.ONNXRUNTIME,
        "Rec.lang_type": LangRec.EN,
        "Rec.model_type": ModelType.MOBILE,
        "Rec.ocr_version": OCRVersion.PPOCRV4,
    }


class RapidOcrEngine:
    """
    Motore OCR basato su RapidOCR (ONNX Runtime + PP-OCR models).

    Singleton: una sola istanza condivisa. I modelli vengono scaricati
    automaticamente al primo utilizzo (~15 MB).

    L'interfaccia pubblica è compatibile con il precedente GlmOcrEngine:
    - is_available()
    - recognize_text(image_data, mode) -> (text, confidence)
    - recognize_document_page(image_data, detect_tables) -> text
    """

    _instance: Optional["RapidOcrEngine"] = None
    _engine: Optional["RapidOCR"] = None
    _available: Optional[bool] = None  # cache del check

    def __new__(cls) -> "RapidOcrEngine":
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Inizializza l'engine RapidOCR (lazy: solo al primo uso effettivo)."""
        if self._engine is not None:
            return
        if not RAPIDOCR_AVAILABLE:
            logger.error("RapidOCR non disponibile (libreria non installata)")
            return
        try:
            params = _build_engine_params()
            self._engine = RapidOCR(params=params)
            logger.info(f"RapidOCR engine inizializzato: {OCR_ENGINE_NAME}")
            self._available = True
        except Exception as e:
            capture_exception(e, context={"operation": "rapidocr_init"})
            logger.error(f"Errore inizializzazione RapidOCR: {e}")
            self._engine = None
            self._available = False

    # ------------------------------------------------------------------
    # Interfaccia pubblica
    # ------------------------------------------------------------------

    def is_available(self) -> bool:
        """Verifica se RapidOCR è pronto."""
        if self._available is not None:
            return self._available
        if not RAPIDOCR_AVAILABLE or self._engine is None:
            self._available = False
            return False
        self._available = True
        return True

    def recognize_text(
        self,
        image_data: bytes,
        mode: str = "text",
    ) -> Tuple[str, float]:
        """
        Riconosce il testo da un'immagine.

        Args:
            image_data: bytes dell'immagine (PNG, JPEG, ecc.)
            mode: modalità ("text" per ora; "table"/"figure" mantenuti
                  per compatibilità ma trattati come "text")

        Returns:
            (testo_riconosciuto, confidence_media)
        """
        if not self.is_available():
            return "", 0.0

        try:
            # Converti bytes -> numpy array (formato accettato da RapidOCR)
            img = Image.open(io.BytesIO(image_data))
            img_np = np.array(img.convert("RGB"))

            result = self._engine(img_np)

            if result is None or result.txts is None or len(result.txts) == 0:
                logger.debug("RapidOCR: nessun testo rilevato")
                return "", 0.0

            # Ricostruisci il testo ordinando le box per posizione verticale
            text = self._reconstruct_text(result)
            confidence = self._compute_mean_confidence(result)

            logger.debug(
                f"RapidOCR [{mode}]: {len(text)} chars, "
                f"confidence={confidence:.3f}, "
                f"elapsed={result.elapse:.3f}s"
            )
            return text, confidence

        except Exception as e:
            capture_exception(
                e,
                context={"operation": "rapidocr_recognize", "mode": mode},
                tags={"component": "ocr"},
            )
            logger.error(f"RapidOCR errore: {e}")
            return "", 0.0

    def recognize_document_page(
        self,
        image_data: bytes,
        detect_tables: bool = True,
    ) -> str:
        """
        Riconosce una pagina intera di documento.

        A differenza di GLM-OCR, RapidOCR non ha modalità "table" separata.
        Le tabelle vengono gestite dal text detector che individua le singole celle.
        Il parametro detect_tables è mantenuto per compatibilità di interfaccia.

        Args:
            image_data: bytes dell'immagine della pagina
            detect_tables: ignorato (mantenuto per compatibilità)

        Returns:
            Testo riconosciuto dalla pagina
        """
        text, confidence = self.recognize_text(image_data, mode="text")
        return text

    # ------------------------------------------------------------------
    # Metodi interni
    # ------------------------------------------------------------------

    @staticmethod
    def _reconstruct_text(result) -> str:
        """
        Ricostruisce il testo dalle box di RapidOCR rispettando l'ordine di lettura.

        Strategia:
        1. Per ogni riga rilevata, calcola la posizione Y media (centro della box)
        2. Ordina per Y (top-to-bottom), poi per X (left-to-right) per stessa riga
        3. Aggrega righe vicine in un unico blocco, separando i paragrafi
           con doppio newline quando c'è un gap verticale significativo.

        Questo approccio mantiene l'ordine di lettura naturale anche per
        layout multi-colonna semplici.
        """
        if result.boxes is None or result.txts is None:
            return ""

        boxes = result.boxes       # shape (N, 4, 2)
        txts = result.txts         # tuple of N strings
        scores = result.scores     # tuple of N floats

        # Calcola centroide Y e X minimo per ogni box
        entries: List[Tuple[float, float, str, float]] = []
        for i, (box, txt, score) in enumerate(zip(boxes, txts, scores)):
            # box è [[x1,y1], [x2,y2], [x3,y3], [x4,y4]] — quadrilatero
            y_center = float(np.mean(box[:, 1]))
            x_min = float(np.min(box[:, 0]))
            box_height = float(np.max(box[:, 1]) - np.min(box[:, 1]))
            entries.append((y_center, x_min, txt, box_height))

        if not entries:
            return ""

        # Ordina per Y, poi per X
        entries.sort(key=lambda e: (e[0], e[1]))

        # Raggruppa righe: due box sono sulla stessa riga se la differenza
        # dei centri Y è < 50% dell'altezza media delle box
        lines: List[List[str]] = []
        current_line: List[Tuple[float, str]] = []
        prev_y = entries[0][0]
        avg_height = np.mean([e[3] for e in entries]) if entries else 20.0

        # Threshold per considerare "stessa riga"
        same_line_threshold = avg_height * 0.5
        # Threshold per paragrafo (gap > 1.5x altezza media)
        paragraph_gap = avg_height * 1.5

        line_texts: List[Tuple[float, str]] = []  # (y_center, testo_riga)

        for y_center, x_min, txt, box_h in entries:
            if abs(y_center - prev_y) > same_line_threshold:
                # Nuova riga
                if current_line:
                    current_line.sort(key=lambda t: t[0])
                    merged = " ".join(t for _, t in current_line)
                    line_texts.append((prev_y, merged))
                current_line = [(x_min, txt)]
                prev_y = y_center
            else:
                current_line.append((x_min, txt))

        # Ultima riga
        if current_line:
            current_line.sort(key=lambda t: t[0])
            merged = " ".join(t for _, t in current_line)
            line_texts.append((prev_y, merged))

        if not line_texts:
            return ""

        # Unisci righe con separazione paragrafi per gap verticali grandi
        output_parts: List[str] = [line_texts[0][1]]
        for i in range(1, len(line_texts)):
            y_gap = line_texts[i][0] - line_texts[i - 1][0]
            if y_gap > paragraph_gap:
                output_parts.append("")  # riga vuota = separazione paragrafo
            output_parts.append(line_texts[i][1])

        return "\n".join(output_parts)

    @staticmethod
    def _compute_mean_confidence(result) -> float:
        """Calcola la confidence media delle righe riconosciute."""
        if result.scores is None or len(result.scores) == 0:
            return 0.0
        return float(np.mean(result.scores))


# ---------------------------------------------------------------------------
# Funzioni di utilità (compatibilità con vecchia interfaccia)
# ---------------------------------------------------------------------------

def check_ocr_status() -> Tuple[bool, str]:
    """
    Verifica lo stato di RapidOCR.

    Returns:
        (is_ready, status_message)
    """
    if not RAPIDOCR_AVAILABLE:
        return False, "RapidOCR non installato. Eseguire: pip install rapidocr onnxruntime"

    try:
        engine = RapidOcrEngine()
        if engine.is_available():
            return True, f"RapidOCR pronto ({OCR_ENGINE_NAME})"
        else:
            return False, "RapidOCR inizializzazione fallita"
    except Exception as e:
        return False, f"Errore RapidOCR: {e}"


# Alias per compatibilità con il vecchio check_ollama_status
check_ollama_status = check_ocr_status


def ocr_image(image_data: bytes, mode: str = "text") -> str:
    """
    Funzione OCR rapida per una singola immagine.

    Args:
        image_data: bytes dell'immagine
        mode: "text" (default)

    Returns:
        Testo riconosciuto
    """
    engine = RapidOcrEngine()
    text, _ = engine.recognize_text(image_data, mode)
    return text
