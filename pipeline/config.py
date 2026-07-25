"""
pipeline/config.py — environment configuration loader (T0.5)

Keys are ONLY read from environment variables (loaded from .env via
python-dotenv).  No secrets ever appear in code, configs, or commits.

Edge cases closed: M8 (secrets leakage).
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from pipeline.common import PROJECT_ROOT

# Load .env from project root (if it exists)
_env_path = PROJECT_ROOT / ".env"
load_dotenv(_env_path)


def _require(name: str) -> str:
    """Return an env var's value or raise with a helpful message."""
    value = os.environ.get(name)
    if not value:
        raise EnvironmentError(
            f"Missing required environment variable: {name}\n"
            f"Copy .env.example -> .env and fill in your keys."
        )
    return value


def _optional(name: str, default: str = "") -> str:
    """Return an env var's value or the default."""
    return os.environ.get(name, default)


# ── API Keys ───────────────────────────────────────────────────────────────
def gemini_api_key() -> str:
    """Gemini API key — required for synthesis stages."""
    return _require("GEMINI_API_KEY")


def groq_api_key() -> str:
    """Groq API key — required for high-volume tagging."""
    return _require("GROQ_API_KEY")


# ── Reddit OAuth (optional) ────────────────────────────────────────────────
# Reddit returns HTTP 403 to unauthenticated API requests since the 2023 API
# changes. Free "script" app credentials (https://www.reddit.com/prefs/apps)
# restore access. Optional: without them the Reddit collector is skipped and
# the omission is documented as a collection limitation.
def reddit_client_id() -> str:
    """Reddit OAuth client id — optional; empty string if unset."""
    return _optional("REDDIT_CLIENT_ID")


def reddit_client_secret() -> str:
    """Reddit OAuth client secret — optional; empty string if unset."""
    return _optional("REDDIT_CLIENT_SECRET")


# ── Model defaults ─────────────────────────────────────────────────────────
# These can be overridden via env vars if model versions change.
# Note: `gemini-2.5-flash*` returns 404 for keys created after its retirement
# to new users, and `gemini-2.0-flash` free-tier quota exhausts quickly.
# `gemini-flash-latest` is the current working free-tier alias.
GEMINI_MODEL = _optional("GEMINI_MODEL", "gemini-flash-latest")
GROQ_MODEL = _optional("GROQ_MODEL", "llama-3.3-70b-versatile")

# ── Rate limits (requests per minute) ──────────────────────────────────────
GEMINI_RPM = int(_optional("GEMINI_RPM", "15"))
GROQ_RPM = int(_optional("GROQ_RPM", "30"))
