# Building LAC Translate for Windows

This guide explains how to build the Windows executable with full PaddleOCR support for scanned document translation.

## Prerequisites

- Windows 10/11 (64-bit)
- Python 3.11 (3.12+ may have compatibility issues with PaddlePaddle)
- At least 8GB RAM for the build process
- ~3GB free disk space

## Quick Build

Run the automated build script:

```batch
build_windows.bat
```

This will:
1. Create a virtual environment
2. Install all dependencies
3. Download OCR models
4. Build the executable

## Manual Build Steps

### 1. Setup Environment

```batch
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install pyinstaller
```

### 2. Download OCR Models

**IMPORTANT**: This step is required for scanned PDF support!

```batch
python scripts/download_ocr_models.py
```

This downloads the PaddleOCR PP-OCRv5 models (~500MB) and stores them in `paddle_models/`.

### 3. Build

```batch
pyinstaller lac_translate.spec --clean --noconfirm
```

The executable will be in `dist/lac-translate/lac-translate.exe`.

## Troubleshooting

### "A dependency error occurred during pipeline creation"

This error means the OCR models are not found. Solutions:

1. **Re-run model download**:
   ```batch
   python scripts/download_ocr_models.py
   ```

2. **Check models directory**: Ensure `paddle_models/` exists in the same directory as the executable.

3. **Check PaddleX cache**: Models might also be in `%USERPROFILE%\.paddlex\official_models\`

### "Failed to initialize PaddleOCR"

1. **Update PaddlePaddle**:
   ```batch
   pip install paddlepaddle==3.2.1
   pip install paddleocr>=3.3.0
   ```

2. **Install Visual C++ Redistributable**: Download from Microsoft.

### Build takes too long / Out of memory

1. Close other applications
2. Try building without UPX compression:
   Edit `lac_translate.spec`, change `upx=True` to `upx=False`

## Directory Structure After Build

```
dist/lac-translate/
├── lac-translate.exe      # Main executable
├── paddle_models/         # OCR models (if downloaded)
├── .paddlex/              # PaddleX models cache
├── paddle/                # PaddlePaddle libraries
├── PySide6/               # Qt libraries
└── ...                    # Other dependencies
```

## Testing the Build

1. Run `dist/lac-translate/lac-translate.exe`
2. Open a scanned PDF
3. Click "Translate"
4. If OCR works, the scanned text will be recognized and translated

## Notes

- First run may take longer as models are loaded into memory
- Translation models (~300MB per language pair) are downloaded on first use
- For best OCR quality, use 300 DPI scans
