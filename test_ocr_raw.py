#!/usr/bin/env python3
"""Test GLM-OCR puro su documenti scannerizzati - nessuna dipendenza dal progetto."""

import pymupdf
import base64
import ollama
import time
import sys

def test_page(pdf_path: str, page_num: int = 0):
    """Testa OCR su una singola pagina."""
    print(f"\n{'='*60}")
    print(f"FILE: {pdf_path}")
    print(f"PAGE: {page_num}")
    print(f"{'='*60}")
    
    doc = pymupdf.open(pdf_path)
    page = doc[page_num]
    
    # Render at 2x (144 DPI)
    mat = pymupdf.Matrix(2.0, 2.0)
    pix = page.get_pixmap(matrix=mat)
    img_bytes = pix.tobytes("png")
    img_b64 = base64.b64encode(img_bytes).decode()
    
    print(f"Page size: {page.rect.width:.0f}x{page.rect.height:.0f} pts")
    print(f"Image: {pix.width}x{pix.height} px ({len(img_bytes):,} bytes)")
    
    native_text = page.get_text().strip()
    print(f"Native text: {len(native_text)} chars")
    
    # GLM-OCR - Text Recognition
    print(f"\n--- GLM-OCR Text Recognition ---")
    start = time.time()
    response = ollama.chat(
        model="glm-ocr",
        messages=[{
            "role": "user",
            "content": "Text Recognition:",
            "images": [img_b64]
        }],
        options={"temperature": 0.1, "num_predict": 16384}
    )
    elapsed = time.time() - start
    
    text = response.message.content
    print(f"Time: {elapsed:.1f}s")
    print(f"Characters: {len(text)}")
    print(f"\n--- OUTPUT ---")
    print(text[:3000])  # Cap output for readability
    if len(text) > 3000:
        print(f"\n... [truncated, {len(text)} total chars]")
    print(f"--- END ---\n")
    
    doc.close()
    return text


if __name__ == "__main__":
    # Test su diversi tipi di documento
    tests = [
        ("input/confidenziali/DOC040625-04062025140056.pdf", 0),  # Scan puro 
        ("input/confidenziali/1.pdf", 0),                          # Scan con tante immagini
        ("input/sim_economist_1881-08-06_39_1980.pdf", 1),         # Giornale storico
    ]
    
    for pdf_path, page_num in tests:
        try:
            test_page(pdf_path, page_num)
        except Exception as e:
            print(f"ERROR on {pdf_path}: {e}")
        sys.stdout.flush()
