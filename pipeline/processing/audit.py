"""
pipeline/processing/audit.py — Rejection Audit (T2.7)

Randomly samples ~50 records that were rejected by the LLM as irrelevant.
Outputs them to `audit_sample.json` so the researcher can manually review them
for false negatives before freezing the corpus (P3).
"""

from __future__ import annotations

import json
import logging
import random
from pathlib import Path

from pipeline.common import (
    ANALYSIS_DIR,
    DATA_DIR,
    iter_jsonl,
    setup_logging,
)

logger = logging.getLogger(__name__)

REJECTED_PATH = DATA_DIR / "intermediate" / "06_rejected.jsonl"
AUDIT_OUTPUT_PATH = ANALYSIS_DIR / "rejection_audit_sample.json"

SAMPLE_SIZE = 50


def process() -> None:
    setup_logging()
    logger.info("Starting T2.7 Rejection Audit Sampling...")

    if not REJECTED_PATH.exists():
        logger.warning(f"Rejected items file not found: {REJECTED_PATH}")
        return

    all_rejected = []
    for rec_dict in iter_jsonl(REJECTED_PATH):
        # We only want to audit items rejected by the LLM pass
        if rec_dict.get("relevance_pass") == "llm" and rec_dict.get("relevant_to_category_behavior") == "no":
            all_rejected.append(rec_dict)

    if not all_rejected:
        logger.info("No LLM-rejected items found to audit.")
        return

    # Randomly sample up to SAMPLE_SIZE
    sample = random.sample(all_rejected, min(len(all_rejected), SAMPLE_SIZE))

    # Format for easy manual review
    audit_data = []
    for item in sample:
        audit_data.append({
            "id": item.get("id"),
            "text": item.get("text"),
            "rationale": item.get("relevance_rationale"),
            "is_false_negative": False,  # For the researcher to toggle manually
            "notes": ""
        })

    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    with AUDIT_OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(audit_data, f, indent=2, ensure_ascii=False)

    logger.info(
        f"Sampled {len(sample)} rejected items out of {len(all_rejected)} total. "
        f"Saved to {AUDIT_OUTPUT_PATH}. "
        f"Please review them for false negatives."
    )


if __name__ == "__main__":
    process()
