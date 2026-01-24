"""
Sentry Integration for LAC Translate

This module provides centralized Sentry error tracking and monitoring.
Follows best practices for Python desktop applications:
- Automatic error capture with full context
- User privacy protection (configurable PII settings)
- Performance monitoring for slow operations
- Breadcrumbs for debugging complex issues
- Qt-specific exception handling

Configuration:
    Set SENTRY_DSN environment variable, or pass DSN to init_sentry()
    Set SENTRY_ENVIRONMENT for environment tagging (production, staging, dev)

Usage:
    from app.core.sentry_integration import init_sentry, capture_exception, add_breadcrumb
    
    # At app startup
    init_sentry()
    
    # In error handlers
    try:
        risky_operation()
    except Exception as e:
        capture_exception(e, context={"operation": "pdf_load"})
"""
import os
import sys
import logging
import platform
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from functools import wraps

# Lazy import sentry_sdk to avoid import errors if not installed
_sentry_sdk = None
_sentry_initialized = False

logger = logging.getLogger(__name__)


def _get_sentry_sdk():
    """Lazy import of sentry_sdk."""
    global _sentry_sdk
    if _sentry_sdk is None:
        try:
            import sentry_sdk
            _sentry_sdk = sentry_sdk
        except ImportError:
            logger.warning("sentry-sdk not installed. Error tracking disabled.")
            _sentry_sdk = False
    return _sentry_sdk if _sentry_sdk else None


def _load_env_file():
    """Load environment variables from .env file if python-dotenv is available."""
    try:
        from dotenv import load_dotenv
        
        # Multiple locations to search for .env file
        search_paths = [
            # 1. Project root (development)
            Path(__file__).parent.parent.parent / ".env",
            # 2. Current working directory
            Path.cwd() / ".env",
            # 3. Executable directory (PyInstaller bundle)
            Path(sys.executable).parent / ".env",
            # 4. Parent of executable (for dist/lac-translate structure)
            Path(sys.executable).parent.parent / ".env",
            # 5. Home directory config
            Path.home() / ".lac-translate" / ".env",
        ]
        
        for env_file in search_paths:
            if env_file.exists():
                load_dotenv(env_file)
                logger.debug(f"Loaded environment from {env_file}")
                return True
        
        logger.debug(f".env file not found in any of: {[str(p) for p in search_paths]}")
        return False
        
    except ImportError:
        logger.debug("python-dotenv not installed, skipping .env file loading")
    return False


def init_sentry(
    dsn: Optional[str] = None,
    environment: Optional[str] = None,
    sample_rate: float = 1.0,
    traces_sample_rate: float = 0.1,
    enable_tracing: bool = True,
    debug: bool = False,
    send_default_pii: bool = True,
) -> bool:
    """
    Initialize Sentry error tracking.
    
    Args:
        dsn: Sentry DSN. Falls back to SENTRY_DSN environment variable.
        environment: Environment name (production, staging, development).
                    Falls back to SENTRY_ENVIRONMENT env var.
        sample_rate: Error event sample rate (0.0 to 1.0). Default 1.0 (all errors).
        traces_sample_rate: Performance tracing sample rate. Default 0.1 (10%).
        enable_tracing: Enable performance monitoring. Default True.
        debug: Enable Sentry debug mode for troubleshooting. Default False.
        send_default_pii: Send personally identifiable information. Default True.
    
    Returns:
        True if Sentry was initialized successfully, False otherwise.
    """
    global _sentry_initialized
    
    # Load .env file first
    _load_env_file()
    
    sentry_sdk = _get_sentry_sdk()
    if not sentry_sdk:
        logger.info("Sentry SDK not available. Error tracking disabled.")
        return False
    
    # Get DSN from parameter or environment
    dsn = dsn or os.environ.get("SENTRY_DSN")
    if not dsn:
        logger.info("No Sentry DSN configured. Error tracking disabled.")
        return False
    
    # Get environment
    environment = environment or os.environ.get("SENTRY_ENVIRONMENT", "development")
    
    # Get version info
    try:
        from app.__version__ import __version__, APP_NAME
        release = f"{APP_NAME}@{__version__}"
    except ImportError:
        release = "lac-translate@unknown"
    
    try:
        # Import integrations
        from sentry_sdk.integrations.logging import LoggingIntegration
        from sentry_sdk.integrations.threading import ThreadingIntegration
        
        # Configure logging integration to capture ERROR and above as events
        logging_integration = LoggingIntegration(
            level=logging.INFO,          # Capture INFO and above as breadcrumbs
            event_level=logging.ERROR,   # Send ERROR and above as events
        )
        
        sentry_sdk.init(
            dsn=dsn,
            release=release,
            environment=environment,
            sample_rate=sample_rate,
            traces_sample_rate=traces_sample_rate if enable_tracing else 0.0,
            enable_tracing=enable_tracing,
            debug=debug,
            send_default_pii=send_default_pii,
            # Attach stack traces to logged errors
            attach_stacktrace=True,
            # Set reasonable max breadcrumbs
            max_breadcrumbs=100,
            # Integrations for better error capturing
            integrations=[
                logging_integration,
                ThreadingIntegration(propagate_hub=True),
            ],
            # Before send hook for filtering/enriching events
            before_send=_before_send,
            # Include local variables in stack traces
            include_local_variables=True,
            # Auto session tracking
            auto_session_tracking=True,
        )
        
        # Set initial context
        _set_initial_context()
        
        _sentry_initialized = True
        logger.info(f"Sentry initialized: release={release}, environment={environment}, pii={send_default_pii}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")
        return False


