"""
pipeline/validation/spotcheck.py — Human Spot-Check Sampling Tool (T4.2)

Samples 10–15% of tagged items, spread across all batches (not just early ones).
Presents them for human tag agreement review.

Pre-committed protocol:
  • If agreement < 80% → revise taxonomy/prompt → re-tag → re-check
  • Report both rounds

Edge cases closed: A7, V1.
"""

from __future__ import annotations

import json
import logging
import math
import random
from pathlib import Path

from pipeline.common import (
    ANALYSIS_DIR,
    DATA_DIR,
    iter_jsonl,
    setup_logging,
)

logger = logging.getLogger(__name__)

TAGS_PATH = DATA_DIR / "state" / "tags_results.jsonl"
CORPUS_PATH = DATA_DIR / "clean" / "corpus.jsonl"
SPOTCHECK_PATH = ANALYSIS_DIR / "spotcheck_sample.json"

SAMPLE_FRACTION = 0.12  # Target ~12% (within the 10-15% range)
AGREEMENT_THRESHOLD = 0.80


def process() -> None:
    setup_logging()
    logger.info("Starting T4.2 Spot-Check Sampling...")

    if not TAGS_PATH.exists():
        logger.warning(f"Tags file not found: {TAGS_PATH}")
        return

    # Load all tagged items
    all_tags = list(iter_jsonl(TAGS_PATH))
    if not all_tags:
        logger.info("No tagged items to sample.")
        return

    # Load corpus for the original text
    corpus_map = {}
    if CORPUS_PATH.exists():
        for rec in iter_jsonl(CORPUS_PATH):
            corpus_map[rec["id"]] = rec

    total_items = len(all_tags)
    sample_size = max(5, math.ceil(total_items * SAMPLE_FRACTION))
    sample_size = min(sample_size, total_items)

    # ── Stratified sampling across batches ──────────────────────────────────
    # We divide the item list into N equal-sized buckets and sample
    # proportionally from each to avoid early-batch bias.
    num_buckets = min(10, total_items)
    bucket_size = math.ceil(total_items / num_buckets)
    per_bucket = max(1, math.ceil(sample_size / num_buckets))

    sampled_indices: set[int] = set()
    for b in range(num_buckets):
        start = b * bucket_size
        end = min(start + bucket_size, total_items)
        bucket_indices = list(range(start, end))
        take = min(per_bucket, len(bucket_indices))
        sampled_indices.update(random.sample(bucket_indices, take))

    # Trim to exact sample_size if we oversampled
    sampled_indices_list = sorted(sampled_indices)[:sample_size]

    # ── Build the review items ─────────────────────────────────────────────
    review_items = []
    for idx in sampled_indices_list:
        tag_row = all_tags[idx]
        item_id = tag_row["item_id"]
        tag_result = tag_row["result"]
        corpus_item = corpus_map.get(item_id, {})

        review_items.append({
            "item_id": item_id,
            "text_raw": corpus_item.get("text_raw", ""),
            "context": corpus_item.get("context", ""),
            "source": corpus_item.get("source", ""),
            # AI-assigned tags for the reviewer to judge
            "ai_barriers": tag_result.get("barriers", []),
            "ai_sentiment": tag_result.get("sentiment", ""),
            "ai_key_quote": tag_result.get("key_quote", ""),
            "ai_categories": tag_result.get("categories_mentioned", []),
            # Human review fields (to be filled by the reviewer)
            "human_agrees_barriers": None,    # True / False
            "human_agrees_sentiment": None,   # True / False
            "human_agrees_quote": None,       # True / False
            "human_notes": "",
        })

    # ── Save ───────────────────────────────────────────────────────────────
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    with SPOTCHECK_PATH.open("w", encoding="utf-8") as f:
        json.dump({
            "protocol": {
                "sample_fraction": SAMPLE_FRACTION,
                "agreement_threshold": AGREEMENT_THRESHOLD,
                "total_tagged_items": total_items,
                "sample_size": len(review_items),
                "sampling_method": "stratified across batches (not just early items)",
                "pre_committed_rule": (
                    f"If agreement < {AGREEMENT_THRESHOLD:.0%}, "
                    "revise taxonomy/prompt, re-tag, re-check, "
                    "and report both rounds."
                ),
            },
            "items": review_items,
        }, f, indent=2, ensure_ascii=False)

    logger.info(
        f"Spot-check sample generated: {len(review_items)} items "
        f"({len(review_items)/total_items:.1%} of {total_items}). "
        f"Saved to {SPOTCHECK_PATH}."
    )


def compute_agreement(spotcheck_path: Path | None = None) -> dict:
    """
    After the human reviewer fills in the `human_agrees_*` fields,
    call this function to compute the agreement rate.
    """
    path = spotcheck_path or SPOTCHECK_PATH
    if not path.exists():
        return {"error": "spotcheck_sample.json not found"}

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    items = data.get("items", [])
    reviewed = [
        it for it in items
        if it.get("human_agrees_barriers") is not None
    ]

    if not reviewed:
        return {"error": "No items have been reviewed yet (human_agrees_* fields are all null)."}

    agree_barriers = sum(1 for it in reviewed if it["human_agrees_barriers"])
    agree_sentiment = sum(1 for it in reviewed if it.get("human_agrees_sentiment"))
    agree_quote = sum(1 for it in reviewed if it.get("human_agrees_quote"))
    total = len(reviewed)

    barrier_rate = agree_barriers / total
    sentiment_rate = agree_sentiment / total
    quote_rate = agree_quote / total
    overall = (agree_barriers + agree_sentiment + agree_quote) / (total * 3)

    result = {
        "reviewed_count": total,
        "barrier_agreement": f"{barrier_rate:.1%}",
        "sentiment_agreement": f"{sentiment_rate:.1%}",
        "quote_agreement": f"{quote_rate:.1%}",
        "overall_agreement": f"{overall:.1%}",
        "passed": overall >= AGREEMENT_THRESHOLD,
    }
    if not result["passed"]:
        result["action_required"] = (
            f"Overall agreement ({overall:.1%}) < {AGREEMENT_THRESHOLD:.0%}. "
            "Per protocol: revise taxonomy/prompt → re-tag → re-check."
        )
    return result


if __name__ == "__main__":
    process()
