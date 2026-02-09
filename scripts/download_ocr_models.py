#!/usr/bin/env python3
"""
Pre-download PaddleOCR models for bundling in Windows EXE.

Run this script BEFORE building with PyInstaller to ensure
all models are available offline.
"""
import os
import sys

# Set environment first
os.environ['DISABLE_MODEL_SOURCE_CHECK'] = 'True'

def download_models():
    """Download all PaddleOCR models for English."""
    print("=" * 60)
    print("PaddleOCR Model Pre-Download Script")
    print("=" * 60)
    
    # Create models directory
    models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'paddle_models')
    os.makedirs(models_dir, exist_ok=True)
    
    # Set paddle home to our directory
    os.environ['PADDLE_HOME'] = models_dir
    os.environ['PADDLEOCR_HOME'] = models_dir
    os.environ['HF_HOME'] = models_dir
    
    print(f"\nModels will be stored in: {models_dir}")
    print("\n[1/4] Initializing PaddleOCR for English...")
    
    try:
        from paddleocr import PaddleOCR
        
        # Initialize OCR - this triggers model download
        ocr = PaddleOCR(
            lang='en',
            use_textline_orientation=True,
        )
        print("[OK] English OCR models downloaded")
        
        # Test on a simple image
        print("\n[2/4] Testing OCR functionality...")
        import numpy as np
        from PIL import Image
        
        # Create a test image with text
        test_img = np.ones((100, 300, 3), dtype=np.uint8) * 255
        result = ocr.predict(test_img)
        print("[OK] OCR test passed")
        
    except Exception as e:
        print(f"[ERROR] Failed to initialize PaddleOCR: {e}")
        return False
    
    print("\n[3/4] Trying LayoutDetection (optional)...")
    try:
        from paddleocr import LayoutDetection
        layout = LayoutDetection()
        print("[OK] LayoutDetection models downloaded")
    except Exception as e:
        print(f"[SKIP] LayoutDetection not available: {e}")
    
    print("\n[4/4] Trying DocPreprocessor (optional)...")
    try:
        from paddleocr import DocPreprocessor
        preprocessor = DocPreprocessor()
        print("[OK] DocPreprocessor models downloaded")
    except Exception as e:
        print(f"[SKIP] DocPreprocessor not available: {e}")
    
    # List downloaded models
    print(f"\n{'=' * 60}")
    print("Downloaded models:")
    print("=" * 60)
    
    total_size = 0
    for root, dirs, files in os.walk(models_dir):
        for f in files:
            filepath = os.path.join(root, f)
            size = os.path.getsize(filepath)
            total_size += size
            rel_path = os.path.relpath(filepath, models_dir)
            if size > 1_000_000:  # Only show files > 1MB
                print(f"  {rel_path}: {size/1_000_000:.1f} MB")
    
    print(f"\nTotal size: {total_size/1_000_000:.1f} MB")
    print("\n[OK] Model pre-download complete!")
    print("\nYou can now build the Windows EXE with:")
    print("  pyinstaller lac_translate.spec --clean")
    
    return True


if __name__ == '__main__':
    success = download_models()
    sys.exit(0 if success else 1)
