#!/usr/bin/env python3
"""
LAC TRANSLATE - Version Information
Gestione versioning semantico e build number
"""
import json
from pathlib import Path
from datetime import datetime

# Version information
VERSION_MAJOR = 2
VERSION_MINOR = 0
VERSION_PATCH = 0

# Build information (auto-incremented in build script)
BUILD_NUMBER = 1

# Version string
VERSION_STRING = f"{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_PATCH}"
VERSION_FULL = f"{VERSION_STRING}.{BUILD_NUMBER}"

# Build date
BUILD_DATE = datetime.now().strftime("%Y-%m-%d")

# Version file path
VERSION_FILE = Path(__file__).parent.parent / "VERSION.json"

def get_version():
    """Ottieni versione corrente"""
    return VERSION_STRING

def get_version_full():
    """Ottieni versione completa con build number"""
    return VERSION_FULL

def get_build_info():
    """Ottieni informazioni build"""
    return {
        'version': VERSION_STRING,
        'version_full': VERSION_FULL,
        'build_number': BUILD_NUMBER,
        'build_date': BUILD_DATE,
        'major': VERSION_MAJOR,
        'minor': VERSION_MINOR,
        'patch': VERSION_PATCH
    }

def save_version():
    """Salva informazioni versione in file JSON"""
    info = get_build_info()
    try:
        with open(VERSION_FILE, 'w') as f:
            json.dump(info, f, indent=2)
    except Exception as e:
        print(f"Error saving version: {e}")

def load_version():
    """Carica informazioni versione da file"""
    if VERSION_FILE.exists():
        try:
            with open(VERSION_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return get_build_info()

if __name__ == "__main__":
    # Salva versione quando eseguito direttamente
    save_version()
    print(f"LAC TRANSLATE Version {VERSION_FULL}")
    print(f"Build Date: {BUILD_DATE}")

