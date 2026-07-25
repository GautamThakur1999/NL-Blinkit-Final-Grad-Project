"""
pipeline/collectors/play_store.py — Play Store review collector (T1.2)

Fetches reviews for Blinkit using google-play-scraper.
Pins the storefront to India (gl=IN).
Uses a progress cursor to resume after interruptions.
Drops rating-only reviews into an aggregate stats file to keep the corpus clean (C3).
Strips developer replies by only capturing the user's `content`.

Edge cases closed: C1, C3, C7, C10.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

from google_play_scraper import Sort, reviews
from google_play_scraper.features.reviews import _ContinuationToken

from pipeline.collectors.queries import PLAY_STORE_APP_ID, PLAY_STORE_URL, classify_era
from pipeline.collectors.schemas import RatingAggregate, RawRecord, make_id
from pipeline.common import (
    DATA_DIR,
    RAW_DIR,
    append_jsonl,
    normalize_utc,
    setup_logging,
    utc_now_iso,
)

logger = logging.getLogger(__name__)

# ── Paths ──────────────────────────────────────────────────────────────────
CURSOR_PATH = DATA_DIR / "state" / "play_store_cursor.json"
OUTPUT_PATH = RAW_DIR / "play_store.jsonl"
STATS_PATH = RAW_DIR / "play_store_stats.json"

# ── Config ─────────────────────────────────────────────────────────────────
FETCH_COUNT = 199  # Reviews per page
MAX_PAGES = 1000   # Max pages per run to prevent infinite hang


def _load_cursor() -> _ContinuationToken | None:
    """Load the continuation token from disk if it exists."""
    if not CURSOR_PATH.exists():
        return None
    try:
        with CURSOR_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
            return _ContinuationToken(
                token=data["token"],
                lang=data.get("lang", "en"),
                country=data.get("country", "in"),
                sort=data.get("sort", Sort.NEWEST),
                count=data.get("count", FETCH_COUNT),
                filter_score_with=data.get("filter_score_with", None),
                filter_device_with=data.get("filter_device_with", None),
            )
    except Exception as exc:
        logger.warning(f"Failed to load cursor, starting fresh: {exc}")
        return None


def _save_cursor(token: _ContinuationToken | None) -> None:
    """Save the continuation token to disk atomically."""
    CURSOR_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not token:
        # Done or no token
        if CURSOR_PATH.exists():
            CURSOR_PATH.unlink()
        return

    tmp = CURSOR_PATH.with_suffix(".tmp")
    data = {
        "token": token.token,
        "lang": token.lang,
        "country": token.country,
        "sort": token.sort,
        "count": token.count,
        "filter_score_with": token.filter_score_with,
        "filter_device_with": token.filter_device_with,
    }
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f)
    tmp.replace(CURSOR_PATH)


def _load_stats() -> RatingAggregate:
    """Load rating aggregates or create new."""
    if not STATS_PATH.exists():
        return RatingAggregate(source="play_store")
    try:
        with STATS_PATH.open("r", encoding="utf-8") as f:
            return RatingAggregate.model_validate_json(f.read())
    except Exception:
        return RatingAggregate(source="play_store")


def _save_stats(stats: RatingAggregate) -> None:
    """Save rating aggregates."""
    STATS_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATS_PATH.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        f.write(stats.model_dump_json(indent=2))
    tmp.replace(STATS_PATH)


def collect() -> None:
    """Run the Play Store collector."""
    setup_logging()
    logger.info("Starting Play Store collection (India storefront pinned)")

    continuation_token = _load_cursor()
    stats = _load_stats()
    
    pages = 0
    total_reviews_this_run = 0
    corpus_added = 0
    rating_only = 0

    while pages < MAX_PAGES:
        logger.info(f"Fetching page {pages + 1}...")
        try:
            result, continuation_token = reviews(
                PLAY_STORE_APP_ID,
                lang="en",
                country="in",
                sort=Sort.NEWEST,
                count=FETCH_COUNT,
                continuation_token=continuation_token,
            )
        except Exception as exc:
            logger.error(f"Fetch failed: {exc}")
            break

        if not result:
            logger.info("No more reviews found.")
            break

        total_reviews_this_run += len(result)
        now_iso = utc_now_iso()

        for r in result:
            content = (r.get("content") or "").strip()
            score = r.get("score")

            # Handle rating-only reviews (C3)
            if not content:
                stats.total_rating_only += 1
                if score is not None:
                    score_str = str(score)
                    if score_str in stats.rating_distribution:
                        stats.rating_distribution[score_str] += 1
                rating_only += 1
                continue

            # Build corpus record
            date_iso = normalize_utc(str(r.get("at")))
            era = classify_era(date_iso)
            
            # Use app version as context if available
            app_version = r.get("reviewCreatedVersion") or r.get("appVersion")
            context_str = f"App Version: {app_version}" if app_version else ""

            record = RawRecord(
                id=make_id("play", r["reviewId"]),
                source="play_store",
                source_url=PLAY_STORE_URL,
                author_handle="",  # Anonymized (C21)
                date=date_iso,
                rating=score,
                text=content,
                context=context_str,
                collected_at=now_iso,
                collection_method="scraper",
                era=era,
            )

            # Write to corpus
            append_jsonl(OUTPUT_PATH, record.model_dump(exclude_none=True))
            corpus_added += 1

        # Save state after each page
        stats.collected_at = now_iso
        _save_stats(stats)
        _save_cursor(continuation_token)
        
        pages += 1
        
        if not continuation_token:
            logger.info("End of available reviews reached.")
            break
            
        time.sleep(1.5)  # Polite pacing

    logger.info(
        f"Collection run complete. Pages: {pages}, "
        f"Fetched: {total_reviews_this_run}, "
        f"Added to corpus: {corpus_added}, "
        f"Dropped rating-only: {rating_only}"
    )


if __name__ == "__main__":
    collect()
