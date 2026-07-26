"""
pipeline/processing/relevance.py — Relevance Filter (T2.6)

Two-pass filter:
1. Keyword pass: Identifies ops/quality complaints (which are partial by default and never auto-dropped).
2. Groq LLM scoring: `relevant_to_category_behavior: yes/partial/no` + one-line rationale.
Items scoring `yes` or `partial` proceed to `corpus.jsonl`.
Items scoring `no` go to `06_rejected.jsonl`.
"""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Any, Literal

from pydantic import AliasChoices, BaseModel, Field

from pipeline.processing.schemas import CleanRecord
from pipeline.common import (
    DATA_DIR,
    append_jsonl,
    iter_jsonl,
    setup_logging,
)
from pipeline.llm import get_gateway, Provider

logger = logging.getLogger(__name__)

# Which provider scores relevance. Override with RELEVANCE_PROVIDER=gemini|groq
# depending on which free tier currently has headroom.
RELEVANCE_PROVIDER = (
    Provider.GEMINI
    if os.environ.get("RELEVANCE_PROVIDER", "groq").lower() == "gemini"
    else Provider.GROQ
)

# The LLM stages run over the sampled corpus (see pipeline/processing/sample.py).
# Falls back to the full burst-detected corpus if no sample has been drawn.
_SAMPLED_PATH = DATA_DIR / "intermediate" / "06_sampled.jsonl"
_FULL_PATH = DATA_DIR / "intermediate" / "05_burst_detected.jsonl"
INPUT_PATH = _SAMPLED_PATH if _SAMPLED_PATH.exists() else _FULL_PATH
CORPUS_PATH = DATA_DIR / "clean" / "corpus.jsonl"
REJECTED_PATH = DATA_DIR / "intermediate" / "06_rejected.jsonl"
CURSOR_PATH = DATA_DIR / "state" / "relevance_cursor.json"
DEAD_LETTER_PATH = DATA_DIR / "state" / "relevance_dead_letters.jsonl"

# Ops/quality complaint keywords (H3 trust-barrier evidence)
OPS_KEYWORDS = re.compile(
    r"\b(missing|expired|rotten|late|support|refund|delivery|rude|stale|damaged|wrong item|worst service|fake|scam|fraud)\b",
    re.IGNORECASE,
)

class RelevanceScore(BaseModel):
    # Models frequently name this field "relevance" or "relevance_score" instead of
    # "score". Accepting those aliases avoids dead-lettering otherwise-valid
    # responses over a key-naming difference (A1).
    model_config = {"populate_by_name": True}

    score: Literal["yes", "partial", "no"] = Field(
        ..., validation_alias=AliasChoices("score", "relevance", "relevance_score")
    )
    rationale: str = Field(
        ..., validation_alias=AliasChoices("rationale", "reason", "explanation")
    )

def merge_only() -> None:
    """
    Fold already-scored LLM results into the corpus without making any API calls.

    Needed because the scoring stage persists results incrementally but only
    merges them into corpus.jsonl after the whole batch finishes. When a run is
    cut short by provider throttling, the completed scores are on disk yet
    absent from the corpus. This recovers them.

    Safe to re-run: items already present in the corpus are skipped.

    Usage:  python -m pipeline.processing.relevance --merge-only
    """
    setup_logging()
    llm_results_path = DATA_DIR / "state" / "relevance_llm_results.jsonl"
    if not llm_results_path.exists():
        logger.error("No scored results at %s", llm_results_path)
        return

    processed_ids: set[str] = set()
    for path in (CORPUS_PATH, REJECTED_PATH):
        if path.exists():
            for rec in iter_jsonl(path):
                processed_ids.add(rec["id"])

    source_map = {rec["id"]: rec for rec in iter_jsonl(INPUT_PATH)}

    kept = rejected = skipped = 0
    for row in iter_jsonl(llm_results_path):
        item_id = row.get("item_id")
        if not item_id or item_id in processed_ids or item_id not in source_map:
            skipped += 1
            continue

        rec = CleanRecord.model_validate(source_map[item_id])
        score_obj = RelevanceScore.model_validate(row["result"])
        rec.relevant_to_category_behavior = score_obj.score
        rec.relevance_rationale = score_obj.rationale
        rec.relevance_pass = "llm"

        if score_obj.score in ("yes", "partial"):
            append_jsonl(CORPUS_PATH, rec.model_dump(exclude_none=True))
            kept += 1
        else:
            append_jsonl(REJECTED_PATH, rec.model_dump(exclude_none=True))
            rejected += 1
        processed_ids.add(item_id)

    logger.info(
        "Merge complete. Kept: %d. Rejected: %d. Skipped (already merged): %d.",
        kept, rejected, skipped,
    )


def build_relevance_prompt(item: dict[str, Any]) -> tuple[str, str]:
    """Build the prompt for the LLM. Returns (system_msg, wrapped_data)."""
    # Kept deliberately short: free-tier throughput is limited by tokens-per-minute,
    # so every token in this system prompt is paid on every one of ~600 calls.
    system_msg = (
        "Rate Blinkit/Grofers app feedback for relevance to cross-category purchase "
        "barriers (why users stick to some categories and avoid others). "
        "Text may be English or Latin-script Hinglish.\n"
        "yes = explicitly discusses category behavior; partial = implies a barrier or "
        "habit; no = generic praise/unrelated.\n"
        'Output only JSON with exactly these keys: {"score":"yes|partial|no",'
        '"rationale":"one short sentence"}'
    )
    full_text = f"Context: {item.get('context', '')}\nReview: {item['text']}"

    return system_msg, full_text

