#!/usr/bin/env python3
"""
LAC TRANSLATE - Update Checker
Controlla aggiornamenti disponibili su GitHub Releases
"""
import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

# Configurazione repository GitHub
GITHUB_REPO = "Lucertae/documents_translator"
GITHUB_API_BASE = f"https://api.github.com/repos/{GITHUB_REPO}"

# Importa versione corrente
try:
    from version import VERSION_STRING, get_version
    CURRENT_VERSION = VERSION_STRING
except ImportError:
    # Fallback se version.py non disponibile
    CURRENT_VERSION = "2.0.0"
    def get_version():
        return CURRENT_VERSION


class UpdateChecker:
    """Gestore check aggiornamenti da GitHub"""
    
    def __init__(self, repo: str = None):
        self.repo = repo or GITHUB_REPO
        self.api_base = f"https://api.github.com/repos/{self.repo}"
        self.current_version = get_version()
        logger.info(f"Update checker initialized for version {self.current_version}")
    
    def get_latest_release(self) -> Optional[Dict]:
        """Ottieni ultima release da GitHub"""
        try:
            url = f"{self.api_base}/releases/latest"
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'LAC-Translate-Updater/2.0')
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read())
                release_info = {
                    'tag_name': data['tag_name'],
                    'version': data['tag_name'].lstrip('v'),
                    'name': data['name'],
                    'body': data['body'],
                    'published_at': data['published_at'],
                    'assets': data.get('assets', []),
                    'html_url': data['html_url']
                }
                logger.info(f"Latest release found: {release_info['version']}")
                return release_info
        except urllib.error.HTTPError as e:
            if e.code == 404:
                logger.info("No releases found on GitHub")
            else:
                logger.error(f"HTTP error checking for updates: {e}")
            return None
        except urllib.error.URLError as e:
            logger.error(f"Network error checking for updates: {e}")
            return None
        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
            return None
    
    def compare_versions(self, version1: str, version2: str) -> int:
        """
        Confronta versioni. 
        Ritorna: -1 (v1 < v2), 0 (v1 == v2), 1 (v1 > v2)
        """
        try:
            v1_parts = [int(x) for x in version1.split('.')]
            v2_parts = [int(x) for x in version2.split('.')]
            
            # Padding con zeri se necessario
            max_len = max(len(v1_parts), len(v2_parts))
            v1_parts += [0] * (max_len - len(v1_parts))
            v2_parts += [0] * (max_len - len(v2_parts))
            
            for v1, v2 in zip(v1_parts, v2_parts):
                if v1 < v2:
                    return -1
                elif v1 > v2:
                    return 1
            return 0
        except Exception as e:
            logger.error(f"Error comparing versions: {e}")
            return 0
    
    def check_for_updates(self) -> Optional[Dict]:
        """Controlla se ci sono aggiornamenti disponibili"""
        latest = self.get_latest_release()
        if not latest:
            return None
        
        latest_version = latest['version']
        comparison = self.compare_versions(self.current_version, latest_version)
        
        if comparison < 0:
            # Versione corrente < ultima versione
            return {
                'available': True,
                'current_version': self.current_version,
                'latest_version': latest_version,
                'release_info': latest
            }
        
        return {'available': False, 'current_version': self.current_version}
    
    def get_download_url(self, platform: str = None) -> Optional[str]:
        """Ottieni URL download per piattaforma"""
        if not platform:
            import sys
            if sys.platform == 'win32':
                platform = 'windows'
            elif sys.platform == 'darwin':
                platform = 'macos'
            elif sys.platform.startswith('linux'):
                platform = 'linux'
        
        latest = self.get_latest_release()
        if not latest:
            return None
        
        # Cerca asset per piattaforma
        for asset in latest['assets']:
            name = asset['name'].lower()
            url = asset['browser_download_url']
            
            if platform == 'windows':
                if name.endswith('.exe') or 'windows' in name or 'win' in name:
                    return url
            elif platform == 'macos':
                if name.endswith('.dmg') or 'macos' in name or 'mac' in name:
                    return url
            elif platform == 'linux':
                if name.endswith('.deb') or name.endswith('.rpm') or 'linux' in name:
                    return url
        
        # Fallback: ritorna primo asset disponibile
        if latest['assets']:
            return latest['assets'][0]['browser_download_url']
        
        return None

