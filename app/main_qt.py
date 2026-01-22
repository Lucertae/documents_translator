#!/usr/bin/env python3
"""
LAC Translate - Professional PDF Translation Application
Entry point for Qt-based application
"""
import sys
import logging
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

# Add parent directory to path for proper imports
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir.parent))

from app.ui import MainWindow


def setup_logging():
    """Configure application logging."""
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / "lac_translate_qt.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )


def main():
    """Application entry point."""
    # Configure logging
    setup_logging()
    logging.info("Starting LAC Translate Qt application")
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("LAC Translate")
    app.setOrganizationName("LUCERTAE SRLS")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Run event loop
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
