"""
Preprocessing robusto per pagine PDF da passare all'OCR (GLM-OCR/Ollama).

Due modalità:
- preprocess_page_from_pymupdf(page, ...): lavora direttamente sulla pagina PyMuPDF
  (usato dalla pipeline interna, evita riscrittura su disco)
- preprocess_pdf_page(pdf_path, page_num, ...): apre il PDF da disco
  (usato dagli script standalone)

Operazioni:
1. Renderizza pagina a DPI target (default 150)
2. Ritaglia bordi bianchi
3. Se troppo grande, riduce DPI e riprova
4. Se troppo piccola, aggiunge padding bianco
5. Converte in PNG RGB pulito
"""
import io
import logging
import tempfile

import numpy as np
import pymupdf
from PIL import Image

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Costanti
# ---------------------------------------------------------------------------
DEFAULT_DPI = 150
MIN_SIDE = 300    # pixel minimi per lato
MAX_SIDE = 2000   # pixel massimi per lato
WHITE_THRESHOLD = 240  # soglia per rilevare bordi bianchi


# ---------------------------------------------------------------------------
# Utilità immagine
# ---------------------------------------------------------------------------

def crop_white_borders(pil_img: Image.Image, threshold: int = WHITE_THRESHOLD) -> Image.Image:
    """Ritaglia bordi bianchi attorno al contenuto."""
    gray = pil_img.convert("L")
    arr = np.array(gray)
    mask = arr < threshold
    if not mask.any():
        return pil_img  # tutto bianco, non toccare
    coords = np.argwhere(mask)
    y0, x0 = coords.min(axis=0)
    y1, x1 = coords.max(axis=0) + 1
    return pil_img.crop((x0, y0, x1, y1))


def pad_to_min_size(pil_img: Image.Image, min_w: int = MIN_SIDE, min_h: int = MIN_SIDE) -> Image.Image:
    """Aggiunge padding bianco se l'immagine è più piccola del minimo."""
    w, h = pil_img.size
    if w >= min_w and h >= min_h:
        return pil_img
    new_w = max(w, min_w)
    new_h = max(h, min_h)
    padded = Image.new("RGB", (new_w, new_h), (255, 255, 255))
    padded.paste(pil_img, (0, 0))
    return padded


def resize_if_too_large(pil_img: Image.Image, max_w: int = MAX_SIDE, max_h: int = MAX_SIDE) -> Image.Image:
    """Ridimensiona proporzionalmente se supera le dimensioni massime."""
    w, h = pil_img.size
    if w <= max_w and h <= max_h:
        return pil_img
    ratio = min(max_w / w, max_h / h)
    new_w = int(w * ratio)
    new_h = int(h * ratio)
    return pil_img.resize((new_w, new_h), Image.LANCZOS)


# ---------------------------------------------------------------------------
# Rendering pagina -> PIL Image
# ---------------------------------------------------------------------------

def _render_page_to_pil(page: pymupdf.Page, dpi: int = DEFAULT_DPI) -> Image.Image:
    """Renderizza una pagina PyMuPDF come PIL Image RGB."""
    scale = dpi / 72.0
    mat = pymupdf.Matrix(scale, scale)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    return Image.frombytes("RGB", [pix.width, pix.height], pix.samples)


# ---------------------------------------------------------------------------
# Pipeline preprocessing completa
# ---------------------------------------------------------------------------

def _preprocess_image(
    img: Image.Image,
    crop_borders: bool = True,
    min_size: int = MIN_SIDE,
    max_size: int = MAX_SIDE,
) -> Image.Image:
    """Applica la pipeline di preprocessing a un'immagine PIL."""
    # 1. Crop bordi bianchi
    if crop_borders:
        img = crop_white_borders(img)

    # 2. Ridimensiona se troppo grande
    img = resize_if_too_large(img, max_size, max_size)

    # 3. Padding se troppo piccola
    img = pad_to_min_size(img, min_size, min_size)

    # 4. Assicura RGB (no alpha, no palette)
    if img.mode != "RGB":
        img = img.convert("RGB")

    return img


