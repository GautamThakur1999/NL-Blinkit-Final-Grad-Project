"""
pipeline/processing/dedupe.py — Deduplication (T2.2)

Identifies near-duplicates using RapidFuzz and cross-posts using canonical URLs.
Keeps the earliest instance of a duplicate cluster (C6, C16, P4).
"""

from __future__ import annotations

import logging
from collections import defaultdict
from pathlib import Path

from rapidfuzz import fuzz

from pipeline.processing.schemas import CleanRecord
from pipeline.common import (
    DATA_DIR,
    append_jsonl,
    iter_jsonl,
    setup_logging,
)

logger = logging.getLogger(__name__)

INPUT_PATH = DATA_DIR / "intermediate" / "01_clean.jsonl"
OUTPUT_PATH = DATA_DIR / "intermediate" / "02_deduped.jsonl"

FUZZY_THRESHOLD = 90.0  # Normalized similarity threshold (0-100)


def process() -> None:
    setup_logging()
    logger.info("Starting T2.2 Deduplication...")

    if not INPUT_PATH.exists():
        logger.warning(f"Input file not found: {INPUT_PATH}")
        return

    if OUTPUT_PATH.exists():
        OUTPUT_PATH.unlink()
        
    records: list[CleanRecord] = []
    
    # 1. Load all records (memory is fine for ~10k-100k items)
    for rec_dict in iter_jsonl(INPUT_PATH):
        records.append(CleanRecord.model_validate(rec_dict))
        
    # Sort by date so we always encounter the earliest instance first
    records.sort(key=lambda r: r.date)
    
    seen_urls = set()
    kept_records = []
    
    # We will maintain a list of kept texts for fuzzy matching.
    # To optimize fuzzy matching, we can group by length or exact matches first.
    # For now, a naive O(N^2) over the kept set is acceptable for small corpus,
    # but we can optimize by only comparing strings of similar length.
    kept_texts = []
    
    total_exact_or_url_dupes = 0
    total_fuzzy_dupes = 0
    
    # Sort optimization: block lengths
    def length_bucket(text: str) -> int:
        return len(text) // 10

    # Bucket -> list of (text, record_id)
    text_buckets: dict[int, list[str]] = defaultdict(list)

    for i, rec in enumerate(records):
        if i % 1000 == 0 and i > 0:
            logger.info(f"Processed {i}/{len(records)} records...")
            
        # 1. Canonical URL check (cross-posts)
        canonical_url = getattr(rec, "canonical_url", rec.source_url)
        if canonical_url and canonical_url in seen_urls:
            total_exact_or_url_dupes += 1
            continue
            
        text = rec.text
        bucket = length_bucket(text)
        
        is_dupe = False
        
        # 2. Fuzzy match against nearby length buckets
        # (Difference in string length bounds the RapidFuzz ratio, so we only check close lengths)
        for b in [bucket - 1, bucket, bucket + 1]:
            for existing_text in text_buckets[b]:
                if fuzz.ratio(text, existing_text) >= FUZZY_THRESHOLD:
                    is_dupe = True
                    total_fuzzy_dupes += 1
                    break
            if is_dupe:
                break
                
        if not is_dupe:
            seen_urls.add(canonical_url)
            text_buckets[bucket].append(text)
            kept_records.append(rec)
            append_jsonl(OUTPUT_PATH, rec.model_dump(exclude_none=True))

    logger.info(
        f"Deduplication complete. "
        f"Total evaluated: {len(records)}, "
        f"URL/Exact dupes dropped: {total_exact_or_url_dupes}, "
        f"Fuzzy dupes dropped: {total_fuzzy_dupes}, "
        f"Kept: {len(kept_records)}"
    )


if __name__ == "__main__":
    process()