def _before_send(event, hint):
    """
    Process event before sending to Sentry.
    Use this to filter, modify, or enrich events.
    """
    # Filter out specific exceptions if needed
    if "exc_info" in hint:
        exc_type, exc_value, tb = hint["exc_info"]
        
        # Skip KeyboardInterrupt
        if isinstance(exc_value, KeyboardInterrupt):
            return None
        
        # Skip SystemExit with code 0 (normal exit)
        if isinstance(exc_value, SystemExit) and exc_value.code == 0:
            return None
    
    return event


def _set_initial_context():
    """Set initial context tags and data."""
    sentry_sdk = _get_sentry_sdk()
    if not sentry_sdk:
        return
    
    # System info
    sentry_sdk.set_tag("os.name", platform.system())
    sentry_sdk.set_tag("os.version", platform.version())
    sentry_sdk.set_tag("python.version", platform.python_version())
    
    # App-specific context
    try:
        from app.__version__ import VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH
        sentry_sdk.set_tag("app.version.major", str(VERSION_MAJOR))
        sentry_sdk.set_tag("app.version.minor", str(VERSION_MINOR))
        sentry_sdk.set_tag("app.version.patch", str(VERSION_PATCH))
    except ImportError:
        pass
    
    # Check for GPU availability (useful for OCR/ML debugging)
    try:
        import torch
        sentry_sdk.set_tag("cuda.available", str(torch.cuda.is_available()))
        if torch.cuda.is_available():
            sentry_sdk.set_tag("cuda.device_count", str(torch.cuda.device_count()))
    except ImportError:
        sentry_sdk.set_tag("cuda.available", "torch_not_installed")


def capture_exception(
    exception: Optional[Exception] = None,
    context: Optional[Dict[str, Any]] = None,
    level: str = "error",
    fingerprint: Optional[list] = None,
) -> Optional[str]:
    """
    Capture an exception and send it to Sentry.
    
    Args:
        exception: The exception to capture. If None, captures current exception.
        context: Additional context to attach to the event.
        level: Error level (error, warning, info, debug).
        fingerprint: Custom fingerprint for grouping similar errors.
    
    Returns:
        Event ID if captured successfully, None otherwise.
    """
    sentry_sdk = _get_sentry_sdk()
    if not sentry_sdk or not _sentry_initialized:
        return None
    
    try:
        with sentry_sdk.push_scope() as scope:
            if context:
                for key, value in context.items():
                    scope.set_extra(key, value)
            
            if level:
                scope.level = level
            
            if fingerprint:
                scope.fingerprint = fingerprint
            
            event_id = sentry_sdk.capture_exception(exception)
            return event_id
            
    except Exception as e:
        logger.warning(f"Failed to capture exception in Sentry: {e}")
        return None