def process() -> None:
    setup_logging()
    logger.info("Starting T2.6 Relevance Filtering...")

    if not INPUT_PATH.exists():
        logger.warning(f"Input file not found: {INPUT_PATH}")
        return

    # To support resume, we read what's already in the corpus/rejected
    # However, since we use `batch_process` from LLMGateway which has its own cursor,
    # we can rely on that for the LLM part. But we need to avoid re-running the keyword pass.
    # To keep it simple, we process entirely in memory if small, or use the cursor.
    # Since we have ~10k items, we'll separate them into keyword-pass and LLM-pass.
    
    CORPUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # We will just overwrite corpus/rejected on fresh run.
    # If the cursor exists, we are resuming.
    is_resume = CURSOR_PATH.exists()
    if not is_resume:
        if CORPUS_PATH.exists():
            CORPUS_PATH.unlink()
        if REJECTED_PATH.exists():
            REJECTED_PATH.unlink()

    # We need to track processed IDs to not duplicate in corpus during a resume.
    processed_ids = set()
    if is_resume:
        for p in [CORPUS_PATH, REJECTED_PATH]:
            if p.exists():
                for rec in iter_jsonl(p):
                    processed_ids.add(rec["id"])

    llm_items = []
    
    total_keyword_partial = 0
    total_queued_llm = 0

    for rec_dict in iter_jsonl(INPUT_PATH):
        rec_id = rec_dict["id"]
        if rec_id in processed_ids:
            continue
            
        rec = CleanRecord.model_validate(rec_dict)
        text_lower = (rec.text + " " + rec.context).lower()
        
        # Pass 1: Keyword Match
        if OPS_KEYWORDS.search(text_lower):
            rec.relevant_to_category_behavior = "partial"
            rec.relevance_rationale = "Auto-classified: ops/quality complaint"
            rec.relevance_pass = "keyword"
            
            append_jsonl(CORPUS_PATH, rec.model_dump(exclude_none=True))
            processed_ids.add(rec_id)
            total_keyword_partial += 1
        else:
            # Pass 2: Queue for LLM
            llm_items.append(rec.model_dump())
            total_queued_llm += 1

    logger.info(f"Pass 1: Auto-classified {total_keyword_partial} items via keywords.")
    logger.info(f"Pass 2: Sending {total_queued_llm} items to Groq LLM...")

    if not llm_items:
        logger.info("No items require LLM scoring.")
        return

    LLM_RESULTS_PATH = DATA_DIR / "state" / "relevance_llm_results.jsonl"
    
    gateway = get_gateway()
    gateway.batch_process(
        items=llm_items,
        item_id_key="id",
        prompt_builder=build_relevance_prompt,
        schema=RelevanceScore,
        # Provider is configurable because the two free tiers fail in different
        # ways and recover on different clocks: Groq caps tokens-per-minute
        # (throttles a long run), Gemini caps requests-per-day (hard stop until
        # reset). Whichever has headroom at run time should be used, so this is
        # an env setting rather than a hardcoded choice.
        provider=RELEVANCE_PROVIDER,
        batch_name="relevance",
        output_path=LLM_RESULTS_PATH,
        cursor_path=CURSOR_PATH,
        dead_letter_path=DEAD_LETTER_PATH,
    )
    
    total_llm_kept = 0
    total_llm_rejected = 0

    llm_items_map = {item["id"]: CleanRecord.model_validate(item) for item in llm_items}

    if LLM_RESULTS_PATH.exists():
        for row in iter_jsonl(LLM_RESULTS_PATH):
            item_id = row["item_id"]
            if item_id in processed_ids:
                continue
                
            # If the item isn't in our current memory map, we can't reconstruct it.
            # But since it wasn't in processed_ids, it SHOULD be in llm_items_map.
            if item_id not in llm_items_map:
                continue
                
            rec = llm_items_map[item_id]
            score_obj = RelevanceScore.model_validate(row["result"])
            
            rec.relevant_to_category_behavior = score_obj.score
            rec.relevance_rationale = score_obj.rationale
            rec.relevance_pass = "llm"
            
            if score_obj.score in ["yes", "partial"]:
                append_jsonl(CORPUS_PATH, rec.model_dump(exclude_none=True))
                total_llm_kept += 1
            else:
                append_jsonl(REJECTED_PATH, rec.model_dump(exclude_none=True))
                total_llm_rejected += 1
            
            processed_ids.add(item_id)

    logger.info(
        f"Relevance Filtering complete. "
        f"Keyword kept: {total_keyword_partial}. "
        f"LLM kept: {total_llm_kept}. "
        f"LLM rejected: {total_llm_rejected}."
    )


if __name__ == "__main__":
    import sys

    if "--merge-only" in sys.argv:
        merge_only()
    else:
        process()
