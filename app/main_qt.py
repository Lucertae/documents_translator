#!/usr/bin/env python3
"""
LAC Translate - Professional PDF Translation Application
Entry point for Qt-based application
"""
import sys
import logging
import atexit
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

# Add parent directory to path for proper imports
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir.parent))

from app.ui import MainWindow
from app.__version__ import __version__, APP_NAME, get_version_info
from app.core.sentry_integration import (
    init_sentry,
    configure_qt_exception_hook,
    flush as sentry_flush,
    set_context,
)


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


def setup_sentry():
    """Initialize Sentry error tracking."""
    # Initialize Sentry (reads DSN from SENTRY_DSN environment variable)
    initialized = init_sentry(
        # sample_rate=1.0,  # Capture all errors
        # traces_sample_rate=0.1,  # Sample 10% for performance
    )
    
    if initialized:
        # Configure Qt-specific exception handling
        configure_qt_exception_hook()
        
        # Set application context
        set_context("application", get_version_info())
        
        # Flush events on exit
        atexit.register(lambda: sentry_flush(timeout=2.0))
        
        logging.info(f"Sentry error tracking enabled for {APP_NAME} v{__version__}")
    else:
        logging.info("Sentry not configured (set SENTRY_DSN to enable)")


def main():
    """Application entry point."""
    # Configure logging first
    setup_logging()
    logging.info(f"Starting {APP_NAME} v{__version__}")
    
    # Initialize Sentry error tracking
    setup_sentry()
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(__version__)
    app.setOrganizationName("LUCERTAE SRLS")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Run event loop
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
