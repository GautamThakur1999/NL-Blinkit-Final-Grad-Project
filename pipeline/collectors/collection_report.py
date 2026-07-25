"""
pipeline/collectors/collection_report.py — Collection Report (T1.7)

Generates per-source counts, date ranges, regional-script counts (Devanagari),
and era split (Grofers vs Blinkit). Feeds METHODOLOGY.md.
"""

from __future__ import annotations

import json
import logging
import re
from collections import Counter
from pathlib import Path

from pipeline.common import RAW_DIR, ANALYSIS_DIR, iter_jsonl, setup_logging

logger = logging.getLogger(__name__)

REPORT_PATH = ANALYSIS_DIR / "collection_report.json"

# Regex to detect Devanagari characters (Hindi/Marathi etc.)
_DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")


def generate_report() -> None:
    """Read all raw JSONL files and generate an aggregated collection report."""
    setup_logging()
    logger.info("Generating Collection Report...")

    # Aggregators
    total_records = 0
    source_counts: Counter[str] = Counter()
    era_counts: Counter[str] = Counter()
    script_counts = {"devanagari": 0, "latin_only": 0}
    
    earliest_date = "9999-99-99"
    latest_date = "0000-00-00"
    
    # Process all JSONL files in the raw directory
    if not RAW_DIR.exists():
        logger.warning(f"Raw directory {RAW_DIR} does not exist.")
        return

    for file_path in RAW_DIR.glob("*.jsonl"):
        logger.info(f"Scanning {file_path.name}...")
        for rec in iter_jsonl(file_path):
            total_records += 1
            
            source = rec.get("source", "unknown")
            source_counts[source] += 1
            
            era = rec.get("era", "unknown")
            era_counts[era] += 1
            
            date = rec.get("date", "")
            if date:
                if date < earliest_date:
                    earliest_date = date
                if date > latest_date:
                    latest_date = date
                    
            text = rec.get("text", "")
            if _DEVANAGARI_RE.search(text):
                script_counts["devanagari"] += 1
            else:
                script_counts["latin_only"] += 1

    report = {
        "total_records": total_records,
        "date_range": {
            "earliest": earliest_date if earliest_date != "9999-99-99" else None,
            "latest": latest_date if latest_date != "0000-00-00" else None,
        },
        "by_source": dict(source_counts),
        "by_era": dict(era_counts),
        "by_script": script_counts,
    }
    
    # Print summary
    print("=" * 50)
    print("COLLECTION REPORT")
    print("=" * 50)
    print(f"Total Corpus Records: {total_records}")
    print(f"Date Range: {report['date_range']['earliest']} to {report['date_range']['latest']}")
    print("\nBy Source:")
    for k, v in report["by_source"].items():
        print(f"  {k}: {v}")
    print("\nBy Era:")
    for k, v in report["by_era"].items():
        print(f"  {k}: {v}")
    print("\nBy Script:")
    print(f"  Devanagari present: {report['by_script']['devanagari']}")
    print(f"  Latin only: {report['by_script']['latin_only']}")
    print("=" * 50)

    # Save to disk
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    with REPORT_PATH.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    logger.info(f"Report saved to {REPORT_PATH}")


if __name__ == "__main__":
    generate_report()
