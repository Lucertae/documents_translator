#!/usr/bin/env python3
"""
LAC TRANSLATE - License Manager
Gestione licenze, validazione seriale, binding hardware
"""
import os
import sys
import hashlib
import json
import platform
import uuid
import re
from pathlib import Path
import logging

# Try to import cryptography, use fallback if not available
try:
    from cryptography.fernet import Fernet
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    logging.warning("cryptography not available - using basic encryption")

# Setup logging
logger = logging.getLogger(__name__)

# Paths
BASE_DIR = Path(__file__).parent.parent
LICENSE_DIR = BASE_DIR / "license"
LICENSE_FILE = LICENSE_DIR / "license.dat"
CONFIG_FILE = LICENSE_DIR / "config.json"

# Crea directory licenza
LICENSE_DIR.mkdir(exist_ok=True)

# Chiave di cifratura (in produzione dovrebbe essere più sicura)
# Per ora usiamo una chiave derivata da informazioni sistema
def get_encryption_key():
    """Genera chiave di cifratura basata su info sistema"""
    if CRYPTO_AVAILABLE:
        # Usa Fernet per cifratura sicura
        machine_id = platform.node()
        processor = platform.processor()
        system = platform.system()
        combined = f"{machine_id}{processor}{system}".encode()
        key_hash = hashlib.sha256(combined).digest()
        return Fernet.generate_key()
    else:
        # Fallback: usa hash semplice
        machine_id = platform.node()
        processor = platform.processor()
        system = platform.system()
        combined = f"{machine_id}{processor}{system}".encode()
        return hashlib.sha256(combined).digest()[:32]


