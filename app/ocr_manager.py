#!/usr/bin/env python3
"""
LAC TRANSLATE - OCR Manager
Sistema modulare per gestire multiple librerie OCR:
- Tesseract OCR (già implementato)
- Dolphin OCR (da implementare)
- Chandra OCR (da implementare)
"""
import os
import sys
import logging
from pathlib import Path
from typing import Optional, Dict, List
from enum import Enum
from PIL import Image
import io

logger = logging.getLogger(__name__)


class OCREngine(Enum):
    """Enum per i motori OCR disponibili"""
    TESSERACT = "tesseract"
    DOLPHIN = "dolphin"
    CHANDRA = "chandra"
    AUTO = "auto"  # Prova in ordine: Tesseract -> Dolphin -> Chandra


class OCRManager:
    """Manager centralizzato per tutti i motori OCR"""
    
    def __init__(self):
        self.available_engines: Dict[OCREngine, bool] = {}
        self.engine_instances: Dict[OCREngine, object] = {}
        self._initialize_engines()
    
    def _initialize_engines(self):
        """Inizializza tutti i motori OCR disponibili"""
        # Tesseract
        try:
            import pytesseract
            self._configure_tesseract()
            self.available_engines[OCREngine.TESSERACT] = True
            logger.info("Tesseract OCR disponibile")
        except ImportError:
            self.available_engines[OCREngine.TESSERACT] = False
            logger.warning("Tesseract OCR non disponibile - installa pytesseract")
        
        # Dolphin OCR
        try:
            # Dolphin OCR potrebbe essere una libreria Python o API REST
            # Adatta questa parte in base alla libreria effettiva
            self.available_engines[OCREngine.DOLPHIN] = self._check_dolphin_ocr()
            if self.available_engines[OCREngine.DOLPHIN]:
                logger.info("Dolphin OCR disponibile")
        except Exception as e:
            self.available_engines[OCREngine.DOLPHIN] = False
            logger.warning(f"Dolphin OCR non disponibile: {e}")
        
        # Chandra OCR
        try:
            # Chandra OCR potrebbe essere una libreria Python o API REST
            # Adatta questa parte in base alla libreria effettiva
            self.available_engines[OCREngine.CHANDRA] = self._check_chandra_ocr()
            if self.available_engines[OCREngine.CHANDRA]:
                logger.info("Chandra OCR disponibile")
        except Exception as e:
            self.available_engines[OCREngine.CHANDRA] = False
            logger.warning(f"Chandra OCR non disponibile: {e}")
    
    def _configure_tesseract(self):
        """Configura Tesseract OCR"""
        import pytesseract
        
        if sys.platform == 'win32':
            tesseract_paths = [
                r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
                r'C:\Tesseract-OCR\tesseract.exe',
            ]
            for path in tesseract_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    break
        elif sys.platform == 'darwin':
            tesseract_paths = [
                '/usr/local/bin/tesseract',
                '/opt/homebrew/bin/tesseract',
                '/usr/bin/tesseract',
            ]
            for path in tesseract_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    break
    
    def _check_dolphin_ocr(self) -> bool:
        """
        Verifica disponibilità Dolphin OCR
        Dolphin: Document Image Parsing via Heterogeneous Anchor Prompting
        Repository: https://github.com/bytedance/Dolphin
        """
        try:
            # Dolphin richiede modelli Hugging Face e dependencies
            # Verifica se il path del modello esiste o se è installato
            dolphin_path = Path(__file__).parent.parent / "Dolphin"
            hf_model_path = Path(__file__).parent.parent / "hf_model"
            
            # Verifica se esiste una directory Dolphin o modello Hugging Face
            if dolphin_path.exists() or hf_model_path.exists():
                # Verifica dependencies base
                try:
                    import torch
                    import transformers
                    return True
                except ImportError:
                    logger.warning("Dolphin richiede torch e transformers - installa con: pip install torch transformers")
                    return False
            
            # Verifica se è installato come package (se disponibile su PyPI)
            try:
                # Prova import diretto (se viene pubblicato come package)
                import dolphin
                return True
            except ImportError:
                pass
            
            return False
        except Exception as e:
            logger.debug(f"Errore verifica Dolphin: {e}")
            return False
    
    def _check_chandra_ocr(self) -> bool:
        """
        Verifica disponibilità Chandra OCR
        Chandra: Advanced OCR per tabelle complesse e layout
        Repository: https://github.com/datalab-to/chandra
        """
        try:
            # Chandra OCR - verifica se il repository è clonato
            chandra_path = Path(__file__).parent.parent / "chandra"
            
            if chandra_path.exists():
                # Verifica dependencies base
                try:
                    # Chandra potrebbe richiedere torch o altre librerie
                    import torch
                    return True
                except ImportError:
                    logger.warning("Chandra richiede torch - installa con: pip install torch")
                    return False
            
            # Verifica se è installato come package
            try:
                import chandra
                return True
            except ImportError:
                try:
                    import chandra_ocr
                    return True
                except ImportError:
                    pass
            
            return False
        except Exception as e:
            logger.debug(f"Errore verifica Chandra: {e}")
            return False
    
    def extract_text(self, image: Image.Image, engine: OCREngine = OCREngine.AUTO, lang: str = 'eng') -> Optional[str]:
        """
        Estrae testo da un'immagine usando il motore OCR specificato
        
        Args:
            image: PIL Image da processare
            engine: Motore OCR da usare (default: AUTO)
            lang: Lingua per OCR (default: 'eng')
        
        Returns:
            Testo estratto o None se fallisce
        """
        if engine == OCREngine.AUTO:
            # Prova in ordine: Tesseract -> Dolphin -> Chandra
            engines_to_try = [OCREngine.TESSERACT, OCREngine.DOLPHIN, OCREngine.CHANDRA]
            for eng in engines_to_try:
                if self.available_engines.get(eng, False):
                    result = self._extract_with_engine(image, eng, lang)
                    if result:
                        logger.info(f"OCR riuscito con {eng.value}")
                        return result
        
        elif self.available_engines.get(engine, False):
            return self._extract_with_engine(image, engine, lang)
        else:
            logger.warning(f"Motore OCR {engine.value} non disponibile")
            return None
        
        return None
    
    def _extract_with_engine(self, image: Image.Image, engine: OCREngine, lang: str) -> Optional[str]:
        """Estrae testo usando un motore specifico"""
        try:
            if engine == OCREngine.TESSERACT:
                return self._extract_tesseract(image, lang)
            elif engine == OCREngine.DOLPHIN:
                return self._extract_dolphin(image, lang)
            elif engine == OCREngine.CHANDRA:
                return self._extract_chandra(image, lang)
        except Exception as e:
            logger.error(f"Errore OCR con {engine.value}: {e}")
            return None
    
    def _extract_tesseract(self, image: Image.Image, lang: str) -> Optional[str]:
        """Estrae testo usando Tesseract OCR"""
        try:
            import pytesseract
            text = pytesseract.image_to_string(image, lang=lang)
            return text.strip() if text else None
        except Exception as e:
            logger.error(f"Errore Tesseract OCR: {e}")
            return None
    
    def _extract_dolphin(self, image: Image.Image, lang: str) -> Optional[str]:
        """
        Estrae testo usando Dolphin OCR
        Dolphin usa demo_page.py o demo_element.py per parsing documenti
        """
        try:
            dolphin_path = Path(__file__).parent.parent / "Dolphin"
            hf_model_path = Path(__file__).parent.parent / "hf_model"
            
            # Se Dolphin è clonato localmente
            if dolphin_path.exists():
                # Salva immagine temporanea
                temp_image_path = Path(__file__).parent.parent / "temp_dolphin_image.png"
                image.save(temp_image_path)
                
                try:
                    # Usa demo_page.py per parsing pagina completa
                    import subprocess
                    import sys
                    
                    dolphin_script = dolphin_path / "demo_page.py"
                    if dolphin_script.exists():
                        # Esegui Dolphin per parsing
                        result = subprocess.run(
                            [
                                sys.executable,
                                str(dolphin_script),
                                "--model_path", str(hf_model_path) if hf_model_path.exists() else "./hf_model",
                                "--save_dir", str(Path(__file__).parent.parent / "temp_dolphin_output"),
                                "--input_path", str(temp_image_path)
                            ],
                            capture_output=True,
                            text=True,
                            timeout=30
                        )
                        
                        # Leggi risultato dal JSON/Markdown generato
                        output_dir = Path(__file__).parent.parent / "temp_dolphin_output"
                        if output_dir.exists():
                            import json
                            
                            # Cerca file JSON per struttura completa (migliore per tabelle)
                            for file in output_dir.glob("*.json"):
                                try:
                                    with open(file, 'r', encoding='utf-8') as f:
                                        data = json.load(f)
                                        
                                        # Dolphin restituisce elementi strutturati, cerca tabelle
                                        if isinstance(data, list):
                                            # Lista di elementi (page results)
                                            for page_result in data:
                                                if isinstance(page_result, dict) and 'elements' in page_result:
                                                    elements = page_result['elements']
                                                    for elem in elements:
                                                        if isinstance(elem, dict):
                                                            # Se è una tabella, estrai direttamente
                                                            if elem.get('type') == 'tab' or elem.get('label') == 'tab':
                                                                content = elem.get('content', elem.get('text', ''))
                                                                if content:
                                                                    return content
                                        elif isinstance(data, dict):
                                            # Singolo elemento o result
                                            if 'elements' in data:
                                                for elem in data['elements']:
                                                    if isinstance(elem, dict) and (elem.get('type') == 'tab' or elem.get('label') == 'tab'):
                                                        content = elem.get('content', elem.get('text', ''))
                                                        if content:
                                                            return content
                                            
                                            # Fallback: estrai testo generico
                                            if 'text' in data:
                                                return data['text']
                                            elif 'content' in data:
                                                return str(data['content'])
                                except Exception as e:
                                    logger.debug(f"Errore parsing JSON Dolphin: {e}")
                                    continue
                            
                            # Fallback: Prova Markdown
                            for file in output_dir.glob("*.md"):
                                try:
                                    with open(file, 'r', encoding='utf-8') as f:
                                        return f.read()
                                except:
                                    continue
                finally:
                    # Pulisci file temporanei
                    if temp_image_path.exists():
                        temp_image_path.unlink()
            
            logger.warning("Dolphin OCR: modello o script non trovati. Vedi README per installazione.")
            return None
        except Exception as e:
            logger.error(f"Errore Dolphin OCR: {e}")
            return None
    
    def _extract_chandra(self, image: Image.Image, lang: str) -> Optional[str]:
        """
        Estrae testo usando Chandra OCR
        Chandra gestisce tabelle complesse, moduli e layout
        """
        try:
            chandra_path = Path(__file__).parent.parent / "chandra"
            
            # Se Chandra è clonato localmente
            if chandra_path.exists():
                # Salva immagine temporanea
                temp_image_path = Path(__file__).parent.parent / "temp_chandra_image.png"
                image.save(temp_image_path)
                
                try:
                    # Prova import diretto se disponibile
                    try:
                        sys.path.insert(0, str(chandra_path))
                        import chandra
                        # Usa API Chandra per riconoscere testo
                        result = chandra.recognize(str(temp_image_path))
                        if result and hasattr(result, 'text'):
                            return result.text
                        elif isinstance(result, str):
                            return result
                    except ImportError:
                        # Se non è un package, prova script diretto
                        import subprocess
                        
                        # Cerca script principale di Chandra
                        for script_name in ['main.py', 'demo.py', 'recognize.py', 'chandra.py']:
                            script = chandra_path / script_name
                            if script.exists():
                                result = subprocess.run(
                                    [sys.executable, str(script), str(temp_image_path)],
                                    capture_output=True,
                                    text=True,
                                    timeout=30
                                )
                                if result.returncode == 0 and result.stdout:
                                    return result.stdout.strip()
                finally:
                    # Pulisci file temporanei
                    if temp_image_path.exists():
                        temp_image_path.unlink()
                    # Rimuovi path solo se aggiunto
                    try:
                        if str(chandra_path) in sys.path:
                            sys.path.remove(str(chandra_path))
                    except (ValueError, AttributeError):
                        pass
            
            # Prova package installato
            try:
                import chandra_ocr
                result = chandra_ocr.recognize(image)
                if result:
                    return result if isinstance(result, str) else getattr(result, 'text', None)
            except ImportError:
                pass
            
            logger.warning("Chandra OCR: repository o package non trovati. Vedi README per installazione.")
            return None
        except Exception as e:
            logger.error(f"Errore Chandra OCR: {e}")
            return None
    
    def get_available_engines(self) -> List[str]:
        """Ritorna lista di motori OCR disponibili"""
        return [engine.value for engine, available in self.available_engines.items() if available]
    
    def is_available(self, engine: OCREngine) -> bool:
        """Verifica se un motore OCR è disponibile"""
        return self.available_engines.get(engine, False)


# Istanza globale del manager OCR
_ocr_manager_instance = None

def get_ocr_manager() -> OCRManager:
    """Ritorna l'istanza globale del manager OCR (singleton)"""
    global _ocr_manager_instance
    if _ocr_manager_instance is None:
        _ocr_manager_instance = OCRManager()
    return _ocr_manager_instance

