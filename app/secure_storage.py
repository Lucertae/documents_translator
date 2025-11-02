#!/usr/bin/env python3
"""
LAC TRANSLATE - Secure Storage
Storage sicuro per dati sensibili (licenze, chiavi, etc.)
"""
import json
import logging
from pathlib import Path
from typing import Optional, Any, Dict
from security import get_security_manager

logger = logging.getLogger(__name__)

class SecureStorage:
    """Storage sicuro con encryption per dati sensibili"""
    
    def __init__(self, storage_file: Optional[Path] = None):
        if storage_file is None:
            storage_file = Path(__file__).parent.parent / "security" / "secure_storage.json"
        
        self.storage_file = Path(storage_file)
        self.storage_file.parent.mkdir(parents=True, exist_ok=True)
        self.security_manager = get_security_manager()
    
    def save_secure_value(self, key: str, value: str, encrypt: bool = True) -> bool:
        """Salva valore sicuro (criptato)"""
        try:
            # Carica storage esistente
            data = self._load_storage()
            
            # Cripta valore se richiesto
            if encrypt:
                encrypted_value = self.security_manager.encrypt_data(value)
                if encrypted_value:
                    data[key] = {
                        'encrypted': True,
                        'value': encrypted_value
                    }
                else:
                    # Fallback non criptato se encryption fallisce
                    logger.warning(f"Encryption failed for {key}, storing unencrypted")
                    data[key] = {
                        'encrypted': False,
                        'value': value
                    }
            else:
                data[key] = {
                    'encrypted': False,
                    'value': value
                }
            
            # Salva storage
            return self._save_storage(data)
        except Exception as e:
            logger.error(f"Error saving secure value {key}: {e}")
            return False
    
    def load_secure_value(self, key: str) -> Optional[str]:
        """Carica valore sicuro (decriptato)"""
        try:
            data = self._load_storage()
            
            if key not in data:
                return None
            
            entry = data[key]
            
            # Decripta se necessario
            if entry.get('encrypted', False):
                decrypted = self.security_manager.decrypt_data(entry['value'])
                if decrypted:
                    return decrypted
                else:
                    logger.error(f"Decryption failed for {key}")
                    return None
            else:
                return entry['value']
        except Exception as e:
            logger.error(f"Error loading secure value {key}: {e}")
            return None
    
    def delete_secure_value(self, key: str) -> bool:
        """Rimuove valore sicuro"""
        try:
            data = self._load_storage()
            
            if key in data:
                del data[key]
                return self._save_storage(data)
            
            return True
        except Exception as e:
            logger.error(f"Error deleting secure value {key}: {e}")
            return False
    
    def list_keys(self) -> list:
        """Lista tutte le chiavi salvate"""
        try:
            data = self._load_storage()
            return list(data.keys())
        except Exception:
            return []
    
    def _load_storage(self) -> Dict[str, Any]:
        """Carica storage da file"""
        if not self.storage_file.exists():
            return {}
        
        try:
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading storage: {e}")
            return {}
    
    def _save_storage(self, data: Dict[str, Any]) -> bool:
        """Salva storage su file"""
        try:
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            # Proteggi file (solo Unix)
            import sys
            if sys.platform != 'win32':
                import os
                os.chmod(self.storage_file, 0o600)  # Solo proprietario leggibile/scrivibile
            
            return True
        except Exception as e:
            logger.error(f"Error saving storage: {e}")
            return False

