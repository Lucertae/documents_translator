#!/usr/bin/env python3
"""
Preprocessing avanzato per PDF scannerizzati da passare a OCR (GLM-OCR/Ollama).
- Estrae la pagina come immagine
- Ritaglia bordi bianchi
- Ridimensiona a DPI ottimale (default 150)
- Converte in PNG pulito (no alpha, no compressione strana)
- Se fallisce, riprova con DPI più basso o crop centrale
- Salva PNG temporanei pronti per OCR
"""
import pymupdf
from PIL import Image, ImageOps
import numpy as np
import os
import io
import tempfile

def crop_white_borders(pil_img, threshold=240):
    # Converte in scala di grigi e trova bounding box del contenuto
    gray = pil_img.convert('L')
    arr = np.array(gray)
    mask = arr < threshold
    if not mask.any():
        return pil_img  # tutto bianco
    coords = np.argwhere(mask)
    y0, x0 = coords.min(axis=0)
    y1, x1 = coords.max(axis=0) + 1
    cropped = pil_img.crop((x0, y0, x1, y1))
    return cropped

def preprocess_pdf_page(pdf_path, page_num=0, dpi=150, min_size=300, max_size=2000, crop_borders=True, try_smaller=True):
    """
    Estrae e normalizza una pagina PDF per OCR.
    Ritorna path PNG temporaneo pronto per OCR.
    """
    doc = pymupdf.open(pdf_path)
    page = doc[page_num]
    # Renderizza a DPI richiesto
    scale = dpi / 72
    mat = pymupdf.Matrix(scale, scale)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    if crop_borders:
        img = crop_white_borders(img)
    # Normalizza dimensioni
    w, h = img.size
    if w < min_size or h < min_size or w > max_size or h > max_size:
        # Prova a ridurre DPI se troppo grande
        if try_smaller and (w > max_size or h > max_size):
            return preprocess_pdf_page(pdf_path, page_num, dpi=int(dpi*0.75), min_size=min_size, max_size=max_size, crop_borders=crop_borders, try_smaller=False)
        # Prova crop centrale se troppo piccolo
        if w < min_size or h < min_size:
            crop = img.crop((0, 0, max(w, min_size), max(h, min_size)))
            img = crop
    # Salva PNG temporaneo
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    img.save(tmp, format='PNG')
    tmp.close()
    doc.close()
    return tmp.name

def preprocess_pdf_all(pdf_path, dpi=150, pages=None, **kwargs):
    """
    Preprocessa tutte (o una selezione di) pagine PDF, ritorna lista di PNG temporanei.
    """
    doc = pymupdf.open(pdf_path)
    n = len(doc)
    if pages is None:
        pages = range(n)
    out = []
    for p in pages:
        try:
            png = preprocess_pdf_page(pdf_path, p, dpi=dpi, **kwargs)
            out.append((p, png))
        except Exception as e:
            print(f"[ERRORE] Pagina {p+1} di {pdf_path}: {e}")
    doc.close()
    return out

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Uso: preprocess_pdf_for_ocr.py file.pdf [pagina]")
        sys.exit(1)
    pdf = sys.argv[1]
    page = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    out = preprocess_pdf_page(pdf, page)
    print(f"PNG pronto per OCR: {out}")
