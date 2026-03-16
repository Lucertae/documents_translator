#!/usr/bin/env python3
"""
LAC Translate - Professional PDF Translation Application
Entry point for Qt-based application
"""
import sys
import logging
import atexit
from pathlib import Path

# ── Fase 0: Qt va inizializzato subito (prima di qualsiasi import pesante)
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, qInstallMessageHandler, QtMsgType
from PySide6.QtGui import QIcon

# Add parent directory to path for proper imports
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir.parent))

# Importa solo cose leggere a questo punto
from app.__version__ import __version__, APP_NAME, get_version_info


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
    from app.core.sentry_integration import capture_message, add_breadcrumb, flush as sentry_flush

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
    from app.core.sentry_integration import (
        init_sentry, configure_qt_exception_hook,
        flush as sentry_flush, set_context,
    )

    initialized = init_sentry()
    
    if initialized:
        configure_qt_exception_hook()
        set_context("application", get_version_info())
        atexit.register(lambda: sentry_flush(timeout=2.0))
        logging.info(f"Sentry error tracking enabled for {APP_NAME} v{__version__}")
    else:
        logging.info("Sentry not configured (set SENTRY_DSN to enable)")


def main():
    """Application entry point con splash screen."""
    # Configure logging first
    setup_logging()
    logging.info(f"Starting {APP_NAME} v{__version__}")

    # Crea QApplication subito (richiesto da qualsiasi widget)
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(__version__)
    app.setOrganizationName("LUCERTAE SRLS")

    # Icona app
    icon_path = Path(__file__).parent.parent / 'assets' / 'icon.png'
    if not icon_path.exists():
        icon_path = Path(sys.executable).parent / '_internal' / 'assets' / 'icon.png'
    if not icon_path.exists():
        icon_path = Path(sys.executable).parent / 'assets' / 'icon.png'
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    # ── Mostra splash screen immediatamente ──
    from app.ui.splash import SplashScreen
    splash = SplashScreen()
    splash.show()
    app.processEvents()

    # ── Caricamento progressivo ──
    splash.set_progress(5, "Preparo il motore…")

    # Sentry (leggero)
    splash.set_progress(10, "Configuro il sistema di diagnostica…")
    setup_sentry()

    # Qt message handler
    qInstallMessageHandler(qt_message_handler)

    # Import pesanti — qui torch/transformers/pymupdf vengono caricati
    splash.set_progress(20, "Carico le librerie di traduzione… (un attimo)")
    from app.ui import MainWindow

    splash.set_progress(60, "Quasi pronto… preparo l'interfaccia")

    # Crea la finestra principale (questo carica il modello OPUS-MT)
    window = MainWindow()

    splash.set_progress(90, "Ci siamo quasi!")

    # Mostra finestra, chiudi splash
    splash.set_progress(100, "Tutto pronto!")
    window.show()
    splash.close()
    splash.deleteLater()

    logging.info("Splash completato, app attiva")

    # Run event loop
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
