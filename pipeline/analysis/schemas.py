"""
pipeline/analysis/schemas.py — Schemas for Phase 3 (T3.2)
"""

from __future__ import annotations

import contextvars
from typing import Literal

from pydantic import BaseModel, field_validator, model_validator

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

class BatchTaggedItem(BaseModel):
    """
    One item inside a batched tagging response.

    Deliberately has NO verbatim validator: a single ContextVar cannot describe
    several source texts at once. The caller re-validates each entry through
    ``TaggedItemSchema`` with that item's own raw text bound, so the verbatim
    guarantee is enforced per item exactly as in the single-item path.

    ``index`` refers to the 1-based REVIEW number in the prompt. Short integers
    are used instead of the full record ids because ids are ~10 tokens each and
    the whole point of batching is token economy.
    """

    index: int
    barriers: list[str] = []
    categories_mentioned: list[str] = []
    channel_alternatives: list[str] = []
    # Models emit JSON null here rather than the string "null" when no discovery
    # mode is evident. Accept both and normalise, otherwise a whole batch is
    # dead-lettered over a null vs "null" difference.
    discovery_mode: str | None = None
    segment_hints: list[str] = []
    sentiment: str = "neutral"
    key_quote: str | None = None
    maps_to_hypotheses: list[str] = []

    @field_validator("discovery_mode", mode="before")
    @classmethod
    def _discovery_null(cls, v: object) -> str:
        # TaggedItemSchema.discovery_mode is a Literal that includes "null"
        return "null" if v is None else str(v)

    @field_validator("key_quote", mode="before")
    @classmethod
    def _quote_null(cls, v: object) -> str:
        # "none" is the sentinel the verbatim validator recognises for
        # "no relevant quote" — not "null"
        if v is None:
            return "none"
        return "none" if str(v).strip().lower() in {"null", ""} else str(v)

    @field_validator("barriers", "maps_to_hypotheses", mode="before")
    @classmethod
    def _none_to_empty(cls, v: object) -> object:
        return [] if v is None else v


class BatchTagResponse(BaseModel):
    results: list[BatchTaggedItem]


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
