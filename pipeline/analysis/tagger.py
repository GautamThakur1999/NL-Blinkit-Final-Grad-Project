"""
pipeline/analysis/tagger.py — Structured Tagging (T3.2)

Uses Groq (low temperature) to tag items according to the Stage 3 schema.
Enforces a programmatic verbatim check on the key_quote.
Long items chunked, resumable batches.
"""

from __future__ import annotations

import logging
from typing import Any

from pipeline.analysis.schemas import TaggedItemSchema, current_raw_text
from pipeline.analysis.taxonomy import get_taxonomy_prompt_text
from pipeline.common import (
    ANALYSIS_DIR,
    DATA_DIR,
    iter_jsonl,
    setup_logging,
)
from pipeline.llm import Provider, get_gateway

logger = logging.getLogger(__name__)

CORPUS_PATH = DATA_DIR / "clean" / "corpus.jsonl"


def build_tagger_prompt(item: dict[str, Any]) -> tuple[str, str]:
    """
    Builds the tagging prompt and injects the raw text into the context variable
    so the Pydantic validator can verify the verbatim quote.
    """
    # 1. Inject raw text for validation
    text_raw = item.get("text_raw", "")
    current_raw_text.set(text_raw)
    
    # 2. Build system prompt
    taxonomy_text = get_taxonomy_prompt_text()
    system_msg = (
        "You are an expert consumer behavior analyst reviewing e-commerce feedback for Blinkit/Grofers.\n"
        "Your task is to extract structured insights from the provided text.\n\n"
        f"{taxonomy_text}\n"
        "CRITICAL INSTRUCTIONS:\n"
        "1. You MUST output valid JSON conforming strictly to the requested schema.\n"
        "2. The 'key_quote' field MUST be an EXACT, VERBATIM substring copied directly from the provided text. Do not summarize or alter the quote. If there is no relevant quote, and the barrier is 'none', output 'none' for key_quote.\n"
        "3. Map the barriers to hypotheses correctly: H1 (habit_loop), H2 (low_awareness), H3 (trust_quality), H4 (discovery_friction), H5 (missing_information).\n"
    )
    
    # 3. Build user prompt
    full_text = f"Context: {item.get('context', '')}\nReview: {text_raw}"
    
    return system_msg, full_text


def process() -> None:
    setup_logging()
    logger.info("Starting T3.2 Structured Tagging...")

    if not CORPUS_PATH.exists():
        logger.warning(f"Corpus not found: {CORPUS_PATH}")
        return

    items = list(iter_jsonl(CORPUS_PATH))
    if not items:
        logger.info("Corpus is empty.")
        return

    gateway = get_gateway()
    
    # Run the batch process
    # Output automatically goes to DATA_DIR/state/tags_results.jsonl (or ANALYSIS_DIR)
    # We will let batch_process use its default analysis dir: ANALYSIS_DIR / "tags_results.jsonl"
    results = gateway.batch_process(
        items=items,
        item_id_key="id",
        prompt_builder=build_tagger_prompt,
        schema=TaggedItemSchema,
        provider=Provider.GROQ,
        batch_name="tags",
        temperature=0.1,  # Low temperature for analytical extraction
    )
    
    logger.info(f"Tagging complete. Processed {len(results)} items in this run.")
    # The output is safely persisted in ANALYSIS_DIR / "tags_results.jsonl" by batch_process.


if __name__ == "__main__":
    process()
