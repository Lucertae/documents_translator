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
from PySide6.QtCore import Qt, qInstallMessageHandler, QtMsgType

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
    capture_message,
    add_breadcrumb,
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


def qt_message_handler(mode: QtMsgType, context, message: str):
    """
    Custom Qt message handler to capture Qt warnings/errors to Sentry.
    """
    if mode == QtMsgType.QtDebugMsg:
        logging.debug(f"Qt Debug: {message}")
    elif mode == QtMsgType.QtInfoMsg:
        logging.info(f"Qt Info: {message}")
    elif mode == QtMsgType.QtWarningMsg:
        logging.warning(f"Qt Warning: {message}")
        add_breadcrumb(
            message=f"Qt Warning: {message}",
            category="qt",
            level="warning",
        )
    elif mode == QtMsgType.QtCriticalMsg:
        logging.error(f"Qt Critical: {message}")
        capture_message(f"Qt Critical Error: {message}", level="error")
    elif mode == QtMsgType.QtFatalMsg:
        logging.critical(f"Qt Fatal: {message}")
        capture_message(f"Qt Fatal Error: {message}", level="fatal")
        sentry_flush(timeout=2.0)


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
    
    # Install Qt message handler to capture Qt warnings/errors
    qInstallMessageHandler(qt_message_handler)
    
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
