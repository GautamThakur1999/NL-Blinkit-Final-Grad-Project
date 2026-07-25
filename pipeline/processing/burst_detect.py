"""
pipeline/processing/burst_detect.py — Burst Detection (T2.5)

Detects timestamp-clusters on normalized UTC dates.
If a single day sees a high volume of reviews (e.g. > mean + 2*sigma, or > N threshold),
items inside that date spike get `burst_flag: true` (C5, P7).
"""

from __future__ import annotations

import logging
import statistics
from collections import defaultdict
from pathlib import Path

from pipeline.processing.schemas import CleanRecord
from pipeline.common import (
    DATA_DIR,
    append_jsonl,
    iter_jsonl,
    setup_logging,
)

logger = logging.getLogger(__name__)

INPUT_PATH = DATA_DIR / "intermediate" / "04_pii_redacted.jsonl"
OUTPUT_PATH = DATA_DIR / "intermediate" / "05_burst_detected.jsonl"

# To define a burst, a day must have at least MIN_BURST_VOLUME items
# AND be > (mean + 2*sigma) of the daily averages.
MIN_BURST_VOLUME = 50


def process() -> None:
    setup_logging()
    logger.info("Starting T2.5 Burst Detection...")

    if not INPUT_PATH.exists():
        logger.warning(f"Input file not found: {INPUT_PATH}")
        return

    if OUTPUT_PATH.exists():
        OUTPUT_PATH.unlink()

    records: list[CleanRecord] = []
    daily_counts: dict[str, int] = defaultdict(int)

    # 1. Load data and count by day (YYYY-MM-DD)
    for rec_dict in iter_jsonl(INPUT_PATH):
        rec = CleanRecord.model_validate(rec_dict)
        records.append(rec)
        # date is ISO-8601 like "2024-01-01T12:00:00Z"
        day = rec.date[:10]
        daily_counts[day] += 1

    if not daily_counts:
        logger.info("No data to process.")
        return

    # 2. Calculate mean and standard deviation
    counts = list(daily_counts.values())
    mean_count = statistics.mean(counts)
    
    if len(counts) > 1:
        stdev = statistics.stdev(counts)
    else:
        stdev = 0.0

    threshold = mean_count + (2 * stdev)
    
    # 3. Identify burst days
    burst_days = set()
    for day, count in daily_counts.items():
        if count >= MIN_BURST_VOLUME and count > threshold:
            burst_days.add(day)

    logger.info(
        f"Burst detection stats: mean={mean_count:.1f}, stdev={stdev:.1f}, "
        f"threshold={threshold:.1f}. Found {len(burst_days)} burst days."
    )

    total_burst_flagged = 0
    
    # 4. Write records with burst flag updated
    for rec in records:
        day = rec.date[:10]
        if day in burst_days:
            rec.burst_flag = True
            total_burst_flagged += 1
        else:
            rec.burst_flag = False
            
        append_jsonl(OUTPUT_PATH, rec.model_dump(exclude_none=True))

    logger.info(f"Burst Detection complete. Items flagged as burst: {total_burst_flagged}")


if __name__ == "__main__":
    process()
