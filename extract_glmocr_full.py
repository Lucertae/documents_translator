#!/usr/bin/env python3
"""
Estrae il testo OCR completo (GLM-OCR via Ollama) per 3 pagine di ciascun PDF scannerizzato.
Salva ogni output in un file txt per documento.
"""
import pymupdf
import base64
import ollama
import time
import os
import sys

def extract_and_save(pdf_path, pages=[0,1,2], target_dpi=150):
    doc = pymupdf.open(pdf_path)
    out_txt = os.path.splitext(os.path.basename(pdf_path))[0] + "_glmocr.txt"
    with open(out_txt, "w", encoding="utf-8") as f:
        for page_num in pages:
            if page_num >= len(doc):
                continue
            page = doc[page_num]
            # Forza sempre 150 DPI
            bbox = page.rect
            scale = 150 / 72  # 150 DPI rispetto ai 72pt PDF
            mat = pymupdf.Matrix(scale, scale)
            pix = page.get_pixmap(matrix=mat)
            img_bytes = pix.tobytes("png")
            img_b64 = base64.b64encode(img_bytes).decode()
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
            f.write(f"\n--- Pagina {page_num+1}/{len(doc)} ---\n")
            f.write(f"Tempo: {elapsed:.1f}s\n")
            f.write(text)
            f.write("\n\n")
    doc.close()
    print(f"Salvato: {out_txt}")

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
            extract_and_save(pdf, pages=[0,1,2])
        except Exception as e:
            print(f"[ERRORE] {pdf}: {e}")
        sys.stdout.flush()
