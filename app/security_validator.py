#!/usr/bin/env python3
"""
LAC TRANSLATE - Security Validator
Validazione sicurezza avanzata e protezione anti-tampering
"""
import sys
import os
import hashlib
import logging
import platform
import psutil
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime

logger = logging.getLogger(__name__)

class SecurityValidator:
    """Validator sicurezza avanzato"""
    
    def __init__(self, app_dir: Optional[Path] = None):
        if app_dir is None:
            app_dir = Path(__file__).parent.parent
        self.app_dir = Path(app_dir)
        self.security_log = self.app_dir / "logs" / "security.log"
        self.security_log.parent.mkdir(parents=True, exist_ok=True)
    
    def log_security_event(self, event_type: str, message: str, severity: str = "INFO"):
        """Log evento sicurezza"""
        try:
            with open(self.security_log, 'a', encoding='utf-8') as f:
                timestamp = datetime.now().isoformat()
                f.write(f"[{timestamp}] [{severity}] [{event_type}] {message}\n")
        except Exception as e:
            logger.error(f"Error writing security log: {e}")
    
    def check_debugger(self) -> bool:
        """Rileva presenza debugger"""
        try:
            # Check common debugger indicators
            if sys.gettrace() is not None:
                self.log_security_event("DEBUGGER_DETECTED", "Python debugger detected", "WARNING")
                return True
            return False
        except Exception:
            return False
    
    def check_vm_sandbox(self) -> Dict[str, bool]:
        """Rileva se in esecuzione in VM/sandbox"""
        indicators = {
            'is_vm': False,
            'is_sandbox': False,
            'suspicious_processes': []
        }
        
        try:
            # Check VM indicators
            system_info = platform.uname()
            vm_keywords = ['virtualbox', 'vmware', 'qemu', 'xen', 'kvm', 'parallels']
            system_lower = f"{system_info.system} {system_info.release}".lower()
            
            for keyword in vm_keywords:
                if keyword in system_lower:
                    indicators['is_vm'] = True
                    self.log_security_event("VM_DETECTED", f"VM detected: {keyword}", "INFO")
                    break
            
            # Check for common sandbox/debugging tools
            suspicious_processes = ['wireshark', 'fiddler', 'procmon', 'ollydbg', 'x64dbg', 'ida']
            running_processes = [p.name().lower() for p in psutil.process_iter(['name'])]
            
            for proc in suspicious_processes:
                if proc in running_processes:
                    indicators['suspicious_processes'].append(proc)
                    indicators['is_sandbox'] = True
            
            if indicators['suspicious_processes']:
                self.log_security_event(
                    "SUSPICIOUS_PROCESSES",
                    f"Detected: {', '.join(indicators['suspicious_processes'])}",
                    "WARNING"
                )
        except Exception as e:
            logger.error(f"Error checking VM/sandbox: {e}")
        
        return indicators
    
    def verify_executable_integrity(self) -> bool:
        """Verifica integrità eseguibile principale"""
        try:
            # Per eseguibili PyInstaller, verifica firma file
            if getattr(sys, 'frozen', False):
                executable_path = Path(sys.executable)
                
                if executable_path.exists():
                    # Calcola hash eseguibile
                    sha256_hash = hashlib.sha256()
                    with open(executable_path, 'rb') as f:
                        # Leggi solo primi 1MB per performance
                        chunk = f.read(1024 * 1024)
                        sha256_hash.update(chunk)
                    
                    hash_value = sha256_hash.hexdigest()
                    
                    # In produzione, confronta con hash atteso salvato
                    # Per ora solo loggiamo
                    self.log_security_event(
                        "EXECUTABLE_HASH",
                        f"Executable hash: {hash_value[:16]}...",
                        "INFO"
                    )
                    return True
            
            return True  # Non frozen, quindi script Python normale
        except Exception as e:
            logger.error(f"Error verifying executable integrity: {e}")
            return False
    
    def check_file_permissions(self, file_path: Path) -> Dict[str, bool]:
        """Verifica permessi file critici"""
        result = {
            'exists': file_path.exists(),
            'readable': False,
            'writable': False,
            'secure': False
        }
        
        try:
            if file_path.exists():
                result['readable'] = os.access(file_path, os.R_OK)
                result['writable'] = os.access(file_path, os.W_OK)
                
                # Su Unix, verifica permessi (non pubblico scrivibile)
                if sys.platform != 'win32':
                    stat_info = os.stat(file_path)
                    mode = stat_info.st_mode
                    # File non deve essere world-writable
                    result['secure'] = not (mode & 0o002)
                else:
                    # Su Windows, permessi più complessi - assumiamo OK se esiste
                    result['secure'] = True
        except Exception as e:
            logger.error(f"Error checking file permissions for {file_path}: {e}")
        
        return result
    
    def validate_license_file_security(self) -> bool:
        """Valida sicurezza file licenza"""
        license_file = self.app_dir / "license" / "license.json"
        
        if not license_file.exists():
            return True  # Nessuna licenza = OK
        
        # Verifica permessi
        perms = self.check_file_permissions(license_file)
        
        if not perms['secure']:
            self.log_security_event(
                "LICENSE_SECURITY_WARNING",
                f"License file has insecure permissions",
                "WARNING"
            )
            return False
        
        # Verifica che file non sia modificato di recente (sospetto)
        try:
            mtime = license_file.stat().st_mtime
            now = datetime.now().timestamp()
            age_hours = (now - mtime) / 3600
            
            # Se modificato nelle ultime ore, potrebbe essere tampering
            if age_hours < 1 and mtime > now - 3600:
                self.log_security_event(
                    "LICENSE_MODIFIED_RECENTLY",
                    f"License file modified {age_hours:.1f} hours ago",
                    "WARNING"
                )
        except Exception:
            pass
        
        return True
    
    def perform_security_checks(self) -> Dict[str, any]:
        """Esegue tutti i controlli sicurezza"""
        results = {
            'debugger_detected': self.check_debugger(),
            'vm_indicators': self.check_vm_sandbox(),
            'executable_integrity': self.verify_executable_integrity(),
            'license_file_security': self.validate_license_file_security(),
            'overall_status': 'OK'
        }
        
        # Determina status complessivo
        warnings = []
        if results['debugger_detected']:
            warnings.append("Debugger detected")
        if results['vm_indicators']['is_vm']:
            warnings.append("Running in VM")
        if results['vm_indicators']['suspicious_processes']:
            warnings.append(f"Suspicious processes: {', '.join(results['vm_indicators']['suspicious_processes'])}")
        if not results['license_file_security']:
            warnings.append("License file security issue")
        
        if warnings:
            results['overall_status'] = 'WARNING'
            results['warnings'] = warnings
            self.log_security_event(
                "SECURITY_WARNINGS",
                f"Warnings: {'; '.join(warnings)}",
                "WARNING"
            )
        else:
            self.log_security_event("SECURITY_CHECK", "All security checks passed", "INFO")
        
        return results


# Istanza globale
_security_validator_instance = None

def get_security_validator(app_dir: Optional[Path] = None) -> SecurityValidator:
    """Ritorna istanza globale SecurityValidator"""
    global _security_validator_instance
    if _security_validator_instance is None:
        _security_validator_instance = SecurityValidator(app_dir)
    return _security_validator_instance

