"""
Test OCR su singola pagina con preprocessing e diagnostica.
Mostra: motore OCR, caratteristiche PNG, output OCR, tempo.
"""
import logging
import os
import time

# Mostra log INFO a schermo (richiesto per vedere info preprocessing)
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

from app.core.pdf_processor import PDFProcessor
from app.core.rapid_ocr import OCR_ENGINE_NAME
from app.core.preprocess_for_ocr import preprocess_pdf_page

# ---- Configurazione ----
pdf_path = "input/confidenziali/Signed_FY2025_2027_Authorized_Distribution_Agreement_Distributor.pdf"
page_num = 1
# -------------------------

print(f"\n{'='*60}")
print(f"Motore OCR: {OCR_ENGINE_NAME}")
print(f"PDF: {pdf_path}")
print(f"Pagina: {page_num}")
print(f"{'='*60}\n")

# Preprocessing standalone (per mostrare info PNG a schermo)
png_path, info = preprocess_pdf_page(pdf_path, page_num, dpi=150)
print(f"PNG preprocessato: {png_path}")
print(f"  Dimensioni:  {info['width']}x{info['height']} px")
print(f"  DPI:         {info['dpi']}")
print(f"  Mode:        {info['mode']}")
print(f"  File size:   {info['file_size_kb']} KB")
print(f"  Originale:   {info['original_size'][0]}x{info['original_size'][1]} px")
print()

# Pulizia PNG temp (il pipeline ne creerà uno suo)
try:
    os.remove(png_path)
except Exception:
    pass

# OCR tramite pipeline
processor = PDFProcessor(pdf_path)
start = time.time()
text = processor.extract_text(page_num)
elapsed = time.time() - start

print(f"\n{'='*60}")
print(f"--- OCR output pagina {page_num} ---")
print(f"{'='*60}\n")
print(text)
print(f"\n{'='*60}")
print(f"Tempo OCR: {elapsed:.2f} secondi")
print(f"Caratteri estratti: {len(text)}")
print(f"Parole estratte: {len(text.split())}")
print(f"{'='*60}\n")
