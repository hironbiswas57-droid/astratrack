"""
AstraTrack AI - Secure Configuration & API Credential Manager

All sensitive values (API keys, secrets) are loaded from environment variables
via a .env file (which is listed in .gitignore and NEVER committed to git).

Usage:
    from .config import get_gemini_api_key, get_nasa_api_key, get_server_settings

Design:
    - Secrets are NEVER stored as module-level variables or class attributes.
    - Every secret is accessed only through a getter function.
    - Calling code receives the value; it is not stored elsewhere.
    - Validation happens at startup via validate_required_keys().
"""

import os
import logging
from pathlib import Path
from typing import Optional

# ── Auto-load .env from project root if python-dotenv is available ──────────
_ENV_LOADED = False

def _load_dotenv() -> None:
    """Load .env file once at import time. Silently skips if file is absent."""
    global _ENV_LOADED
    if _ENV_LOADED:
        return
    try:
        from dotenv import load_dotenv
        env_path = Path(__file__).resolve().parent.parent / ".env"
        if env_path.exists():
            load_dotenv(dotenv_path=env_path, override=False)
            logging.getLogger(__name__).debug(".env loaded from %s", env_path)
        else:
            logging.getLogger(__name__).warning(
                ".env file not found at %s — falling back to system environment variables.", env_path
            )
    except ImportError:
        logging.getLogger(__name__).warning(
            "python-dotenv not installed. Only system environment variables will be used. "
            "Install it with: pip install python-dotenv"
        )
    _ENV_LOADED = True


# Load on import
_load_dotenv()


# ════════════════════════════════════════════════════════════════════════════
#  GETTER FUNCTIONS  — the ONLY way to access secrets
#  These functions never cache, store, or log the values they return.
# ════════════════════════════════════════════════════════════════════════════

def get_gemini_api_key() -> Optional[str]:
    """Return the Gemini API key from environment. Returns None if not set."""
    return os.environ.get("GEMINI_API_KEY") or None


def get_openai_api_key() -> Optional[str]:
    """Return the OpenAI API key from environment. Returns None if not set."""
    return os.environ.get("OPENAI_API_KEY") or None


def get_gemini_model() -> str:
    """Return the configurable Gemini synthesis model identifier."""
    return os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")


def get_nasa_api_key() -> str:
    """
    Return the NASA API key from environment.
    Falls back to 'DEMO_KEY' (heavily rate-limited) if not set.
    """
    return os.environ.get("NASA_API_KEY") or "DEMO_KEY"


def get_jpl_horizons_base_url() -> str:
    """Return the JPL Horizons base URL (no secret, but centralised here)."""
    return os.environ.get(
        "JPL_HORIZONS_BASE_URL",
        "https://ssd.jpl.nasa.gov/api/horizons.api"
    )


def get_cors_origins() -> list[str]:
    """Return a list of allowed CORS origins parsed from CORS_ALLOWED_ORIGINS."""
    raw = os.environ.get("CORS_ALLOWED_ORIGINS", "*")
    if raw.strip() == "*":
        return ["*"]
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def get_ssl_cert_path() -> Optional[str]:
    """Return the SSL certificate path, or None if not configured."""
    return os.environ.get("SSL_CERT_PATH") or None


def get_ssl_key_path() -> Optional[str]:
    """Return the SSL private key path, or None if not configured."""
    return os.environ.get("SSL_KEY_PATH") or None


def get_log_level() -> str:
    """Return the logging level (default: INFO)."""
    return os.environ.get("LOG_LEVEL", "INFO").upper()


def get_server_settings() -> dict:
    """
    Return a dict of non-secret server settings safe to use in logging.
    ⚠️  This dict intentionally omits all API keys and secrets.
    """
    return {
        "host": os.environ.get("ASTRATRACK_HOST", "127.0.0.1"),
        "port": int(os.environ.get("ASTRATRACK_PORT", "8000")),
        "env": os.environ.get("ASTRATRACK_ENV", "development"),
        "log_level": get_log_level(),
        "cors_origins": get_cors_origins(),
    }


# ════════════════════════════════════════════════════════════════════════════
#  STARTUP VALIDATION
# ════════════════════════════════════════════════════════════════════════════

def validate_required_keys() -> list[str]:
    """
    Check that all required secrets are present in the environment.

    Returns a list of missing key NAMES (not values) so errors can be
    reported safely without ever printing the keys themselves.

    Raises RuntimeError in production mode if critical keys are absent.
    """
    missing: list[str] = []

    # Gemini key is required for the multi-agent orchestrator
    if not get_gemini_api_key():
        missing.append("GEMINI_API_KEY")

    env_mode = os.environ.get("ASTRATRACK_ENV", "development")

    if missing:
        msg = (
            f"[AstraTrack Config] Missing required environment variable(s): "
            f"{', '.join(missing)}. "
            f"Copy .env.example to .env and fill in your values."
        )
        if env_mode == "production":
            raise RuntimeError(msg)
        else:
            logging.getLogger(__name__).warning(msg)

    return missing


def is_api_key_configured(key_name: str) -> bool:
    """
    Check whether a named API key is configured, without returning its value.
    Safe to use in health-check endpoints.

    Args:
        key_name: One of 'gemini', 'openai', 'nasa'

    Returns:
        True if the key is present and non-empty, False otherwise.
    """
    _getters = {
        "gemini":  get_gemini_api_key,
        "openai":  get_openai_api_key,
        "nasa":    lambda: None if get_nasa_api_key() == "DEMO_KEY" else get_nasa_api_key(),
    }
    getter = _getters.get(key_name.lower())
    if getter is None:
        raise ValueError(f"Unknown key name: '{key_name}'. Valid options: {list(_getters)}")
    return getter() is not None
