#!/usr/bin/env python3
"""
LAC TRANSLATE - Update Downloader
Download e gestione aggiornamenti da GitHub Releases
"""
import urllib.request
import hashlib
from pathlib import Path
from typing import Optional, Callable
import logging
import webbrowser

from update_checker import UpdateChecker

logger = logging.getLogger(__name__)


class UpdateDownloader:
    """Gestore download aggiornamenti"""
    
    def __init__(self):
        self.checker = UpdateChecker()
        self.download_dir = Path(__file__).parent.parent / "downloads"
        self.download_dir.mkdir(exist_ok=True)
    
    def download_update(self, download_url: str, filename: str = None, 
                       progress_callback: Optional[Callable[[int, int], None]] = None) -> Optional[Path]:
        """Download aggiornamento con progress bar opzionale"""
        if not filename:
            filename = download_url.split('/')[-1]
        
        output_path = self.download_dir / filename
        
        try:
            logger.info(f"Downloading update from: {download_url}")
            
            def show_progress(block_num, block_size, total_size):
                if total_size > 0:
                    downloaded = block_num * block_size
                    percent = (downloaded * 100) // total_size
                    if progress_callback:
                        progress_callback(downloaded, total_size)
                    elif block_num % 10 == 0:  # Log ogni 10 blocchi
                        logger.debug(f"Download progress: {percent}% ({downloaded}/{total_size} bytes)")
            
            urllib.request.urlretrieve(download_url, output_path, show_progress)
            
            logger.info(f"Download completed: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error downloading update: {e}")
            return None
    
    def verify_download(self, file_path: Path) -> bool:
        """Verifica integrità file scaricato"""
        if not file_path.exists():
            return False
        
        # Verifica dimensione file (almeno 1MB per essere realistico)
        file_size = file_path.stat().st_size
        if file_size < 1024 * 1024:  # Meno di 1MB probabilmente è un errore
            logger.warning(f"Downloaded file seems too small: {file_size} bytes")
            return False
        
        logger.info(f"Download verified: {file_path} ({file_size} bytes)")
        return True
    
    def open_download_folder(self):
        """Apri cartella downloads"""
        import platform
        import subprocess
        
        try:
            if platform.system() == 'Windows':
                subprocess.Popen(f'explorer "{self.download_dir}"')
            elif platform.system() == 'Darwin':  # macOS
                subprocess.Popen(['open', str(self.download_dir)])
            else:  # Linux
                subprocess.Popen(['xdg-open', str(self.download_dir)])
        except Exception as e:
            logger.error(f"Error opening download folder: {e}")

