from app.core.pdf_processor import PDFProcessor
from app.core.glm_ocr import GLM_OCR_MODEL
import time
from app.core.preprocess_for_ocr import preprocess_pdf_page
from PIL import Image

pdf_path = "input/confidenziali/Signed_FY2025_2027_Authorized_Distribution_Agreement_Distributor.pdf"
page_num = 1

print(f"Userà modello OCR: {GLM_OCR_MODEL}")
processor = PDFProcessor(pdf_path)

# Preprocessing e stampa info PNG
png_path = preprocess_pdf_page(pdf_path, page_num, dpi=150)
with Image.open(png_path) as img:
    width, height = img.size
    dpi = img.info.get('dpi', (150, 150))
    mode = img.mode
    print(f"PNG preprocessato: {png_path}\nRisoluzione: {width}x{height} px | DPI: {dpi} | Mode: {mode}\n")

start = time.time()
text = processor.extract_text(page_num)
elapsed = time.time() - start

print(f"\n--- OCR output pagina {page_num} ---\n")
print(text)
print(f"\nTempo impiegato per pagina: {elapsed:.2f} secondi\n")