def capture_message(
    message: str,
    level: str = "info",
    context: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """
    Capture a message and send it to Sentry.
    
    Args:
        message: The message to capture.
        level: Message level (error, warning, info, debug).
        context: Additional context to attach to the event.
    
    Returns:
        Event ID if captured successfully, None otherwise.
    """
    sentry_sdk = _get_sentry_sdk()
    if not sentry_sdk or not _sentry_initialized:
        return None
    
    try:
        with sentry_sdk.push_scope() as scope:
            if context:
                for key, value in context.items():
                    scope.set_extra(key, value)
            scope.level = level
            
            event_id = sentry_sdk.capture_message(message)
            return event_id
            
    except Exception as e:
        logger.warning(f"Failed to capture message in Sentry: {e}")
        return None


def add_breadcrumb(
    message: str,
    category: str = "app",
    level: str = "info",
    data: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Add a breadcrumb for debugging context.
    
    Breadcrumbs are used to create a trail of events leading up to an error.
    
    Args:
        message: Description of the event.
        category: Category for grouping (e.g., "ui", "translation", "pdf").
        level: Breadcrumb level (debug, info, warning, error).
        data: Additional data to attach.
    """
    sentry_sdk = _get_sentry_sdk()
    if not sentry_sdk or not _sentry_initialized:
        return
    
    try:
        sentry_sdk.add_breadcrumb(
            message=message,
            category=category,
            level=level,
            data=data or {},
        )
    except Exception as e:
        logger.debug(f"Failed to add breadcrumb: {e}")


def set_user(
    user_id: Optional[str] = None,
    username: Optional[str] = None,
    email: Optional[str] = None,
) -> None:
    """
    Set user information for error tracking.
    
    Note: Be mindful of privacy. Only set what is necessary for debugging.
    Consider using anonymized IDs rather than personal information.
    
    Args:
        user_id: Unique user identifier (can be anonymized).
        username: Username (optional).
        email: Email address (optional, consider privacy implications).
    """
    sentry_sdk = _get_sentry_sdk()
    if not sentry_sdk or not _sentry_initialized:
        return
    
    user_data = {}
    if user_id:
        user_data["id"] = user_id
    if username:
        user_data["username"] = username
    if email:
        user_data["email"] = email
    
    if user_data:
        sentry_sdk.set_user(user_data)


def set_tag(key: str, value: str) -> None:
    """Set a global tag for all subsequent events."""
    sentry_sdk = _get_sentry_sdk()
    if not sentry_sdk or not _sentry_initialized:
        return
    sentry_sdk.set_tag(key, value)


def set_context(name: str, data: Dict[str, Any]) -> None:
    """Set a context block with structured data."""
    sentry_sdk = _get_sentry_sdk()
    if not sentry_sdk or not _sentry_initialized:
        return
    sentry_sdk.set_context(name, data)


def configure_qt_exception_hook() -> None:
    """
    Configure exception hook to work with Qt applications.
    
    Qt has its own exception handling that can swallow Python exceptions.
    This ensures exceptions in Qt callbacks are still reported to Sentry.
    Also configures threading exception hook for Python 3.8+.
    """
    sentry_sdk = _get_sentry_sdk()
    if not sentry_sdk or not _sentry_initialized:
        return
    
    def exception_hook(exc_type, exc_value, exc_tb):
        """Custom exception hook that reports to Sentry."""
        # Skip keyboard interrupt
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return
        
        # Skip SystemExit with code 0 (normal exit)
        if issubclass(exc_type, SystemExit) and (exc_value is None or exc_value.code == 0):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return
        
        # Capture to Sentry with full context
        with sentry_sdk.push_scope() as scope:
            scope.set_tag("exception.source", "sys.excepthook")
            scope.set_tag("exception.type", exc_type.__name__)
            sentry_sdk.capture_exception((exc_type, exc_value, exc_tb))
        
        # Call default handler
        sys.__excepthook__(exc_type, exc_value, exc_tb)
    
    # Set the main exception hook
    sys.excepthook = exception_hook
    
    # Also configure threading exception hook (Python 3.8+)
    import threading
    def threading_exception_hook(args):
        """Handle uncaught exceptions in threads."""
        if args.exc_type == SystemExit:
            return
        
        with sentry_sdk.push_scope() as scope:
            scope.set_tag("exception.source", "threading.excepthook")
            scope.set_tag("exception.type", args.exc_type.__name__)
            scope.set_tag("thread.name", args.thread.name if args.thread else "unknown")
            sentry_sdk.capture_exception((args.exc_type, args.exc_value, args.exc_traceback))
        
        # Log to stderr
        logger.error(f"Uncaught exception in thread {args.thread}: {args.exc_value}", 
                     exc_info=(args.exc_type, args.exc_value, args.exc_traceback))
    
    threading.excepthook = threading_exception_hook
    
    logger.debug("Qt and threading exception hooks configured for Sentry")


def flush(timeout: float = 2.0) -> None:
    """
    Flush pending events to Sentry.
    
    Call this before application exit to ensure all events are sent.
    
    Args:
        timeout: Maximum time to wait for flush (seconds).
    """
    sentry_sdk = _get_sentry_sdk()
    if not sentry_sdk or not _sentry_initialized:
        return
    
    try:
        sentry_sdk.flush(timeout=timeout)
        logger.debug("Sentry events flushed")
    except Exception as e:
        logger.warning(f"Failed to flush Sentry events: {e}")


def is_initialized() -> bool:
    """Check if Sentry is initialized and ready."""
    return _sentry_initialized


# Convenience exports
__all__ = [
    "init_sentry",
    "capture_exception",
    "capture_message",
    "add_breadcrumb",
    "track_pdf_operation",
    "track_translation",
    "set_user",
    "set_tag",
    "set_context",
    "configure_qt_exception_hook",
    "flush",
    "is_initialized",
]
