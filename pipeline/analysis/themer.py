"""
pipeline/analysis/themer.py — Cross-source clustering (T3.3)

Uses Gemini to cluster tagged items into themes per barrier.
Enforces the admission rule: >= N items from >= 2 source types.
Sub-threshold themes are flagged as weak signals.
Outputs to data/analysis/themes.json.
"""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from typing import Any

from pipeline.analysis.schemas import ThemerResponse, Theme, ThemeEvidence
from pipeline.common import (
    ANALYSIS_DIR,
    DATA_DIR,
    iter_jsonl,
    setup_logging,
)
from pipeline.llm import Provider, get_gateway

logger = logging.getLogger(__name__)

CORPUS_PATH = DATA_DIR / "clean" / "corpus.jsonl"
TAGS_PATH = DATA_DIR / "state" / "tags_results.jsonl"  # Output of tagger batch process
THEMES_PATH = ANALYSIS_DIR / "themes.json"

# Thresholds for robust themes
MIN_EVIDENCE_COUNT = 3


def load_data() -> dict[str, list[dict]]:
    """Loads corpus and tags, and groups by barrier."""
    # 1. Load corpus to get source, url, burst_flag
    corpus_map = {}
    if CORPUS_PATH.exists():
        for rec in iter_jsonl(CORPUS_PATH):
            corpus_map[rec["id"]] = rec

    # 2. Load tags and group by barrier
    barrier_groups = defaultdict(list)
    if TAGS_PATH.exists():
        for row in iter_jsonl(TAGS_PATH):
            item_id = row["item_id"]
            if item_id not in corpus_map:
                continue
                
            tag_data = row["result"]
            corpus_item = corpus_map[item_id]
            
            # Skip empty or "none" quotes unless barrier is "none"
            quote = tag_data.get("key_quote", "").strip()
            if not quote or quote.lower() == "none":
                if "none" not in tag_data.get("barriers", []):
                    continue

            for barrier in tag_data.get("barriers", []):
                evidence = {
                    "item_id": item_id,
                    "quote": quote,
                    "url": corpus_item.get("url", ""),
                    "source": corpus_item.get("source", "unknown"),
                    "burst_flag": corpus_item.get("burst_flag", False)
                }
                barrier_groups[barrier].append(evidence)

    return barrier_groups


def _apply_admission_rules(theme: Theme) -> None:
    """Applies programmatic admission rules (C5, A10, A11)."""
    # Rule 1: Must have >= MIN_EVIDENCE_COUNT
    if len(theme.evidence) < MIN_EVIDENCE_COUNT:
        theme.is_weak_signal = True
        theme.weak_signal_reason = f"Less than {MIN_EVIDENCE_COUNT} evidence items."
        return

    # Rule 2: Must have >= 2 source types
    sources = {e.source for e in theme.evidence}
    if len(sources) < 2:
        theme.is_weak_signal = True
        theme.weak_signal_reason = "Supported by only 1 source type (needs triangulation)."
        return

    # Rule 3: Cannot be solely constituted by burst-flagged items
    non_burst = [e for e in theme.evidence if not e.burst_flag]
    if len(non_burst) == 0:
        theme.is_weak_signal = True
        theme.weak_signal_reason = "Solely constituted by burst-flagged (review-bombing) items."
        return

    theme.is_weak_signal = False
    theme.weak_signal_reason = None


def process() -> None:
    setup_logging()
    logger.info("Starting T3.3 Cross-source Clustering (Themer)...")

    barrier_groups = load_data()
    if not barrier_groups:
        logger.warning("No tagged data found or tags are empty.")
        return

    gateway = get_gateway()
    all_themes = []

    for barrier, items in barrier_groups.items():
        if barrier == "none":
            continue

        logger.info(f"Clustering {len(items)} items for barrier: {barrier}")
        
        system_msg = (
            "You are an expert consumer behavior analyst synthesizing e-commerce feedback.\n"
            f"Your task is to cluster the provided evidence items for the barrier '{barrier}' into distinct themes.\n"
            "CRITICAL RULES:\n"
            "1. You must return a structured JSON response matching the requested schema.\n"
            "2. Group items that share the underlying root cause or specific pain point.\n"
            "3. Aim for 2-5 themes depending on the variance in the data. Do NOT create one massive theme holding all items.\n"
            "4. EVERY single evidence item provided MUST be placed into exactly one theme. Do not drop any evidence.\n"
            "5. You MUST include the full 'evidence' array in your output for each theme, exactly copying the provided item structures."
        )

        user_content = json.dumps({"evidence_items": items}, indent=2)
        
        # We use Gemini due to its large context window for clustering
        try:
            parsed_res, meta = gateway.call(
                provider=Provider.GEMINI,
                system_prompt=system_msg,
                user_content=user_content,
                schema=ThemerResponse,
                temperature=0.2
            )
            
            for theme in parsed_res.themes:
                theme.barrier = barrier
                _apply_admission_rules(theme)
                all_themes.append(theme.model_dump())
                
        except Exception as e:
            logger.error(f"Failed to cluster barrier {barrier}: {e}")

    # Save themes
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    with THEMES_PATH.open("w", encoding="utf-8") as f:
        json.dump({"themes": all_themes}, f, indent=2, ensure_ascii=False)

    logger.info(f"Theming complete. Generated {len(all_themes)} themes. Saved to {THEMES_PATH}")


if __name__ == "__main__":
    process()
