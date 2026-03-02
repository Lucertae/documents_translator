"""
Modulo: preprocess_for_ocr.py
Preprocessing robusto per pagine PDF da passare all'OCR (GLM-OCR/Ollama).
"""
import tempfile
from PIL import Image
import numpy as np
import pymupdf

def crop_white_borders(pil_img, threshold=240):
    gray = pil_img.convert('L')
    arr = np.array(gray)
    mask = arr < threshold
    if not mask.any():
        return pil_img
    coords = np.argwhere(mask)
    y0, x0 = coords.min(axis=0)
    y1, x1 = coords.max(axis=0) + 1
    cropped = pil_img.crop((x0, y0, x1, y1))
    return cropped

def preprocess_pdf_page(pdf_path, page_num=0, dpi=150, min_size=300, max_size=2000, crop_borders=True, try_smaller=True):
    doc = pymupdf.open(pdf_path)
    page = doc[page_num]
    scale = dpi / 72
    mat = pymupdf.Matrix(scale, scale)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    if crop_borders:
        img = crop_white_borders(img)
    w, h = img.size
    if w < min_size or h < min_size or w > max_size or h > max_size:
        if try_smaller and (w > max_size or h > max_size):
            return preprocess_pdf_page(pdf_path, page_num, dpi=int(dpi*0.75), min_size=min_size, max_size=max_size, crop_borders=crop_borders, try_smaller=False)
        if w < min_size or h < min_size:
            crop = img.crop((0, 0, max(w, min_size), max(h, min_size)))
            img = crop
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    img.save(tmp, format='PNG')
    tmp.close()
    doc.close()
    return tmp.name
