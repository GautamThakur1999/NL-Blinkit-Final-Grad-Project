"""
pipeline/processing/schemas.py — Processing schema

Defines the structure for records flowing through Stage 2 (Normalize & Filter).
Inherits from RawRecord and adds fields needed for the clean corpus.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import Field

from pipeline.collectors.schemas import RawRecord


class CleanRecord(RawRecord):
    """Schema for a processed data item in the clean corpus."""

    text_raw: str = Field(
        ..., description="Untouched original text (verbatim quote ground truth)"
    )
    # The inherited 'text' field is redefined conceptually as the normalized version
    
    burst_flag: bool = Field(
        default=False, description="True if item falls within a review-bombing burst"
    )
    pii_redacted: bool = Field(
        default=False, description="True if PII redaction rules modified the text"
    )
    language_kept: bool = Field(
        default=True, description="True if kept by language filter (Latin/Hinglish)"
    )
    relevant_to_category_behavior: Optional[Literal["yes", "partial", "no"]] = Field(
        default=None, description="Groq LLM relevance score"
    )
    relevance_rationale: Optional[str] = Field(
        default=None, description="One-line rationale from Groq scoring"
    )
    relevance_pass: Optional[Literal["keyword", "llm"]] = Field(
        default=None, description="Which pass determined the relevance"
    )

    @classmethod
    def from_raw(cls, raw: RawRecord) -> CleanRecord:
        """Create a CleanRecord from a RawRecord with defaults."""
        data = raw.model_dump()
        data["text_raw"] = data["text"]
        return cls(**data)
