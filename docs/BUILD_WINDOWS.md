# Building LAC Translate for Windows

This guide explains how to build the Windows executable with GLM-OCR support (via Ollama) for scanned document translation.

## Prerequisites

- Windows 10/11 (64-bit)
- Python 3.11+
- At least 8GB RAM for the build process
- ~2GB free disk space
- [Ollama](https://ollama.com/download) installed on the target machine (for OCR)

## Quick Build

Run the automated build script:

```batch
build_windows.bat
```

This will:
1. Create a virtual environment
2. Install all dependencies
3. Build the executable

## Manual Build Steps

### 1. Setup Environment

```batch
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install pyinstaller
```

### 2. Build

```batch
pyinstaller lac_translate.spec --clean --noconfirm
```

The executable will be in `dist/lac-translate/lac-translate.exe`.

## OCR Setup (on target machine)

GLM-OCR runs via Ollama, which must be installed separately:

1. **Install Ollama**: Download from [ollama.com](https://ollama.com/download)
2. **Pull the GLM-OCR model**:
   ```batch
   ollama pull glm-ocr
   ```
   This downloads the model (~2.2GB, one-time download).
3. The application will automatically detect and use Ollama when processing scanned PDFs.

## Troubleshooting

### "Ollama not available" or OCR not working

1. **Check Ollama is running**: Open a terminal and run `ollama list`
2. **Pull the model**: `ollama pull glm-ocr`
3. **Check Ollama server**: The app expects Ollama at `http://localhost:11434`

### Build takes too long / Out of memory

1. Close other applications
2. Try building without UPX compression:
   Edit `lac_translate.spec`, change `upx=True` to `upx=False`

## Directory Structure After Build

```
dist/lac-translate/
├── lac-translate.exe      # Main executable
├── PySide6/               # Qt libraries
└── ...                    # Other dependencies
```

## Testing the Build

1. Ensure Ollama is running with GLM-OCR model pulled
2. Run `dist/lac-translate/lac-translate.exe`
3. Open a scanned PDF
4. Click "Translate"
5. If OCR works, the scanned text will be recognized and translated

## Notes

- First run may take longer as translation models are loaded into memory
- Translation models (~300MB per language pair) are downloaded on first use
- GLM-OCR processes pages at high resolution for best accuracy
- Ollama runs as a separate process and can use GPU if available
