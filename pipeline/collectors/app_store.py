"""
pipeline/collectors/app_store.py — App Store review collector (T1.3)

Fetches reviews for Blinkit using the iTunes RSS feed (India storefront).
Since Apple limits the RSS feed to ~500 recent reviews (10 pages of 50),
records are explicitly tagged `recency_limited: True` (C2, C10).

Drops rating-only reviews into an aggregate stats file to keep the corpus clean.
"""

from __future__ import annotations

import logging
import time

import requests

from pipeline.collectors.queries import APP_STORE_ID, APP_STORE_URL, classify_era
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

OUTPUT_PATH = RAW_DIR / "app_store.jsonl"
STATS_PATH = RAW_DIR / "app_store_stats.json"


def _load_stats() -> RatingAggregate:
    """Load rating aggregates or create new."""
    if not STATS_PATH.exists():
        return RatingAggregate(source="app_store")
    try:
        with STATS_PATH.open("r", encoding="utf-8") as f:
            return RatingAggregate.model_validate_json(f.read())
    except Exception:
        return RatingAggregate(source="app_store")


def _save_stats(stats: RatingAggregate) -> None:
    """Save rating aggregates."""
    STATS_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATS_PATH.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        f.write(stats.model_dump_json(indent=2))
    tmp.replace(STATS_PATH)


def fetch_page(page: int) -> list[dict]:
    """Fetch one page (1-10) of the iTunes RSS feed."""
    url = f"https://itunes.apple.com/in/rss/customerreviews/page={page}/id={APP_STORE_ID}/sortby=mostrecent/json"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    
    feed = data.get("feed", {})
    entries = feed.get("entry", [])
    
    # If it's a single entry, it's just the app metadata
    # True review entries are usually >1 in the array
    if isinstance(entries, dict):
        return []  # No reviews on this page
        
    return entries


def collect() -> None:
    """Run the App Store RSS collector."""
    setup_logging()
    logger.info("Starting App Store collection (iTunes RSS)")

    stats = _load_stats()
    corpus_added = 0
    rating_only = 0
    pages_fetched = 0

    now_iso = utc_now_iso()

    for page in range(1, 11):  # iTunes RSS is capped at 10 pages
        logger.info(f"Fetching page {page}...")
        try:
            entries = fetch_page(page)
        except Exception as exc:
            logger.error(f"Failed to fetch page {page}: {exc}")
            break

        if not entries:
            logger.info("No more entries found in feed.")
            break

        pages_fetched += 1
        
        for entry in entries:
            # Skip the first entry on page 1 if it's the app metadata rather than a review
            if "author" not in entry or "content" not in entry:
                continue

            try:
                review_id = entry["id"]["label"]
                content = entry["content"]["label"].strip()
                score_str = entry["im:rating"]["label"]
                score = int(score_str)
                title = entry.get("title", {}).get("label", "").strip()
            except (KeyError, ValueError, TypeError) as exc:
                logger.warning(f"Skipping malformed entry: {exc}")
                continue

            # In the iTunes feed, if a review has no content, it shouldn't really appear,
            # but we handle it just in case.
            if not content:
                stats.total_rating_only += 1
                if score_str in stats.rating_distribution:
                    stats.rating_distribution[score_str] += 1
                else:
                    stats.rating_distribution[score_str] = 1
                rating_only += 1
                continue
                
            # Full text combines title and content
            full_text = f"{title}\n\n{content}" if title else content
            
            # iTunes RSS doesn't give a standard date field unfortunately, but we can 
            # use a dummy or try to parse 'updated'
            date_str = entry.get("updated", {}).get("label", "")
            date_iso = normalize_utc(date_str) if date_str else now_iso
            era = classify_era(date_iso)
            
            app_version = entry.get("im:version", {}).get("label", "")
            context_str = f"App Version: {app_version}" if app_version else ""

            record = RawRecord(
                id=make_id("app", review_id),
                source="app_store",
                source_url=APP_STORE_URL,
                author_handle="",  # Anonymized
                date=date_iso,
                rating=score,
                text=full_text,
                context=context_str,
                collected_at=now_iso,
                collection_method="scraper",
                era=era,
                recency_limited=True,  # Explicitly flagged per C2
            )

            append_jsonl(OUTPUT_PATH, record.model_dump(exclude_none=True))
            corpus_added += 1

        stats.collected_at = now_iso
        _save_stats(stats)
        
        time.sleep(2)  # Polite pacing

    logger.info(
        f"Collection run complete. Pages: {pages_fetched}, "
        f"Added to corpus: {corpus_added}, "
        f"Dropped rating-only: {rating_only}"
    )


if __name__ == "__main__":
    collect()
