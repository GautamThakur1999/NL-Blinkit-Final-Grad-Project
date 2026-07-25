"""
pipeline/collectors/curated.py — Forums & Social curated collector (T1.5)

Ingests manually collected items from sources that cannot/should not be scraped
automatically (e.g., login-gated Facebook groups, niche forums, Quora).
Adheres to C20, C23: no circumvention of login walls. The researcher manually
saves items into `data/curated_inputs.jsonl` with public URLs.

This script validates them, adds the `supplementary: True` and
`collection_method: curated` flags, and appends them to `data/raw/curated.jsonl`.
"""

from __future__ import annotations

import logging
from pathlib import Path

from pipeline.collectors.queries import classify_era
from pipeline.collectors.schemas import RawRecord, make_hash_id
from pipeline.common import (
    DATA_DIR,
    RAW_DIR,
    append_jsonl,
    iter_jsonl,
    normalize_utc,
    setup_logging,
    utc_now_iso,
)

logger = logging.getLogger(__name__)

INPUT_PATH = DATA_DIR / "curated_inputs.jsonl"
OUTPUT_PATH = RAW_DIR / "curated.jsonl"


def collect() -> None:
    """Run the curated data ingestor."""
    setup_logging()
    logger.info("Starting Curated Data Ingestion")

    if not INPUT_PATH.exists():
        logger.info(f"No curated inputs found at {INPUT_PATH}. Skipping.")
        # Create an empty template file so the user knows where to put data
        INPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with INPUT_PATH.open("w", encoding="utf-8") as f:
            f.write(
                '{"url": "https://example.com/post1", "text": "...", '
                '"date": "2025-01-01", "source": "forum", "context": "Thread title"}\n'
            )
        return

    corpus_added = 0
    now_iso = utc_now_iso()
    
    # Track existing IDs to avoid duplicates if run multiple times
    existing_ids = set()
    if OUTPUT_PATH.exists():
        for rec in iter_jsonl(OUTPUT_PATH):
            existing_ids.add(rec.get("id"))

    for item in iter_jsonl(INPUT_PATH):
        try:
            url = item.get("url", "").strip()
            text = item.get("text", "").strip()
            source = item.get("source", "forum")
            
            if not url or not text:
                logger.warning(f"Skipping malformed curated item: missing url or text")
                continue
                
            if source not in ["forum", "social"]:
                source = "forum"

            date_str = item.get("date", "")
            date_iso = normalize_utc(date_str) if date_str else now_iso
            era = classify_era(date_iso)
            
            context_str = item.get("context", "").strip()
            
            # Curated items often don't have stable numeric IDs, use a content hash
            record_id = make_hash_id(source, text, url)
            
            if record_id in existing_ids:
                continue

            record = RawRecord(
                id=record_id,
                source=source,
                source_url=url,
                author_handle="",  # Anonymized (C21)
                date=date_iso,
                rating=None,
                text=text,
                context=context_str,
                collected_at=now_iso,
                collection_method="curated",
                era=era,
                supplementary=True,  # Explicitly flagged per C20
            )

            append_jsonl(OUTPUT_PATH, record.model_dump(exclude_none=True))
            existing_ids.add(record_id)
            corpus_added += 1
            
        except Exception as exc:
            logger.error(f"Error processing curated item: {exc}")

    logger.info(f"Curated ingestion complete. Added to corpus: {corpus_added}")


if __name__ == "__main__":
    collect()
