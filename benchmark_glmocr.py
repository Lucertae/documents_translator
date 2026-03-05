#!/usr/bin/env python3
"""
Benchmark OCR GLM-OCR (Ollama) su PDF scannerizzati.
Estrae 3 pagine per documento, normalizza la risoluzione, salva PNG temporanei e lancia OCR.
"""
import pymupdf
import base64
import ollama
import time
import os
import sys

def optimal_scale(dpi, target=150):
    if dpi < target:
        return target / dpi
    if dpi > 2*target:
        return target / dpi
    return 1.0

def extract_and_ocr(pdf_path, pages=[0,1,2], target_dpi=150):
    print(f"\n{'='*60}\n{pdf_path}\n{'='*60}")
    doc = pymupdf.open(pdf_path)
    for page_num in pages:
        if page_num >= len(doc):
            continue
        page = doc[page_num]
        imgs = page.get_images(full=True)
        # Stima DPI
        if imgs:
            xref = imgs[0][0]
            img = doc.extract_image(xref)
            w, h = img['width'], img['height']
            bbox = page.rect
            dpi_x = int(w / (bbox.width / 72))
            scale = optimal_scale(dpi_x, target_dpi)
        else:
            scale = 2.0  # fallback
        # Renderizza
        mat = pymupdf.Matrix(scale, scale)
        pix = page.get_pixmap(matrix=mat)
        img_bytes = pix.tobytes("png")
        img_b64 = base64.b64encode(img_bytes).decode()
        print(f"\n--- Pagina {page_num+1}/{len(doc)} ---")
        print(f"DPI stimato: {dpi_x if imgs else 'N/A'} | Scala: {scale:.2f}")
        print(f"Immagine: {pix.width}x{pix.height} px ({len(img_bytes):,} bytes)")
        # OCR
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
        print(f"Tempo: {elapsed:.1f}s | Caratteri: {len(text)}")
        print(f"Output: {text[:200].replace(chr(10),' ')}{' ...' if len(text)>200 else ''}")
    doc.close()

if __name__ == "__main__":
    pdfs = [
        "input/2015.129351.Bibliography-Of-Doctoral-Dissertations_text.pdf",
        "input/V. S. Vladimirov - Equations of mathematical physics b.pdf",
        "input/confidenziali/1.pdf",
        "input/confidenziali/DOC040625-04062025140056.pdf",
        "input/confidenziali/Distribution Contract Trotec Bompan SRL_01062024_signed both parties.pdf",
        "input/confidenziali/Signed_FY2025_2027_Authorized_Distribution_Agreement_Distributor.pdf",
        "input/sim_economist_1881-08-06_39_1980.pdf",
        "input/sim_quarterly-journal-of-economics_1980_94_contents.pdf",
    ]
    for pdf in pdfs:
        try:
            extract_and_ocr(pdf, pages=[0,1,2])
        except Exception as e:
            print(f"[ERRORE] {pdf}: {e}")
        sys.stdout.flush()
