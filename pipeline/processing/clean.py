"""
pipeline/processing/clean.py — Normalize and Filter (T2.1)

Reads raw records, normalizes whitespace, strips emojis/noise into the `text` field,
preserves the original untouched text in `text_raw`, and drops items that are
too short (e.g., emoji-only or one-word reviews).
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

import emoji

from pipeline.collectors.schemas import RawRecord
from pipeline.processing.schemas import CleanRecord
from pipeline.common import (
    DATA_DIR,
    RAW_DIR,
    append_jsonl,
    iter_jsonl,
    setup_logging,
)

logger = logging.getLogger(__name__)

INTERMEDIATE_DIR = DATA_DIR / "intermediate"
OUTPUT_PATH = INTERMEDIATE_DIR / "01_clean.jsonl"

MIN_TOKENS = 2  # Drop anything with fewer than 2 tokens (e.g. just "good" or "👍")

def clean_text(text: str) -> str:
    """Normalize whitespace and strip emojis."""
    # 1. Remove emojis
    text_no_emoji = emoji.replace_emoji(text, replace='')
    # 2. Normalize whitespace (collapse multiple spaces/newlines)
    text_normalized = re.sub(r'\s+', ' ', text_no_emoji).strip()
    return text_normalized

def count_tokens(text: str) -> int:
    """Simple word count proxy."""
    return len(text.split())

def process() -> None:
    setup_logging()
    logger.info("Starting T2.1 Text Cleaning & Token Filter...")

    INTERMEDIATE_DIR.mkdir(parents=True, exist_ok=True)
    
    # Overwrite if exists to allow re-runs (C9)
    if OUTPUT_PATH.exists():
        OUTPUT_PATH.unlink()
        
    total_raw = 0
    total_kept = 0
    total_dropped = 0

    if not RAW_DIR.exists():
        logger.warning(f"No raw data found in {RAW_DIR}")
        return

    for file_path in RAW_DIR.glob("*.jsonl"):
        logger.info(f"Processing {file_path.name}...")
        for raw_dict in iter_jsonl(file_path):
            total_raw += 1
            
            raw_record = RawRecord.model_validate(raw_dict)
            clean_record = CleanRecord.from_raw(raw_record)
            
            # Perform cleaning
            clean_record.text = clean_text(clean_record.text_raw)
            
            # Check minimum token filter
            if count_tokens(clean_record.text) < MIN_TOKENS:
                total_dropped += 1
                continue
                
            # Keep
            append_jsonl(OUTPUT_PATH, clean_record.model_dump(exclude_none=True))
            total_kept += 1

    logger.info(
        f"Cleaning complete. "
        f"Raw items: {total_raw}, "
        f"Kept: {total_kept}, "
        f"Dropped (too short): {total_dropped}"
    )

if __name__ == "__main__":
    process()
