"""
LAC Translate - Version Information

This module provides centralized version information for the application.
Used by Sentry, build scripts, and UI components.

Versioning follows Semantic Versioning (SemVer): MAJOR.MINOR.PATCH
- MAJOR: Breaking changes or major rewrites
- MINOR: New features, backward compatible
- PATCH: Bug fixes, backward compatible

Pre-release tags: alpha, beta, rc (release candidate)
"""
from datetime import datetime
from typing import Dict, Any

# ============================================
# Version Numbers
# ============================================

VERSION_MAJOR = 0
VERSION_MINOR = 1
VERSION_PATCH = 6
VERSION_PRERELEASE = ""  # e.g., "alpha", "beta", "rc.1", or "" for stable

# Build metadata (auto-generated or set by CI/CD)
BUILD_DATE = "2026-01-26"
BUILD_NUMBER = ""  # Set by CI/CD pipeline, e.g., "1234"


# ============================================
# Computed Version Strings
# ============================================

def get_version() -> str:
    """
    Get the full version string.
    
    Examples:
        "3.1.0"
        "3.1.0-beta"
        "3.1.0-rc.1"
    """
    version = f"{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_PATCH}"
    if VERSION_PRERELEASE:
        version = f"{version}-{VERSION_PRERELEASE}"
    return version


def get_version_with_build() -> str:
    """
    Get version with build metadata for detailed tracking.
    
    Examples:
        "3.1.0+20260123"
        "3.1.0-beta+build.1234"
    """
    version = get_version()
    
    # Add build metadata
    if BUILD_NUMBER:
        version = f"{version}+build.{BUILD_NUMBER}"
    elif BUILD_DATE:
        # Use date as build identifier if no build number
        date_str = BUILD_DATE.replace("-", "")
        version = f"{version}+{date_str}"
    
    return version


def get_version_info() -> Dict[str, Any]:
    """
    Get complete version information as a dictionary.
    Useful for Sentry context and debug logging.
    """
    return {
        "version": get_version(),
        "version_full": get_version_with_build(),
        "major": VERSION_MAJOR,
        "minor": VERSION_MINOR,
        "patch": VERSION_PATCH,
        "prerelease": VERSION_PRERELEASE or None,
        "build_date": BUILD_DATE,
        "build_number": BUILD_NUMBER or None,
        "is_stable": not VERSION_PRERELEASE,
        "is_development": VERSION_PRERELEASE in ("alpha", "beta", "dev"),
    }


def get_user_agent() -> str:
    """
    Get a user-agent style string for API calls and logging.
    
    Example: "LACTranslate/3.1.0 (Linux; Python 3.11)"
    """
    import sys
    import platform
    
    os_name = platform.system()
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    
    return f"LACTranslate/{get_version()} ({os_name}; Python {py_version})"


# ============================================
# Module-level exports
# ============================================

__version__ = get_version()
__version_info__ = (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)

# Human-readable application info
APP_NAME = "LAC Translate"
APP_AUTHOR = "LUCERTAE SRLS"
APP_DESCRIPTION = "Professional PDF Translation with OPUS-MT and PaddleOCR"


if __name__ == "__main__":
    # Quick test when run directly
    print(f"Application: {APP_NAME}")
    print(f"Version: {__version__}")
    print(f"Full version: {get_version_with_build()}")
    print(f"User-Agent: {get_user_agent()}")
    print(f"\nVersion info:")
    for key, value in get_version_info().items():
        print(f"  {key}: {value}")
