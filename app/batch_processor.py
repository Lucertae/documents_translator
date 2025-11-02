#!/usr/bin/env python3
"""
LAC TRANSLATE - Batch Processor
Processamento batch di cartelle PDF
"""
import os
import sys
from pathlib import Path
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

class BatchProcessor:
    """Processore batch per traduzione multipla PDF"""
    
    def __init__(self, input_dir: str, output_dir: str, translator_func=None):
        """
        Inizializza batch processor
        
        Args:
            input_dir: Directory con PDF da tradurre
            output_dir: Directory output per PDF tradotti
            translator_func: Funzione per tradurre un singolo PDF
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.translator_func = translator_func
        
        # Crea output dir se non esiste
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Statistics
        self.processed = 0
        self.failed = 0
        self.total = 0
        
    def find_pdf_files(self) -> List[Path]:
        """Trova tutti i file PDF nella directory input"""
        pdf_files = list(self.input_dir.glob("*.pdf"))
        # Escludi file già tradotti se esistono
        existing_translated = {f.stem for f in self.output_dir.glob("*.pdf")}
        pdf_files = [f for f in pdf_files if f.stem not in existing_translated]
        return sorted(pdf_files)
    
    def process_batch(self, progress_callback=None, error_callback=None):
        """
        Processa tutti i PDF nella cartella
        
        Args:
            progress_callback: Funzione callback(processed, total, current_file)
            error_callback: Funzione callback(file, error)
        
        Returns:
            dict: Statistiche processamento
        """
        pdf_files = self.find_pdf_files()
        self.total = len(pdf_files)
        self.processed = 0
        self.failed = 0
        
        results = []
        
        for i, pdf_file in enumerate(pdf_files, 1):
            try:
                logger.info(f"Processing {i}/{self.total}: {pdf_file.name}")
                
                if progress_callback:
                    progress_callback(i, self.total, pdf_file.name)
                
                # Processa PDF
                if self.translator_func:
                    output_path = self.output_dir / f"translated_{pdf_file.name}"
                    success = self.translator_func(str(pdf_file), str(output_path))
                    
                    if success:
                        self.processed += 1
                        results.append({
                            'file': pdf_file.name,
                            'status': 'success',
                            'output': str(output_path)
                        })
                    else:
                        self.failed += 1
                        results.append({
                            'file': pdf_file.name,
                            'status': 'failed',
                            'error': 'Translation failed'
                        })
                        
                        if error_callback:
                            error_callback(pdf_file, "Translation failed")
                else:
                    # Placeholder - copia file se translator non fornito
                    output_path = self.output_dir / f"translated_{pdf_file.name}"
                    import shutil
                    shutil.copy2(pdf_file, output_path)
                    self.processed += 1
                    
            except Exception as e:
                logger.error(f"Error processing {pdf_file.name}: {e}")
                self.failed += 1
                results.append({
                    'file': pdf_file.name,
                    'status': 'error',
                    'error': str(e)
                })
                
                if error_callback:
                    error_callback(pdf_file, str(e))
        
        return {
            'total': self.total,
            'processed': self.processed,
            'failed': self.failed,
            'results': results
        }
    
    def get_statistics(self):
        """Ottieni statistiche processamento"""
        return {
            'total': self.total,
            'processed': self.processed,
            'failed': self.failed,
            'success_rate': (self.processed / self.total * 100) if self.total > 0 else 0
        }

