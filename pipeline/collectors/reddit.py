"""
pipeline/collectors/reddit.py — Reddit JSON API collector (T1.4)

Uses the public Reddit JSON API to search for keywords across target subreddits.
Skips deleted/removed posts and known bots (AutoModerator).
Stores thread title in context. Uses the post permalink as canonical_URL.
Throttles requests to comply with Reddit API guidelines.

Edge cases closed: C11, C12, C13, C16, C17, C18, C19.
"""

from __future__ import annotations

import logging
import time
from urllib.parse import urljoin

import requests

from pipeline.collectors.brand_guard import is_blinkit_related
from pipeline.collectors.queries import SUBREDDITS, classify_era, get_all_queries
from pipeline.collectors.schemas import RawRecord, make_id
from pipeline.config import reddit_client_id, reddit_client_secret
from pipeline.common import (
    RAW_DIR,
    append_jsonl,
    normalize_utc,
    setup_logging,
    utc_now_iso,
)

logger = logging.getLogger(__name__)

OUTPUT_PATH = RAW_DIR / "reddit.jsonl"
REDDIT_BASE = "https://www.reddit.com"
REDDIT_OAUTH_BASE = "https://oauth.reddit.com"
USER_AGENT = "windows:blinkit-category-research:v1.0 (research pipeline)"

# Reddit blocks unauthenticated JSON API access (HTTP 403) as of the 2023 API
# changes. Free "script" app credentials restore access:
#   1. https://www.reddit.com/prefs/apps -> "create another app..." -> type: script
#   2. Put the client id and secret in .env as REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET
# Without credentials the collector exits cleanly and the run proceeds with the
# remaining sources (documented as a limitation, never silently skipped).
_TOKEN_CACHE: dict[str, str] = {}


def get_access_token() -> str | None:
    """
    Obtain an app-only OAuth token. Returns None if credentials are absent
    or rejected (caller then skips Reddit collection).
    """
    if "token" in _TOKEN_CACHE:
        return _TOKEN_CACHE["token"]

    client_id = reddit_client_id()
    client_secret = reddit_client_secret()
    if not client_id or not client_secret:
        return None

    try:
        resp = requests.post(
            f"{REDDIT_BASE}/api/v1/access_token",
            auth=(client_id, client_secret),
            data={"grant_type": "client_credentials"},
            headers={"User-Agent": USER_AGENT},
            timeout=20,
        )
        resp.raise_for_status()
        token = resp.json().get("access_token")
    except Exception as exc:
        logger.error("Reddit OAuth failed: %s", exc)
        return None

    if not token:
        return None
    _TOKEN_CACHE["token"] = token
    return token

# ── Boilerplate / Bot filters ──────────────────────────────────────────────
_KNOWN_BOTS = {"AutoModerator", "RemindMeBot", "imguralbumbot"}
_DELETED_TEXTS = {"[deleted]", "[removed]"}


def _is_valid_post(post_data: dict) -> bool:
    """Filter out deleted content, bots, and empty posts (C12, C13, C17)."""
    author = post_data.get("author", "")
    if author in _KNOWN_BOTS:
        return False

    text = post_data.get("selftext", "").strip()
    title = post_data.get("title", "").strip()
    
    # Must have some text (either title or body)
    if not text and not title:
        return False
        
    if text in _DELETED_TEXTS or title in _DELETED_TEXTS:
        return False

    return True


def fetch_subreddit_search(
    subreddit: str, query: str, after: str | None = None, token: str | None = None
) -> dict:
    """Fetch one page of search results from a subreddit (OAuth endpoint)."""
    base = REDDIT_OAUTH_BASE if token else REDDIT_BASE
    suffix = "" if token else ".json"
    url = f"{base}/r/{subreddit}/search{suffix}"
    params = {
        "q": query,
        "restrict_sr": "1",
        "sort": "new",
        "limit": "100",
    }
    if after:
        params["after"] = after

    headers = {"User-Agent": USER_AGENT}
    if token:
        headers["Authorization"] = f"bearer {token}"

    # Polite pacing to avoid 429 Too Many Requests (C17)
    time.sleep(1.5)

    resp = requests.get(url, params=params, headers=headers, timeout=20)

    if resp.status_code == 429:
        logger.warning(f"Rate limited by Reddit API on {subreddit}, sleeping 30s...")
        time.sleep(30)
        resp = requests.get(url, params=params, headers=headers, timeout=20)

    resp.raise_for_status()
    return resp.json()


