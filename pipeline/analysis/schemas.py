"""
pipeline/analysis/schemas.py — Schemas for Phase 3 (T3.2)
"""

from __future__ import annotations

import contextvars
from typing import Literal

from pydantic import BaseModel, model_validator

# We use a ContextVar to pass the raw text down into the Pydantic validator
# so we can enforce the verbatim quote rule strictly during LLM validation,
# triggering automatic retries if the LLM hallucinates a quote.
current_raw_text = contextvars.ContextVar("current_raw_text", default="")

class TaggedItemSchema(BaseModel):
    barriers: list[str]
    categories_mentioned: list[str]
    channel_alternatives: list[str]
    discovery_mode: Literal["search", "reorder", "browse", "promo", "word_of_mouth", "accidental", "null"]
    segment_hints: list[str]
    sentiment: Literal["positive", "negative", "mixed", "neutral"]
    key_quote: str
    maps_to_hypotheses: list[str]

    @model_validator(mode='after')
    def verify_quote(self) -> TaggedItemSchema:
        """Programmatic verbatim check (C15, A6)."""
        raw_text = current_raw_text.get()
        if not raw_text:
            # If not set (e.g. testing), bypass
            return self
            
        quote = self.key_quote.strip()
        # If the quote is "none" or empty, we allow it only if barriers == ["none"]
        if not quote or quote.lower() == "none":
            if "none" not in self.barriers:
                raise ValueError("key_quote cannot be empty unless barrier is 'none'.")
            return self

        # We do a lowercased, whitespace-normalized substring check
        def normalize(s: str) -> str:
            return " ".join(s.lower().split())
            
        if normalize(quote) not in normalize(raw_text):
            raise ValueError(
                f"Verbatim check failed! The key_quote '{quote}' "
                f"was not found in the original text. You must extract an EXACT substring."
            )
            
        return self

class ThemeEvidence(BaseModel):
    item_id: str
    quote: str
    url: str
    source: str
    burst_flag: bool

class Theme(BaseModel):
    theme_name: str
    description: str
    barrier: str
    evidence: list[ThemeEvidence]
    is_weak_signal: bool
    weak_signal_reason: str | None = None

class ThemerResponse(BaseModel):
    themes: list[Theme]

class InsightScorecard(BaseModel):
    hypothesis_id: Literal["H1_habit_loop", "H2_low_awareness", "H3_trust_quality", "H4_discovery_friction", "H5_missing_information", "emergent"]
    evidence_strength: Literal["strong", "moderate", "weak", "contradicted"]
    finding_summary: str
    supporting_theme_names: list[str]

class Insight(BaseModel):
    research_question_id: Literal["Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8"]
    insight_title: str
    synthesis_narrative: str
    scorecards: list[InsightScorecard]

class InsightsResponse(BaseModel):
    insights: list[Insight]

class Contradiction(BaseModel):
    insight_title: str
    contradicting_quote: str
    explanation: str

class CounterEvidenceResponse(BaseModel):
    contradictions: list[Contradiction]