class LicenseManager:
    """Gestore licenze per LAC Translate"""
    
    def __init__(self):
        self.license_file = LICENSE_FILE
        self.config_file = CONFIG_FILE
        self.hw_id = self._get_hardware_id()
        self.license_data = None
        self.is_valid = False
        
    def _get_hardware_id(self):
        """Genera ID hardware univoco per binding licenza (cross-platform)"""
        try:
            components = []
            
            # MAC address (tutte le piattaforme)
            try:
                mac = ':'.join(['{:02x}'.format((uuid.getnode() >> i) & 0xff) 
                               for i in range(0, 8*6, 8)][::-1])
                components.append(mac)
            except:
                try:
                    mac = uuid.getnode()
                    components.append(str(mac))
                except:
                    pass
            
            # CPU info (tutte le piattaforme)
            try:
                cpu = platform.processor()
                if cpu:
                    components.append(cpu)
            except:
                pass
            
            # System info (tutte le piattaforme)
            try:
                system = platform.system()
                machine = platform.machine()
                components.append(system)
                components.append(machine)
            except:
                pass
            
            # Platform-specific identifiers
            if sys.platform == 'darwin':  # macOS
                try:
                    # Machine UUID on macOS
                    import subprocess
                    result = subprocess.run(['ioreg', '-rd1', '-c', 'IOPlatformExpertDevice'], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        for line in result.stdout.split('\n'):
                            if 'IOPlatformUUID' in line:
                                uuid_match = re.search(r'"[0-9A-F-]+"', line)
                                if uuid_match:
                                    components.append(uuid_match.group().strip('"'))
                except:
                    pass
            
            elif sys.platform.startswith('linux'):  # Linux
                try:
                    # Machine ID (se disponibile)
                    machine_id_file = Path('/etc/machine-id')
                    if machine_id_file.exists():
                        components.append(machine_id_file.read_text().strip())
                    else:
                        # Fallback: hostname
                        components.append(platform.node())
                except:
                    pass
            
            elif sys.platform == 'win32':  # Windows
                try:
                    # Windows machine GUID
                    import winreg
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                       r"SOFTWARE\Microsoft\Cryptography")
                    guid = winreg.QueryValueEx(key, "MachineGuid")[0]
                    winreg.CloseKey(key)
                    components.append(guid)
                except:
                    pass
            
            # Combina e crea hash
            if components:
                hw_string = ''.join(components).encode()
                hw_hash = hashlib.sha256(hw_string).hexdigest()[:16]
                return hw_hash.upper()
            else:
                # Ultimo fallback
                return hashlib.md5(str(uuid.getnode()).encode()).hexdigest()[:16].upper()
                
        except Exception as e:
            logger.error(f"Error generating hardware ID: {e}")
            # Fallback finale
            try:
                return hashlib.md5(str(uuid.getnode()).encode()).hexdigest()[:16].upper()
            except:
                return "UNKNOWN"
    
    def _encrypt_data(self, data, key=None):
        """Cifra dati licenza"""
        # Per ora non usiamo cifratura, solo hash validation
        # In produzione si può aggiungere cifratura completa
        return data.encode()
    
    def _decrypt_data(self, encrypted_data, key=None):
        """Decifra dati licenza"""
        # Per ora non usiamo cifratura, solo hash validation
        return encrypted_data.decode()
    
    def validate_serial_key(self, serial_key):
        """Valida formato chiave seriale"""
        # Formato: LAC-XXXX-XXXX-XXXX (4 gruppi alfanumerici)
        parts = serial_key.split('-')
        if len(parts) != 4:
            return False
        
        if parts[0].upper() != 'LAC':
            return False
        
        for part in parts[1:]:
            if not part.isalnum() or len(part) != 4:
                return False
        
        return True
    
    def generate_license_hash(self, serial_key, hw_id):
        """Genera hash licenza da seriale e HW ID"""
        combined = f"{serial_key}{hw_id}".encode()
        return hashlib.sha256(combined).hexdigest()[:32]
    
    def activate_license(self, serial_key):
        """Attiva licenza con chiave seriale"""
        if not self.validate_serial_key(serial_key):
            logger.warning(f"Invalid serial key format: {serial_key}")
            return False, "Formato chiave seriale non valido. Usa formato: LAC-XXXX-XXXX-XXXX"
        
        # Genera hash licenza
        license_hash = self.generate_license_hash(serial_key, self.hw_id)
        
        # Crea dati licenza
        license_data = {
            'serial_key': serial_key,
            'hw_id': self.hw_id,
            'license_hash': license_hash,
            'activated': True,
            'license_type': 'FULL',
            'features': ['unlimited_translations', 'all_languages', 'ocr_full'],
            'timestamp': int(__import__('time').time())
        }
        
        # Salva licenza
        try:
            # Salva in formato JSON (cifrato in produzione)
            with open(self.license_file, 'w') as f:
                json.dump(license_data, f, indent=2)
            
            self.license_data = license_data
            self.is_valid = True
            
            # Registra attivazione nel database tracking (se disponibile)
            try:
                from license_tracker import LicenseTracker
                tracker = LicenseTracker()
                tracker.activate_license(serial_key, self.hw_id)
                logger.info(f"License activation registered in tracking database")
            except ImportError:
                logger.debug("License tracker not available, skipping database registration")
            except Exception as e:
                logger.warning(f"Could not register activation in database: {e}")
            
            logger.info(f"License activated successfully: {serial_key[:8]}...")
            return True, "Licenza attivata con successo!"
            
        except Exception as e:
            logger.error(f"Error saving license: {e}")
            return False, f"Errore durante il salvataggio della licenza: {str(e)}"
    
    def load_license(self):
        """Carica licenza da file (con supporto secure storage)"""
        if not self.license_file.exists():
            logger.info("No license file found")
            return False
        
        try:
            with open(self.license_file, 'r') as f:
                self.license_data = json.load(f)
            
            # Se serial_key è criptato, carica da secure storage
            if self.license_data.get('serial_key') == '[ENCRYPTED]':
                try:
                    from secure_storage import SecureStorage
                    secure_storage = SecureStorage()
                    serial_key = secure_storage.load_secure_value('license_serial')
                    
                    if not serial_key:
                        logger.error("Cannot decrypt license serial key from secure storage")
                        return False
                    
                    self.license_data['serial_key'] = serial_key
                except ImportError:
                    logger.error("Secure storage not available but encrypted license found")
                    return False
            
            serial_key = self.license_data.get('serial_key', '')
            
            # Verifica binding hardware
            if self.license_data.get('hw_id') != self.hw_id:
                logger.warning(f"Hardware ID mismatch: {self.license_data.get('hw_id')} != {self.hw_id}")
                return False
            
            # Verifica hash licenza
            expected_hash = self.generate_license_hash(serial_key, self.hw_id)
            if self.license_data.get('license_hash') != expected_hash:
                logger.warning("License hash mismatch - possible tampering")
                return False
            
            # Verifica licenza attivata
            if not self.license_data.get('activated', False):
                logger.warning("License not activated")
                return False
            
            self.is_valid = True
            logger.info("License loaded and validated successfully")
            return True
            
        except json.JSONDecodeError:
            logger.error("Invalid license file format")
            return False
        except Exception as e:
            logger.error(f"Error loading license: {e}")
            return False
    
    def check_license(self):
        """Controlla se licenza è valida"""
        if not self.is_valid:
            return self.load_license()
        return self.is_valid
    
    def get_license_info(self):
        """Ottieni informazioni licenza"""
        if not self.license_data:
            self.load_license()
        
        if not self.license_data:
            return {
                'activated': False,
                'serial_key': None,
                'license_type': None,
                'hw_id': self.hw_id
            }
        
        return {
            'activated': self.license_data.get('activated', False),
            'serial_key': self.license_data.get('serial_key', ''),
            'license_type': self.license_data.get('license_type', 'UNKNOWN'),
            'hw_id': self.license_data.get('hw_id', self.hw_id),
            'features': self.license_data.get('features', [])
        }
    
    def deactivate_license(self):
        """Disattiva licenza (rimuove file)"""
        try:
            if self.license_file.exists():
                self.license_file.unlink()
            self.license_data = None
            self.is_valid = False
            logger.info("License deactivated")
            return True
        except Exception as e:
            logger.error(f"Error deactivating license: {e}")
            return False


# Singleton instance
_license_manager = None

def get_license_manager():
    """Ottieni istanza singleton del license manager"""
    global _license_manager
    if _license_manager is None:
        _license_manager = LicenseManager()
    return _license_manager