def collect() -> None:
    """Run the Reddit collector."""
    setup_logging()
    logger.info("Starting Reddit collection")

    token = get_access_token()
    if not token:
        logger.error(
            "No Reddit OAuth token — unauthenticated access returns HTTP 403. "
            "Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET in .env "
            "(create a free 'script' app at https://www.reddit.com/prefs/apps). "
            "Skipping Reddit; this is recorded as a collection limitation."
        )
        return
    logger.info("Reddit OAuth token acquired")

    queries = get_all_queries()
    corpus_added = 0
    now_iso = utc_now_iso()

    for subreddit in SUBREDDITS:
        logger.info(f"--- Searching r/{subreddit} ---")
        for query in queries:
            after = None
            pages = 0
            
            while pages < 5:  # Cap at 5 pages per query per subreddit
                try:
                    data = fetch_subreddit_search(subreddit, query, after, token)
                except requests.exceptions.HTTPError as exc:
                    if exc.response.status_code == 403:
                        logger.error(f"Reddit API blocked us (403). Aborting Reddit collection to save time.")
                        return
                    logger.error(f"Failed search {query} in r/{subreddit}: {exc}")
                    break
                except Exception as exc:
                    logger.error(f"Failed search {query} in r/{subreddit}: {exc}")
                    break

                children = data.get("data", {}).get("children", [])
                if not children:
                    break
                    
                for child in children:
                    kind = child.get("kind")
                    post = child.get("data", {})
                    
                    if not _is_valid_post(post):
                        continue
                        
                    # Handle both t3 (posts) and t1 (comments)
                    if kind == "t1":
                        title = post.get("link_title", "").strip()
                        selftext = post.get("body", "").strip()
                        context_str = f"Thread Title: {title}"
                        # If it's a comment, we could theoretically fetch the parent comment
                        # but to avoid rate limits, we just note it's a comment in the context.
                        parent_id = post.get("parent_id", "")
                        if parent_id and not parent_id.startswith("t3_"):
                            context_str += f" | Parent Comment ID: {parent_id}"
                        full_text = selftext
                    else:
                        title = post.get("title", "").strip()
                        selftext = post.get("selftext", "").strip()
                        context_str = f"Thread Title: {title}"
                        full_text = f"{title}\n\n{selftext}" if selftext else title
                    
                    # Brand collision guard (C14)
                    if not is_blinkit_related(full_text):
                        continue

                    post_id = post.get("id")
                    permalink = post.get("permalink", "")
                    source_url = urljoin(REDDIT_BASE, permalink)
                    
                    # C16: canonical_url for deduplication
                    canonical_url = post.get("url", source_url)
                    
                    date_iso = normalize_utc(str(post.get("created_utc", "")))
                    era = classify_era(date_iso)

                    record = RawRecord(
                        id=make_id("reddit", post_id),
                        source="reddit",
                        source_url=source_url,
                        author_handle="",  # Anonymized (C21)
                        date=date_iso,
                        rating=None,
                        text=full_text,
                        context=context_str,
                        collected_at=now_iso,
                        collection_method="api",
                        era=era,
                        subreddit=subreddit,
                        canonical_url=canonical_url,
                    )
                    
                    append_jsonl(OUTPUT_PATH, record.model_dump(exclude_none=True))
                    corpus_added += 1

                after = data.get("data", {}).get("after")
                if not after:
                    break
                    
                pages += 1

    logger.info(f"Reddit collection complete. Added to corpus: {corpus_added}")


if __name__ == "__main__":
    collect()
