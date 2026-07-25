"""
pipeline/processing/composition_report.py — Corpus Composition (T2.8)

Generates corpus composition stats:
- Source mix
- Ops-vs-Category-Signal ratio (from relevance passes)
- Sentiment mix (from ratings where available)
This makes class imbalance visible and honestly reported in METHODOLOGY.md (P6).
"""

from __future__ import annotations

import json
import logging
from collections import Counter
from pathlib import Path

from pipeline.common import (
    ANALYSIS_DIR,
    DATA_DIR,
    iter_jsonl,
    setup_logging,
)

logger = logging.getLogger(__name__)

CORPUS_PATH = DATA_DIR / "clean" / "corpus.jsonl"
REPORT_PATH = ANALYSIS_DIR / "composition_report.json"


def generate_report() -> None:
    setup_logging()
    logger.info("Generating Composition Report for the clean corpus...")

    if not CORPUS_PATH.exists():
        logger.warning(f"Corpus not found at {CORPUS_PATH}")
        return

    total_records = 0
    source_mix: Counter[str] = Counter()
    relevance_mix: Counter[str] = Counter()
    pass_mix: Counter[str] = Counter()
    rating_mix: Counter[str] = Counter()
    burst_count = 0
    pii_redacted_count = 0

    for rec in iter_jsonl(CORPUS_PATH):
        total_records += 1
        source_mix[rec.get("source", "unknown")] += 1
        
        rel = rec.get("relevant_to_category_behavior", "unknown")
        relevance_mix[rel] += 1
        
        rel_pass = rec.get("relevance_pass", "unknown")
        pass_mix[rel_pass] += 1
        
        rating = rec.get("rating")
        if rating is not None:
            # 1-3 is negative, 4-5 is positive (rough proxy)
            r = int(rating)
            if r <= 3:
                rating_mix["negative_1_to_3"] += 1
            else:
                rating_mix["positive_4_to_5"] += 1
                
        if rec.get("burst_flag"):
            burst_count += 1
            
        if rec.get("pii_redacted"):
            pii_redacted_count += 1

    report = {
        "total_records": total_records,
        "source_mix": dict(source_mix),
        "relevance_mix": dict(relevance_mix),
        "relevance_pass_mix": dict(pass_mix),
        "sentiment_proxy": dict(rating_mix),
        "burst_flagged": burst_count,
        "pii_redacted": pii_redacted_count,
    }

    print("=" * 50)
    print("COMPOSITION REPORT")
    print("=" * 50)
    print(json.dumps(report, indent=2))
    print("=" * 50)

    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    with REPORT_PATH.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    logger.info(f"Report saved to {REPORT_PATH}")


if __name__ == "__main__":
    generate_report()
