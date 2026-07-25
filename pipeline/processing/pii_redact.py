"""
pipeline/processing/pii_redact.py — PII Redaction (T2.4)

Regex redaction of phone numbers, emails, order IDs, and long digit runs
from all text fields (C21). Sets the `pii_redacted: True` flag if any changes occur.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

from pipeline.processing.schemas import CleanRecord
from pipeline.common import (
    DATA_DIR,
    append_jsonl,
    iter_jsonl,
    setup_logging,
)

logger = logging.getLogger(__name__)

INPUT_PATH = DATA_DIR / "intermediate" / "03_language.jsonl"
OUTPUT_PATH = DATA_DIR / "intermediate" / "04_pii_redacted.jsonl"

# ── Redaction Regexes ──────────────────────────────────────────────────────

# Matches generic phone numbers in various formats (+91 9999999999, 999-999-9999, etc.)
# We aim broadly: any sequence of 9-13 digits, optionally separated by space/dash
PHONE_RE = re.compile(r"(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{2,4}\)?[\s-]?)?\d{3,4}[\s-]?\d{3,4}[\s-]?\d{3,4}")

# Matches emails
EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")

# Matches long digits (like Order IDs, OTPs, tracking numbers) - 6 or more digits
DIGITS_RE = re.compile(r"\b\d{6,}\b")

# Blinkit/Grofers specific Order ID patterns like "ORD1234567"
ORDER_ID_RE = re.compile(r"\bORD[-_]?\d+\b", flags=re.IGNORECASE)


def redact_text(text: str) -> tuple[str, bool]:
    """Apply PII redactions to text. Returns (redacted_text, was_redacted)."""
    original = text
    
    # Apply substitutions
    text = EMAIL_RE.sub("[EMAIL]", text)
    text = ORDER_ID_RE.sub("[ORDER_ID]", text)
    
    # Phones often look like long digit runs, so replace phone first
    text = PHONE_RE.sub("[PHONE]", text)
    
    # Catch any remaining long digit sequences
    text = DIGITS_RE.sub("[DIGITS]", text)
    
    return text, text != original


def process() -> None:
    setup_logging()
    logger.info("Starting T2.4 PII Redaction...")

    if not INPUT_PATH.exists():
        logger.warning(f"Input file not found: {INPUT_PATH}")
        return

    if OUTPUT_PATH.exists():
        OUTPUT_PATH.unlink()
        
    total_processed = 0
    total_redacted = 0
    
    for rec_dict in iter_jsonl(INPUT_PATH):
        total_processed += 1
        rec = CleanRecord.model_validate(rec_dict)
        
        # Redact main text
        clean_text, redacted_text = redact_text(rec.text)
        rec.text = clean_text
        
        # Redact raw text
        clean_text_raw, redacted_raw = redact_text(rec.text_raw)
        rec.text_raw = clean_text_raw
        
        # Redact context
        clean_context, redacted_context = redact_text(rec.context)
        rec.context = clean_context
        
        if redacted_text or redacted_raw or redacted_context:
            rec.pii_redacted = True
            total_redacted += 1
            
        append_jsonl(OUTPUT_PATH, rec.model_dump(exclude_none=True))

    logger.info(
        f"PII Redaction complete. "
        f"Processed: {total_processed}, "
        f"Items with redactions: {total_redacted}"
    )


if __name__ == "__main__":
    process()
