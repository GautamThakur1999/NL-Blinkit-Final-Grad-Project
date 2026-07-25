"""
pipeline/processing/language.py — Language Filter (T2.3)

Keeps English + Latin-script Hinglish.
Detects regional scripts (Devanagari, Tamil, Bengali, etc.) and sets them aside.
They are never silently discarded (C8, P1).
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

INPUT_PATH = DATA_DIR / "intermediate" / "02_deduped.jsonl"
OUTPUT_PATH = DATA_DIR / "intermediate" / "03_language.jsonl"
DROPPED_PATH = DATA_DIR / "intermediate" / "03_language_dropped.jsonl"

# Match Indic scripts: U+0900 to U+0DFF covers most Indian scripts 
# (Devanagari, Bengali, Gurmukhi, Gujarati, Oriya, Tamil, Telugu, Kannada, Malayalam, Sinhala)
INDIC_SCRIPT_RE = re.compile(r"[\u0900-\u0DFF]")


def process() -> None:
    setup_logging()
    logger.info("Starting T2.3 Language Filtering...")

    if not INPUT_PATH.exists():
        logger.warning(f"Input file not found: {INPUT_PATH}")
        return

    if OUTPUT_PATH.exists():
        OUTPUT_PATH.unlink()
    if DROPPED_PATH.exists():
        DROPPED_PATH.unlink()
        
    total_processed = 0
    total_kept = 0
    total_dropped = 0
    
    for rec_dict in iter_jsonl(INPUT_PATH):
        total_processed += 1
        rec = CleanRecord.model_validate(rec_dict)
        
        # Check text and context for Indic scripts
        text_to_check = rec.text + " " + rec.context
        if INDIC_SCRIPT_RE.search(text_to_check):
            rec.language_kept = False
            total_dropped += 1
            append_jsonl(DROPPED_PATH, rec.model_dump(exclude_none=True))
        else:
            rec.language_kept = True
            total_kept += 1
            append_jsonl(OUTPUT_PATH, rec.model_dump(exclude_none=True))

    logger.info(
        f"Language filtering complete. "
        f"Processed: {total_processed}, "
        f"Kept (Latin/Hinglish): {total_kept}, "
        f"Set aside (Regional scripts): {total_dropped}"
    )


if __name__ == "__main__":
    process()
