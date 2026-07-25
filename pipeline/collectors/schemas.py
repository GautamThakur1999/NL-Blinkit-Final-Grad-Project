"""
pipeline/collectors/schemas.py — raw record schema (ARCHITECTURE §3.1)

Every collector emits records validated against this schema and writes
immediately to ``data/raw/<source>.jsonl``.  A crash never loses data (C9).
Author handles are anonymized/omitted at write time (C21-partial).
"""

from __future__ import annotations

import hashlib
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, model_validator


class RawRecord(BaseModel):
    """Schema for a single collected data item across all sources."""

    id: str = Field(
        ..., description="Unique ID: <source_prefix>-<source_specific_id>"
    )
    source: Literal["play_store", "app_store", "reddit", "forum", "social"] = Field(
        ..., description="Data source identifier"
    )
    source_url: str = Field(
        ..., description="Public URL for traceability (app page or permalink)"
    )
    author_handle: str = Field(
        default="", description="Anonymized or omitted (C21)"
    )
    date: str = Field(
        ..., description="UTC ISO-8601 datetime of the original post/review"
    )
    rating: Optional[int] = Field(
        default=None, description="Star rating 1-5 (reviews only), null otherwise"
    )
    text: str = Field(
        ..., description="Verbatim user text"
    )
    context: str = Field(
        default="", description="Thread title / app version / query that surfaced it"
    )
    collected_at: str = Field(
        ..., description="UTC ISO-8601 timestamp of collection"
    )
    collection_method: Literal["scraper", "api", "curated"] = Field(
        ..., description="How the item was obtained"
    )

    # ── Extended metadata (added by specific collectors) ──────────────────
    era: Optional[Literal["grofers", "blinkit"]] = Field(
        default=None,
        description="Brand era based on date vs Dec-2021 rebrand (C11)",
    )
    recency_limited: bool = Field(
        default=False,
        description="True if source only provides recent items, e.g. App Store RSS (C2)",
    )
    supplementary: bool = Field(
        default=False,
        description="True for curated/supplementary sources (C20)",
    )
    subreddit: Optional[str] = Field(
        default=None, description="Reddit subreddit name (Reddit records only)"
    )
    canonical_url: Optional[str] = Field(
        default=None, description="Canonical URL for cross-post dedup (C16)"
    )

    @model_validator(mode="after")
    def text_must_not_be_empty(self) -> "RawRecord":
        if not self.text or not self.text.strip():
            raise ValueError("Record text must not be empty")
        return self


class RatingAggregate(BaseModel):
    """Aggregate stats for rating-only reviews (C3: dropped from corpus)."""

    source: str
    total_rating_only: int = 0
    rating_distribution: dict[str, int] = Field(
        default_factory=lambda: {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
    )
    collected_at: str = ""


def make_id(prefix: str, unique_part: str) -> str:
    """Create a deterministic record ID: ``<prefix>-<unique_part>``."""
    return f"{prefix}-{unique_part}"


def make_hash_id(prefix: str, text: str, url: str = "") -> str:
    """Create a hash-based record ID for sources without stable IDs."""
    content = f"{url}|{text[:200]}"
    h = hashlib.sha256(content.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}-{h}"
