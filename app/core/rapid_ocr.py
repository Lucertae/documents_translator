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
OCR_ENGINE_NAME = "RapidOCR v3 + PP-OCRv5 det + PP-OCRv4 LATIN SERVER rec (ONNX Runtime)"


# ---------------------------------------------------------------------------
# Parametri di configurazione per l'engine
# ---------------------------------------------------------------------------

# Soglia globale di confidenza testo (default RapidOCR: 0.5)
# Usiamo un valore più basso per non perdere testo marginale (titoli chiari, note a piè di pagina)
TEXT_SCORE_THRESHOLD = 0.3

# Log level interno di RapidOCR (critical = silenzioso)
RAPIDOCR_LOG_LEVEL = "warning"


def _build_engine_params() -> dict:
    """
    Costruisce i parametri ottimali per l'engine RapidOCR.

    Scelte progettuali:
    - Detection: PP-OCRv5 MOBILE (veloce, buona qualità su layout complessi)
    - Classification: PP-OCRv4 mobile (unica opzione disponibile)
    - Recognition: PP-OCRv4 SERVER LATIN (copre tutte le lingue latine: EN, IT, FR, DE, ES...)
    - Engine: ONNX Runtime (migliore compatibilità cross-platform)
    - max_side_len=3000: coerente con il preprocessing (MAX_SIDE=3000) e DPI 300
    - text_score=0.3: permissivo per non perdere testo marginale

    Miglioramenti rispetto alla configurazione precedente:
    - DPI: 150 → 300 (migliore risoluzione = migliore riconoscimento)
    - Detection model: MOBILE v5 (buon bilanciamento velocità/qualità)
    - Recognition model: EN MOBILE → LATIN SERVER (copre italiano + inglese, più accurato)
    - max_side_len: 2000 → 3000 (supporta immagini più grandi da 300 DPI)
    - text_score: 0.4 → 0.3 (più permissivo per catturare testo marginale)
    - box_thresh: 0.5 → 0.6 (filtra detections deboli da watermark/rumore)

    Nota: PP-OCRv5 detection disponibile solo con lang_type CH (non EN/MULTI).
    Testato: CH v5 è superiore a EN v4 e MULTI v4 per keyword recall su documenti legali.
    """
    return {
        # --- Global ---
        "Global.text_score": TEXT_SCORE_THRESHOLD,
        "Global.use_det": True,
        "Global.use_cls": True,
        "Global.use_rec": True,
        "Global.max_side_len": 3000,
        "Global.min_side_len": 30,
        "Global.log_level": RAPIDOCR_LOG_LEVEL,

        # --- Detection: PP-OCRv5 MOBILE (veloce + accurato) ---
        # box_thresh=0.6: filtra detections deboli da watermark/rumore (default 0.5)
        # Benchmark: +2% confidence senza perdita di keyword recall
        "Det.engine_type": EngineType.ONNXRUNTIME,
        "Det.lang_type": LangDet.CH,
        "Det.model_type": ModelType.MOBILE,
        "Det.ocr_version": OCRVersion.PPOCRV5,
        "Det.box_thresh": 0.6,

        # --- Classification: PP-OCRv4 mobile ---
        "Cls.engine_type": EngineType.ONNXRUNTIME,
        "Cls.lang_type": LangDet.CH,
        "Cls.model_type": ModelType.MOBILE,
        "Cls.ocr_version": OCRVersion.PPOCRV4,

        # --- Recognition: PP-OCRv4 SERVER LATIN ---
        # 'latin' copre inglese + italiano + tutte le lingue latine
        # SERVER model è più accurato di MOBILE per testo fine
        "Rec.engine_type": EngineType.ONNXRUNTIME,
        "Rec.lang_type": LangRec.LATIN,
        "Rec.model_type": ModelType.SERVER,
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

    @classmethod
    def reset(cls) -> None:
        """Reset singleton state. Necessario quando si cambiano i parametri dell'engine."""
        cls._instance = None
        cls._engine = None
        cls._available = None

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
    def _detect_columns(entries: list, page_width: float) -> list:
        """
        Rileva le colonne del documento analizzando i gap tra box riga per riga.

        Algoritmo robusto basato sulla consistenza verticale dei gap:
        1. Raggruppa le box in righe orizzontali (stessa Y)
        2. Per ogni riga, trova i gap tra box consecutive (ordinate per X)
        3. Istogramma dei gap per posizione X: un gap che appare costantemente
           alla stessa posizione X in molte righe è un separatore di colonna
        4. Le colonne sono definite dagli intervalli tra i separatori

        Questo rileva sia layout a 2 colonne che a 4 colonne (es. contratti legali
        con sub-colonne), e gestisce anche layout single-column.

        Returns:
            Lista di tuple (x_start, x_end) per ogni colonna rilevata.
            Se layout single-column, ritorna [(0, page_width)].
        """
        if not entries or page_width <= 0:
            return [(0, page_width)]

        avg_height = float(np.mean([e[3] for e in entries])) if entries else 20.0

        # --- Passo 1: Raggruppa box in righe orizzontali ---
        same_line_threshold = avg_height * 0.5
        sorted_entries = sorted(entries, key=lambda e: e[0])

        lines = []
        current_line = [sorted_entries[0]]
        for e in sorted_entries[1:]:
            if abs(e[0] - current_line[0][0]) <= same_line_threshold:
                current_line.append(e)
            else:
                lines.append(current_line)
                current_line = [e]
        if current_line:
            lines.append(current_line)

        if len(lines) < 3:
            return [(0, page_width)]

        # --- Passo 2: Per ogni riga, trova i gap tra box consecutive ---
        # Un gap è definito come spazio vuoto tra x_max di una box e x_min della successiva
        min_gap_size = avg_height * 1.5  # Il gap deve essere almeno 1.5x l'altezza del testo

        n_buckets = 200
        bucket_width = page_width / n_buckets
        gap_histogram = [0] * n_buckets

        for line in lines:
            if len(line) < 2:
                continue
            # Ordina box nella riga per x_min
            sorted_by_x = sorted(line, key=lambda e: e[1])
            for j in range(len(sorted_by_x) - 1):
                x_max_curr = sorted_by_x[j][4]   # x_max della box corrente
                x_min_next = sorted_by_x[j + 1][1]  # x_min della box successiva
                gap_size = x_min_next - x_max_curr

                if gap_size >= min_gap_size:
                    # Registra il centro del gap nell'istogramma
                    gap_center = (x_max_curr + x_min_next) / 2.0
                    bucket_idx = min(n_buckets - 1, max(0, int(gap_center / bucket_width)))
                    gap_histogram[bucket_idx] += 1

        # --- Passo 3: Trova picchi nell'istogramma (posizioni con gap consistenti) ---
        # Un gap è "consistente" se appare in almeno il 25% delle righe multi-box
        multi_box_lines = sum(1 for line in lines if len(line) >= 2)
        if multi_box_lines < 3:
            return [(0, page_width)]

        min_count = max(3, int(multi_box_lines * 0.25))

        # Somma bucket adiacenti (smoothing con finestra di 5 bucket)
        smoothed = [0] * n_buckets
        for i in range(n_buckets):
            window_start = max(0, i - 2)
            window_end = min(n_buckets, i + 3)
            smoothed[i] = sum(gap_histogram[window_start:window_end])

        # Trova picchi (bucket con conteggio >= soglia)
        peak_buckets = [i for i in range(n_buckets) if smoothed[i] >= min_count]

        if not peak_buckets:
            return [(0, page_width)]

        # Mergi picchi adiacenti (entro 3% della larghezza pagina)
        merge_distance = max(3, int(0.03 * n_buckets))
        merged_peaks = []
        current_peak_start = peak_buckets[0]
        current_peak_end = peak_buckets[0]

        for b in peak_buckets[1:]:
            if b - current_peak_end <= merge_distance:
                current_peak_end = b
            else:
                # Media del range come posizione del picco
                merged_peaks.append((current_peak_start + current_peak_end) / 2.0)
                current_peak_start = b
                current_peak_end = b

        merged_peaks.append((current_peak_start + current_peak_end) / 2.0)

        if not merged_peaks:
            return [(0, page_width)]

        # --- Passo 4: Converti picchi in confini di colonna ---
        column_boundaries = [p * bucket_width for p in merged_peaks]

        # Filtra separatori troppo vicini ai bordi della pagina (< 5% o > 95%)
        margin = page_width * 0.05
        column_boundaries = [b for b in column_boundaries if margin < b < page_width - margin]

        if not column_boundaries:
            return [(0, page_width)]

        # Costruisci colonne
        columns = []
        col_start = 0
        for boundary in column_boundaries:
            columns.append((col_start, boundary))
            col_start = boundary
        columns.append((col_start, page_width))

        # --- Passo 5: Validazione ---
        # Ogni colonna deve avere una larghezza ragionevole (almeno 8% della pagina)
        min_col_width = page_width * 0.08
        valid_columns = []
        for col in columns:
            if col[1] - col[0] >= min_col_width:
                valid_columns.append(col)
            elif valid_columns:
                # Mergi colonna troppo stretta con la precedente
                prev = valid_columns[-1]
                valid_columns[-1] = (prev[0], col[1])
            else:
                valid_columns.append(col)

        if len(valid_columns) <= 1:
            return [(0, page_width)]

        # Verifica che ogni colonna contenga un numero sufficiente di box
        min_entries_per_col = max(3, len(entries) * 0.05)
        populated_columns = []
        for col_start, col_end in valid_columns:
            count = sum(
                1 for e in entries
                if e[1] >= col_start - avg_height and e[4] <= col_end + avg_height
            )
            if count >= min_entries_per_col:
                populated_columns.append((col_start, col_end))

        if len(populated_columns) <= 1:
            return [(0, page_width)]

        logger.debug(
            f"Column detection: {len(populated_columns)} columns found: "
            f"{[(f'{c[0]:.0f}-{c[1]:.0f}') for c in populated_columns]}"
        )
        return populated_columns

    @staticmethod
    def _assign_to_column(x_min: float, x_max: float, columns: list) -> int:
        """
        Assegna una box alla colonna con la massima sovrapposizione.
        """
        best_col = 0
        best_overlap = 0

        for i, (col_start, col_end) in enumerate(columns):
            overlap_start = max(x_min, col_start)
            overlap_end = min(x_max, col_end)
            overlap = max(0, overlap_end - overlap_start)
            if overlap > best_overlap:
                best_overlap = overlap
                best_col = i

        return best_col

    @staticmethod
    def _reconstruct_text(result) -> str:
        """
        Ricostruisce il testo dalle box di RapidOCR rispettando l'ordine di lettura
        con supporto per layout multi-colonna.

        Strategia:
        1. Per ogni box, calcola le coordinate (y_center, x_min, x_max, height)
        2. Rileva automaticamente la struttura a colonne della pagina
        3. Se multi-colonna: legge prima tutta la colonna 1 (top-to-bottom),
           poi tutta la colonna 2, ecc.
        4. Dentro ogni colonna, raggruppa le box sulla stessa riga
           e ordina per X (left-to-right)
        5. Separa i paragrafi quando c'è un gap verticale significativo

        Questo approccio gestisce correttamente:
        - Layout single-column (documenti, lettere, articoli)
        - Layout multi-colonna (contratti legali, riviste, giornali)
        - Layout misti (titolo a larghezza piena + corpo a 2 colonne)
        """
        if result.boxes is None or result.txts is None:
            return ""

        boxes = result.boxes       # shape (N, 4, 2)
        txts = result.txts         # tuple of N strings
        scores = result.scores     # tuple of N floats

        # Calcola coordinate per ogni box
        # (y_center, x_min, txt, box_height, x_max)
        entries: List[Tuple[float, float, str, float, float]] = []
        for i, (box, txt, score) in enumerate(zip(boxes, txts, scores)):
            y_center = float(np.mean(box[:, 1]))
            x_min = float(np.min(box[:, 0]))
            x_max = float(np.max(box[:, 0]))
            box_height = float(np.max(box[:, 1]) - np.min(box[:, 1]))
            entries.append((y_center, x_min, txt, box_height, x_max))

        if not entries:
            return ""

        page_width = max(e[4] for e in entries)
        avg_height = float(np.mean([e[3] for e in entries])) if entries else 20.0

        # --- Rileva colonne ---
        columns = RapidOcrEngine._detect_columns(entries, page_width)
        is_multicolumn = len(columns) > 1

        if is_multicolumn:
            logger.info(f"Multi-column layout detected: {len(columns)} columns")

        # --- Assegna ogni box a una colonna ---
        column_entries: List[List[Tuple[float, float, str, float]]] = [
            [] for _ in columns
        ]

        # Identifica box che attraversano più colonne (es. titoli full-width)
        full_width_entries: List[Tuple[float, float, str, float]] = []

        for y_center, x_min, txt, box_h, x_max in entries:
            if is_multicolumn:
                box_width = x_max - x_min
                # Una box è "full-width" se copre almeno il 70% della larghezza pagina
                if box_width > page_width * 0.70:
                    full_width_entries.append((y_center, x_min, txt, box_h))
                    continue

            col_idx = RapidOcrEngine._assign_to_column(x_min, x_max, columns)
            column_entries[col_idx].append((y_center, x_min, txt, box_h))

        # --- Ricostruisci testo per ogni colonna ---
        def _build_column_text(
            col_entries: List[Tuple[float, float, str, float]],
            avg_h: float,
        ) -> List[Tuple[float, str]]:
            """
            Costruisce il testo di una colonna raggruppando righe vicine.
            Ritorna lista di (y_center, line_text).
            """
            if not col_entries:
                return []

            # Ordina per Y, poi per X
            col_entries.sort(key=lambda e: (e[0], e[1]))

            same_line_threshold = avg_h * 0.5
            paragraph_gap = avg_h * 1.5

            line_texts: List[Tuple[float, str]] = []
            current_line: List[Tuple[float, str]] = []
            prev_y = col_entries[0][0]

            for y_center, x_min, txt, box_h in col_entries:
                if abs(y_center - prev_y) > same_line_threshold:
                    if current_line:
                        current_line.sort(key=lambda t: t[0])
                        merged = " ".join(t for _, t in current_line)
                        line_texts.append((prev_y, merged))
                    current_line = [(x_min, txt)]
                    prev_y = y_center
                else:
                    current_line.append((x_min, txt))

            if current_line:
                current_line.sort(key=lambda t: t[0])
                merged = " ".join(t for _, t in current_line)
                line_texts.append((prev_y, merged))

            return line_texts

        # --- Assemblaggio finale ---
        all_output_parts: List[str] = []

        if is_multicolumn:
            # Multi-colonna: emetti full-width, poi colonne in ordine
            # Raccogli full-width entries con il loro y per collocarle correttamente
            fw_lines = _build_column_text(full_width_entries, avg_height)
            col_line_groups = [
                _build_column_text(column_entries[i], avg_height)
                for i in range(len(columns))
            ]

            # Determina la Y range per le colonne
            # Full-width lines che precedono le colonne vanno prima
            col_y_min = float('inf')
            col_y_max = float('-inf')
            for col_lines in col_line_groups:
                if col_lines:
                    col_y_min = min(col_y_min, col_lines[0][0])
                    col_y_max = max(col_y_max, col_lines[-1][0])

            # Emetti: header full-width → colonne → footer full-width
            paragraph_gap = avg_height * 1.5

            # Header full-width (prima delle colonne)
            for y, txt in fw_lines:
                if y < col_y_min - avg_height:
                    all_output_parts.append(txt)

            if all_output_parts:
                all_output_parts.append("")  # separatore

            # Colonne: leggi ogni colonna completamente, poi la successiva
            for col_idx, col_lines in enumerate(col_line_groups):
                if not col_lines:
                    continue

                if col_idx > 0:
                    all_output_parts.append("")  # separatore tra colonne

                prev_y_line = col_lines[0][0]
                for line_idx, (y, txt) in enumerate(col_lines):
                    if line_idx > 0:
                        y_gap = y - prev_y_line
                        if y_gap > paragraph_gap:
                            all_output_parts.append("")
                    all_output_parts.append(txt)
                    prev_y_line = y

            # Footer full-width (dopo le colonne)
            footer_parts = []
            for y, txt in fw_lines:
                if y > col_y_max + avg_height:
                    footer_parts.append(txt)

            if footer_parts:
                all_output_parts.append("")
                all_output_parts.extend(footer_parts)
        else:
            # Single column: logica originale
            line_texts = _build_column_text(
                [(y, x, t, h) for y, x, t, h, _ in entries],
                avg_height,
            )
            paragraph_gap = avg_height * 1.5

            if line_texts:
                all_output_parts.append(line_texts[0][1])
                for i in range(1, len(line_texts)):
                    y_gap = line_texts[i][0] - line_texts[i - 1][0]
                    if y_gap > paragraph_gap:
                        all_output_parts.append("")
                    all_output_parts.append(line_texts[i][1])

        return "\n".join(all_output_parts)

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
# TODO: rimuovere quando tutti i chiamanti saranno aggiornati
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