def preprocess_page_from_pymupdf(
    page: pymupdf.Page,
    dpi: int = DEFAULT_DPI,
    crop_borders: bool = True,
    min_size: int = MIN_SIDE,
    max_size: int = MAX_SIDE,
) -> tuple:
    """
    Preprocessa una pagina PyMuPDF per OCR.
    Lavora direttamente sulla pagina, senza scrivere/leggere PDF temporanei.

    Args:
        page: Oggetto pymupdf.Page
        dpi: DPI per il rendering (default 150)
        crop_borders: Se ritagliare bordi bianchi
        min_size: Dimensione minima lato (pixel)
        max_size: Dimensione massima lato (pixel)

    Returns:
        Tuple (png_bytes, info_dict) dove info_dict contiene:
        - width, height: dimensioni in pixel
        - dpi: DPI usato
        - mode: modalità colore
        - original_size: dimensioni originali prima del preprocessing
        - file_size_kb: dimensione PNG in KB
    """
    # Renderizza
    img = _render_page_to_pil(page, dpi)
    original_size = img.size

    # Preprocessing
    img = _preprocess_image(img, crop_borders, min_size, max_size)

    # Se dopo il preprocessing l'immagine è ancora troppo grande, riduci DPI
    w, h = img.size
    if (w > max_size or h > max_size) and dpi > 72:
        lower_dpi = max(72, int(dpi * 0.75))
        logger.info(f"Immagine troppo grande ({w}x{h}), riprovo con DPI {lower_dpi}")
        return preprocess_page_from_pymupdf(page, lower_dpi, crop_borders, min_size, max_size)

    # Converti in PNG bytes
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    png_bytes = buf.getvalue()

    info = {
        "width": img.size[0],
        "height": img.size[1],
        "dpi": dpi,
        "mode": img.mode,
        "original_size": original_size,
        "file_size_kb": round(len(png_bytes) / 1024, 1),
    }

    logger.info(
        f"Preprocessing OK: {info['width']}x{info['height']} px, "
        f"DPI={info['dpi']}, mode={info['mode']}, "
        f"file={info['file_size_kb']} KB "
        f"(originale: {original_size[0]}x{original_size[1]})"
    )

    return png_bytes, info


def preprocess_pdf_page(
    pdf_path: str,
    page_num: int = 0,
    dpi: int = DEFAULT_DPI,
    crop_borders: bool = True,
    min_size: int = MIN_SIDE,
    max_size: int = MAX_SIDE,
) -> tuple:
    """
    Preprocessa una pagina PDF da file per OCR (per uso standalone).

    Args:
        pdf_path: Percorso al file PDF
        page_num: Numero pagina (0-based)
        dpi, crop_borders, min_size, max_size: parametri preprocessing

    Returns:
        Tuple (png_path, info_dict)
    """
    doc = None
    try:
        doc = pymupdf.open(pdf_path)
        if page_num < 0 or page_num >= len(doc):
            raise IndexError(f"Pagina {page_num} fuori range (0-{len(doc)-1})")
        page = doc[page_num]
        png_bytes, info = preprocess_page_from_pymupdf(page, dpi, crop_borders, min_size, max_size)

        # Salva PNG temporaneo
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        tmp.write(png_bytes)
        tmp.close()

        info["png_path"] = tmp.name
        return tmp.name, info

    finally:
        if doc:
            doc.close()


# ---------------------------------------------------------------------------
# CLI standalone
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    if len(sys.argv) < 2:
        print("Uso: python -m app.core.preprocess_for_ocr file.pdf [pagina]")
        sys.exit(1)

    pdf = sys.argv[1]
    page = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    png_path, info = preprocess_pdf_page(pdf, page)
    print(f"PNG pronto per OCR: {png_path}")
    for k, v in info.items():
        print(f"  {k}: {v}")
