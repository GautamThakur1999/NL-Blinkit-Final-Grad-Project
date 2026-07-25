"""
pipeline/processing/sample.py — corpus sampling for LLM stages

Why this step exists
--------------------
The LLM gateway makes one call per item. On the free tiers used by this project
(Groq: ~30 RPM and a daily request cap; Gemini: daily token/request quotas),
scoring all ~4,667 processed records would exceed the daily allowance and take
hours. Instead the LLM stages run over a **random sample** drawn with a fixed
seed, which is:

  • reproducible  — same seed + same input file => same sample
  • unbiased      — simple random sample, no cherry-picking of "good" reviews
  • documented    — the sample size, seed, and sampling frame are written to
                    data/analysis/sampling_report.json and reported in
                    METHODOLOGY.md as a stated limitation

This is a sampling decision driven by cost, not a filtering decision — it happens
BEFORE relevance scoring so it cannot bias which barriers get surfaced.

Usage:
    python -m pipeline.processing.sample            # default sample size
    python -m pipeline.processing.sample --size 500
"""

from __future__ import annotations

import argparse
import json
import logging
import random

from pipeline.common import (
    ANALYSIS_DIR,
    DATA_DIR,
    iter_jsonl,
    setup_logging,
    utc_now_iso,
    write_jsonl,
)

logger = logging.getLogger(__name__)

INTERMEDIATE_DIR = DATA_DIR / "intermediate"
INPUT_PATH = INTERMEDIATE_DIR / "05_burst_detected.jsonl"
OUTPUT_PATH = INTERMEDIATE_DIR / "06_sampled.jsonl"
REPORT_PATH = ANALYSIS_DIR / "sampling_report.json"

DEFAULT_SAMPLE_SIZE = 800
RANDOM_SEED = 20260726


def process(sample_size: int = DEFAULT_SAMPLE_SIZE, seed: int = RANDOM_SEED) -> None:
    """Draw a seeded simple random sample from the processed corpus."""
    setup_logging()
    logger.info("Starting corpus sampling (size=%d, seed=%d)", sample_size, seed)

    population = list(iter_jsonl(INPUT_PATH))
    if not population:
        logger.error("No input records at %s — run the processing pipeline first.", INPUT_PATH)
        return

    total = len(population)

    if sample_size >= total:
        logger.info("Sample size >= population (%d); using the full corpus.", total)
        sampled = population
    else:
        # Stratified by source: minority sources (e.g. App Store, Reddit) are
        # taken in full, the majority source fills the remaining budget. A
        # proportional sample would leave too few minority-source items to
        # satisfy the >=2-source triangulation rule for themes (C5/A11).
        rng = random.Random(seed)
        by_source: dict[str, list[dict]] = {}
        for rec in population:
            by_source.setdefault(rec.get("source", "unknown"), []).append(rec)

        # Smallest strata first so their full inclusion is guaranteed
        strata = sorted(by_source.items(), key=lambda kv: len(kv[1]))
        sampled = []
        remaining_budget = sample_size
        for idx, (source, records) in enumerate(strata):
            strata_left = len(strata) - idx
            # Reserve nothing for later strata beyond what they can supply
            fair_share = max(remaining_budget // strata_left, 0)
            take = min(len(records), max(fair_share, 0)) if strata_left > 1 else min(
                len(records), remaining_budget
            )
            # Small strata: take everything available
            if len(records) <= fair_share or strata_left == 1:
                take = min(len(records), remaining_budget)
            chosen = records if take >= len(records) else rng.sample(records, take)
            sampled.extend(chosen)
            remaining_budget -= len(chosen)

        rng.shuffle(sampled)

    write_jsonl(OUTPUT_PATH, sampled)

    # Composition of the sample vs the population, so any skew is visible
    def _by_source(records: list[dict]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for r in records:
            counts[r.get("source", "unknown")] = counts.get(r.get("source", "unknown"), 0) + 1
        return counts

    report = {
        "generated_at": utc_now_iso(),
        "sampling_frame": str(INPUT_PATH.name),
        "population_size": total,
        "sample_size": len(sampled),
        "sampling_method": (
            "stratified random sample without replacement; minority sources taken "
            "in full, majority source randomly sampled to fill the budget"
        ),
        "random_seed": seed,
        "reason": (
            "Free-tier LLM quotas (Groq daily request cap, Gemini daily quota) make "
            "per-item scoring of the full corpus infeasible. Sampling occurs before "
            "relevance scoring so it cannot bias which barriers are surfaced."
        ),
        "population_by_source": _by_source(population),
        "sample_by_source": _by_source(sampled),
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with REPORT_PATH.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    logger.info(
        "Sampled %d of %d records -> %s", len(sampled), total, OUTPUT_PATH.name
    )
    logger.info("Sample composition by source: %s", report["sample_by_source"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Sample the processed corpus for LLM stages.")
    parser.add_argument("--size", type=int, default=DEFAULT_SAMPLE_SIZE)
    parser.add_argument("--seed", type=int, default=RANDOM_SEED)
    args = parser.parse_args()
    process(sample_size=args.size, seed=args.seed)


if __name__ == "__main__":
    main()
