#!/usr/bin/env python3
"""
LAC TRANSLATE - Integrity Checker
Verifica integrità file critici e protezione contro tampering
"""
import hashlib
import sys
import logging
from pathlib import Path
from typing import Optional, Dict, List
import json

logger = logging.getLogger(__name__)

# File critici da verificare (opzionale - per build distribuiti)
CRITICAL_FILES = [
    'app/license_manager.py',
    'app/license_activation.py',
    'app/pdf_translator_gui.py',
]

class IntegrityChecker:
    """Verifica integrità file critici applicazione"""
    
    def __init__(self, app_dir: Optional[Path] = None):
        if app_dir is None:
            app_dir = Path(__file__).parent.parent
        self.app_dir = Path(app_dir)
        self.manifest_file = self.app_dir / "security" / "file_manifest.json"
    
    def compute_file_hash(self, file_path: Path) -> Optional[str]:
        """Calcola hash SHA256 di un file"""
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"Error computing hash for {file_path}: {e}")
            return None
    
    def create_manifest(self, files: List[str]) -> Dict[str, str]:
        """Crea manifest hash per file critici"""
        manifest = {}
        
        for file_rel_path in files:
            file_path = self.app_dir / file_rel_path
            if file_path.exists():
                file_hash = self.compute_file_hash(file_path)
                if file_hash:
                    manifest[file_rel_path] = file_hash
                    logger.debug(f"Added to manifest: {file_rel_path} ({file_hash[:16]}...)")
        
        return manifest
    
    def save_manifest(self, manifest: Dict[str, str]) -> bool:
        """Salva manifest in file"""
        try:
            self.manifest_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.manifest_file, 'w') as f:
                json.dump(manifest, f, indent=2)
            logger.info(f"Manifest saved: {self.manifest_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving manifest: {e}")
            return False
    
    def load_manifest(self) -> Optional[Dict[str, str]]:
        """Carica manifest da file"""
        try:
            if not self.manifest_file.exists():
                return None
            
            with open(self.manifest_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading manifest: {e}")
            return None
    
    def verify_integrity(self, strict: bool = False) -> Dict[str, bool]:
        """
        Verifica integrità file critici
        
        Args:
            strict: Se True, fallisce su qualsiasi modifica. Se False, solo warning.
        
        Returns:
            Dict con risultato verifica per ogni file
        """
        manifest = self.load_manifest()
        if not manifest:
            logger.warning("No integrity manifest found - skipping integrity check")
            return {}
        
        results = {}
        
        for file_rel_path, expected_hash in manifest.items():
            file_path = self.app_dir / file_rel_path
            
            if not file_path.exists():
                logger.warning(f"Critical file missing: {file_rel_path}")
                results[file_rel_path] = False
                continue
            
            actual_hash = self.compute_file_hash(file_path)
            if not actual_hash:
                logger.error(f"Cannot compute hash for: {file_rel_path}")
                results[file_rel_path] = False
                continue
            
            if actual_hash == expected_hash:
                results[file_rel_path] = True
                logger.debug(f"✓ Integrity verified: {file_rel_path}")
            else:
                logger.warning(
                    f"⚠ Integrity check FAILED for {file_rel_path}\n"
                    f"  Expected: {expected_hash[:16]}...\n"
                    f"  Actual:   {actual_hash[:16]}..."
                )
                results[file_rel_path] = False
                
                if strict:
                    logger.error(f"Strict mode: Integrity violation detected!")
        
        return results
    
    def check_critical_files(self) -> bool:
        """Verifica file critici - ritorna True se tutti OK"""
        results = self.verify_integrity(strict=False)
        
        if not results:
            # Nessun manifest = prima installazione, OK
            return True
        
        # Verifica che tutti i file siano integri
        all_ok = all(results.values())
        
        if not all_ok:
            logger.warning(
                f"Integrity check found {sum(1 for v in results.values() if not v)} "
                f"modified file(s) out of {len(results)}"
            )
        
        return all_ok

