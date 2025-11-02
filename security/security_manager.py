#!/usr/bin/env python3
"""
LAC TRANSLATE - Security Manager
Gestione sicurezza applicazione:
- Validazione integrità file
- Protezione dati sensibili
- Controllo accessi
- Encryption dati
"""
import os
import sys
import hashlib
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import base64

logger = logging.getLogger(__name__)


class SecurityManager:
    """Manager per sicurezza applicazione"""
    
    def __init__(self, app_dir: Optional[Path] = None):
        """
        Inizializza Security Manager
        
        Args:
            app_dir: Directory applicazione (default: directory corrente)
        """
        if app_dir is None:
            app_dir = Path(__file__).parent.parent
        
        self.app_dir = Path(app_dir)
        self.security_dir = self.app_dir / "security"
        self.security_dir.mkdir(exist_ok=True)
        
        # File di configurazione sicurezza
        self.config_file = self.security_dir / "security_config.json"
        self.key_file = self.security_dir / ".encryption_key"
        
        # Inizializza encryption key
        self.encryption_key = self._load_or_create_key()
        self.cipher = Fernet(self.encryption_key) if self.encryption_key else None
    
    def _load_or_create_key(self) -> Optional[bytes]:
        """Carica o crea chiave di encryption"""
        try:
            if self.key_file.exists():
                with open(self.key_file, 'rb') as f:
                    return f.read()
            else:
                # Crea nuova chiave
                key = Fernet.generate_key()
                with open(self.key_file, 'wb') as f:
                    f.write(key)
                # Proteggi il file (solo su Unix)
                if sys.platform != 'win32':
                    os.chmod(self.key_file, 0o600)
                return key
        except Exception as e:
            logger.error(f"Errore gestione encryption key: {e}")
            return None
    
    def encrypt_data(self, data: str) -> Optional[str]:
        """
        Cripta dati sensibili
        
        Args:
            data: Dati da criptare (stringa)
        
        Returns:
            Dati criptati (base64) o None se errore
        """
        if not self.cipher:
            logger.warning("Encryption non disponibile")
            return None
        
        try:
            encrypted = self.cipher.encrypt(data.encode('utf-8'))
            return base64.b64encode(encrypted).decode('utf-8')
        except Exception as e:
            logger.error(f"Errore encryption: {e}")
            return None
    
    def decrypt_data(self, encrypted_data: str) -> Optional[str]:
        """
        Decripta dati sensibili
        
        Args:
            encrypted_data: Dati criptati (base64)
        
        Returns:
            Dati originali o None se errore
        """
        if not self.cipher:
            logger.warning("Encryption non disponibile")
            return None
        
        try:
            encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
            decrypted = self.cipher.decrypt(encrypted_bytes)
            return decrypted.decode('utf-8')
        except Exception as e:
            logger.error(f"Errore decryption: {e}")
            return None
    
    def compute_file_hash(self, file_path: Path) -> Optional[str]:
        """
        Calcola hash SHA256 di un file per verificare integrità
        
        Args:
            file_path: Percorso file
        
        Returns:
            Hash SHA256 o None se errore
        """
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"Errore calcolo hash file {file_path}: {e}")
            return None
    
    def verify_file_integrity(self, file_path: Path, expected_hash: str) -> bool:
        """
        Verifica integrità file confrontando hash
        
        Args:
            file_path: Percorso file da verificare
            expected_hash: Hash atteso
        
        Returns:
            True se integrità verificata, False altrimenti
        """
        actual_hash = self.compute_file_hash(file_path)
        if not actual_hash:
            return False
        return actual_hash == expected_hash
    
    def save_secure_data(self, key: str, data: Any, encrypt: bool = True) -> bool:
        """
        Salva dati in modo sicuro
        
        Args:
            key: Chiave identificativa
            data: Dati da salvare
            encrypt: Se True, cripta i dati
        
        Returns:
            True se salvato con successo
        """
        try:
            config = {}
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            if encrypt and isinstance(data, str):
                encrypted = self.encrypt_data(data)
                if encrypted:
                    config[key] = encrypted
                else:
                    config[key] = data  # Fallback non criptato
            else:
                config[key] = data
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"Errore salvataggio dati sicuri: {e}")
            return False
    
    def load_secure_data(self, key: str, decrypt: bool = True) -> Optional[Any]:
        """
        Carica dati salvati in modo sicuro
        
        Args:
            key: Chiave identificativa
            decrypt: Se True, decripta i dati
        
        Returns:
            Dati caricati o None se errore
        """
        try:
            if not self.config_file.exists():
                return None
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            if key not in config:
                return None
            
            data = config[key]
            
            if decrypt and isinstance(data, str):
                decrypted = self.decrypt_data(data)
                return decrypted if decrypted else data
            
            return data
        except Exception as e:
            logger.error(f"Errore caricamento dati sicuri: {e}")
            return None
    
    def check_security_status(self) -> Dict[str, bool]:
        """
        Verifica stato sicurezza applicazione
        
        Returns:
            Dizionario con stato vari controlli sicurezza
        """
        status = {
            'encryption_available': self.cipher is not None,
            'key_file_exists': self.key_file.exists(),
            'config_file_exists': self.config_file.exists(),
            'security_dir_exists': self.security_dir.exists(),
        }
        return status


# Istanza globale del manager sicurezza
_security_manager_instance = None

def get_security_manager(app_dir: Optional[Path] = None) -> SecurityManager:
    """Ritorna l'istanza globale del manager sicurezza (singleton)"""
    global _security_manager_instance
    if _security_manager_instance is None:
        _security_manager_instance = SecurityManager(app_dir)
    return _security_manager_instance

