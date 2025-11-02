#!/usr/bin/env python3
"""
LAC TRANSLATE - Settings Manager
Gestione configurazione utente persistente
"""
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Paths
BASE_DIR = Path(__file__).parent.parent
CONFIG_DIR = BASE_DIR / "config"
CONFIG_FILE = CONFIG_DIR / "settings.json"

# Crea directory config
CONFIG_DIR.mkdir(exist_ok=True)

# Default settings
DEFAULT_SETTINGS = {
    'translator_type': 'Google',
    'source_lang': 'English',
    'target_lang': 'Italiano',
    'text_color': 'Rosso',
    'zoom_level': 1.25,
    'output_dir': str(BASE_DIR / "output"),
    'logs_dir': str(BASE_DIR / "logs"),
    'recent_files': [],
    'max_recent_files': 10,
    'ui_language': 'it',
    'auto_save_settings': True,
    'ocr_language': 'eng',
    'translation_chunk_size': 800
}

class SettingsManager:
    """Gestore configurazione utente"""
    
    def __init__(self):
        self.config_file = CONFIG_FILE
        self.settings = DEFAULT_SETTINGS.copy()
        self.load_settings()
    
    def load_settings(self):
        """Carica impostazioni da file"""
        if not self.config_file.exists():
            logger.info("No settings file found, using defaults")
            return
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
            
            # Merge con default (per nuove impostazioni)
            self.settings.update(loaded)
            
            # Valida e limita recent files
            if 'recent_files' in self.settings:
                self.settings['recent_files'] = self.settings['recent_files'][:self.settings.get('max_recent_files', 10)]
            
            logger.info("Settings loaded successfully")
            
        except json.JSONDecodeError:
            logger.error("Invalid settings file format, using defaults")
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
    
    def save_settings(self):
        """Salva impostazioni su file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            
            logger.info("Settings saved successfully")
            return True
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            return False
    
    def get(self, key, default=None):
        """Ottieni valore impostazione"""
        return self.settings.get(key, default)
    
    def set(self, key, value):
        """Imposta valore impostazione"""
        self.settings[key] = value
        if self.settings.get('auto_save_settings', True):
            self.save_settings()
    
    def add_recent_file(self, file_path):
        """Aggiungi file ai recenti"""
        if 'recent_files' not in self.settings:
            self.settings['recent_files'] = []
        
        # Rimuovi se già presente
        if file_path in self.settings['recent_files']:
            self.settings['recent_files'].remove(file_path)
        
        # Aggiungi all'inizio
        self.settings['recent_files'].insert(0, file_path)
        
        # Limita numero
        max_files = self.settings.get('max_recent_files', 10)
        self.settings['recent_files'] = self.settings['recent_files'][:max_files]
        
        if self.settings.get('auto_save_settings', True):
            self.save_settings()
    
    def get_recent_files(self):
        """Ottieni lista file recenti"""
        return self.settings.get('recent_files', [])
    
    def reset_to_defaults(self):
        """Ripristina impostazioni di default"""
        self.settings = DEFAULT_SETTINGS.copy()
        self.save_settings()
        logger.info("Settings reset to defaults")


# Singleton instance
_settings_manager = None

def get_settings_manager():
    """Ottieni istanza singleton del settings manager"""
    global _settings_manager
    if _settings_manager is None:
        _settings_manager = SettingsManager()
    return _settings_manager

