"""
pipeline/common.py — cross-cutting utilities (T0.4)

Provides:
  * UTF-8-explicit file I/O (Windows defaults to cp1252 -- we override everywhere)
  * JSONL read / write / append
  * UTC ISO-8601 date normalizer
  * ASCII-safe console logger
  * pathlib-based directory helpers

All subsequent pipeline modules MUST use these helpers instead of raw open() / json.

Edge cases closed: P2 (encoding corruption), P7 (timestamp chaos), X1 (Windows quirks).
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

# ── Project root (repo top-level) ──────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
CLEAN_DIR = DATA_DIR / "clean"
ANALYSIS_DIR = DATA_DIR / "analysis"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"


# ── Directory bootstrapping ────────────────────────────────────────────────
def ensure_dirs() -> None:
    """Create the standard data directories if they don't exist."""
    for d in (RAW_DIR, CLEAN_DIR, ANALYSIS_DIR, OUTPUTS_DIR):
        d.mkdir(parents=True, exist_ok=True)


# ── UTF-8 file I/O helpers ─────────────────────────────────────────────────
def read_text(path: Path) -> str:
    """Read an entire text file with explicit UTF-8 encoding."""
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    """Write text to a file with explicit UTF-8 encoding, creating parents."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# ── JSONL helpers ──────────────────────────────────────────────────────────
def read_jsonl(path: Path) -> list[dict[str, Any]]:
    """Read all records from a .jsonl file. Returns [] if the file is missing."""
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                records.append(json.loads(stripped))
            except json.JSONDecodeError as exc:
                logging.getLogger(__name__).warning(
                    "Skipping malformed JSON at %s:%d -- %s", path.name, lineno, exc
                )
    return records


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    """Lazily iterate records from a .jsonl file (for large files)."""
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if stripped:
                yield json.loads(stripped)


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    """Overwrite a .jsonl file with *records*, one JSON object per line."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    """Append a single record to a .jsonl file (crash-safe: one write per call)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


# ── UTC ISO-8601 date normalizer ──────────────────────────────────────────
def normalize_utc(date_string: str) -> str:
    """
    Best-effort parse of a date(time) string -> UTC ISO-8601.

    Handles:
      * ISO-8601 with or without timezone
      * Unix timestamps (int / float as string)
      * Common human formats: "Jul 18, 2025", "18/07/2025", "2025-07-18"

    Returns the ISO-8601 UTC string, or the original string unchanged if
    parsing fails (the caller decides whether to reject).
    """
    if not date_string or not isinstance(date_string, str):
        return date_string  # type: ignore[return-value]

    text = date_string.strip()

    # Attempt 1: Unix timestamp
    try:
        ts = float(text)
        if 1_000_000_000 < ts < 2_000_000_000:  # plausible epoch seconds
            return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
        if 1_000_000_000_000 < ts < 2_000_000_000_000:  # epoch millis
            return datetime.fromtimestamp(ts / 1000, tz=timezone.utc).isoformat()
    except (ValueError, OverflowError):
        pass

    # Attempt 2: ISO-8601
    try:
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    except ValueError:
        pass

    # Attempt 3: Common formats
    for fmt in (
        "%b %d, %Y",          # "Jul 18, 2025"
        "%B %d, %Y",          # "July 18, 2025"
        "%d/%m/%Y",           # "18/07/2025"
        "%m/%d/%Y",           # "07/18/2025"
        "%Y/%m/%d",           # "2025/07/18"
        "%d %b %Y",           # "18 Jul 2025"
        "%d %B %Y",           # "18 July 2025"
        "%Y-%m-%d %H:%M:%S",  # "2025-07-18 14:30:00"
    ):
        try:
            dt = datetime.strptime(text, fmt).replace(tzinfo=timezone.utc)
            return dt.isoformat()
        except ValueError:
            continue

    # Give up -- return original
    return date_string


def utc_now_iso() -> str:
    """Current UTC time as ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


# ── ASCII-safe console logging ─────────────────────────────────────────────
def setup_logging(level: int = logging.INFO) -> None:
    """
    Configure root logger for ASCII-safe console output.

    Windows consoles can choke on Unicode in log messages, so we force
    ASCII encoding on the stream handler with 'replace' error handling.
    """
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    )
    # Force ASCII-safe output on Windows
    if hasattr(handler.stream, "reconfigure"):
        handler.stream.reconfigure(encoding="ascii", errors="replace")

    root = logging.getLogger()
    root.setLevel(level)
    # Avoid duplicate handlers if called more than once
    if not root.handlers:
        root.addHandler(handler)


# ── Convenience ────────────────────────────────────────────────────────────
def count_jsonl(path: Path) -> int:
    """Count records in a JSONL file without loading all into memory."""
    if not path.exists():
        return 0
    count = 0
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                count += 1
    return count
