# Script di installazione automatica OCR
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "   INSTALLAZIONE OCR AUTOMATICA" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Installa pacchetti Python
Write-Host "[1/3] Installazione pacchetti Python OCR..." -ForegroundColor Yellow
pip install pytesseract pdf2image
Write-Host ""

# Prova a installare Tesseract con winget
Write-Host "[2/3] Tentativo installazione Tesseract con winget..." -ForegroundColor Yellow
try {
    winget install --id UB-Mannheim.TesseractOCR -e --silent
    Write-Host "✓ Tesseract installato con successo!" -ForegroundColor Green
} catch {
    Write-Host "✗ Installazione automatica fallita" -ForegroundColor Red
    Write-Host ""
    Write-Host "Scarica manualmente da:" -ForegroundColor Yellow
    Write-Host "https://github.com/UB-Mannheim/tesseract/wiki" -ForegroundColor Cyan
    Write-Host ""
    
    # Apri il browser
    Start-Process "https://github.com/UB-Mannheim/tesseract/wiki"
}

Write-Host ""
Write-Host "[3/3] Verifica installazione..." -ForegroundColor Yellow

# Verifica Python packages
python -c "import pytesseract; print('✓ pytesseract installato')" 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ pytesseract installato" -ForegroundColor Green
} else {
    Write-Host "✗ pytesseract non installato" -ForegroundColor Red
}

python -c "import pdf2image; print('✓ pdf2image installato')" 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ pdf2image installato" -ForegroundColor Green
} else {
    Write-Host "✗ pdf2image non installato" -ForegroundColor Red
}

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "   INSTALLAZIONE COMPLETATA!" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "NOTA: Se Tesseract non è installato, installalo manualmente" -ForegroundColor Yellow
Write-Host "Riavvia LAC TRANSLATE con AVVIA_GUI.bat" -ForegroundColor Yellow
Write-Host ""

Read-Host "Premi INVIO per continuare"

