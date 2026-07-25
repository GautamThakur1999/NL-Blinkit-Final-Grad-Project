"""
pipeline/collectors/queries.py — keyword-steered query families (T1.1)

Shared by all collectors.  Each family targets a specific aspect of the
cross-category-barrier research goal.

Includes **"Grofers"** variants for every family so legacy discussions
(pre-Dec 2021 rebrand) are not missed (C11-partial).

Edge cases closed: C11 (partial).
"""

from __future__ import annotations

# ── The Grofers rebrand date (UTC) ─────────────────────────────────────────
GROFERS_REBRAND_DATE = "2021-12-13"  # Grofers → Blinkit official rebrand

# ── App identifiers ────────────────────────────────────────────────────────
PLAY_STORE_APP_ID = "com.grofers.customerapp"
PLAY_STORE_URL = f"https://play.google.com/store/apps/details?id={PLAY_STORE_APP_ID}"

# App Store ID — Blinkit (formerly Grofers) on the India store
APP_STORE_ID = "960335206"
APP_STORE_URL = f"https://apps.apple.com/in/app/blinkit/id{APP_STORE_ID}"

# ── Target subreddits for Reddit collection ────────────────────────────────
SUBREDDITS = [
    "india",
    "indiasocial",
    "bangalore",
    "delhi",
    "mumbai",
    "hyderabad",
    "pune",
    "IndianFood",
]

# ── Query families ─────────────────────────────────────────────────────────
# Each family is a list of search terms/phrases. Collectors use these to
# steer keyword-based collection toward cross-category purchase barriers.
#
# Every family includes Grofers variants so pre-rebrand data is captured.

QUERY_FAMILIES: dict[str, list[str]] = {
    # Why users stick to the same categories
    "reorder_habit": [
        "blinkit same order",
        "blinkit repeat order",
        "blinkit weekly order",
        "blinkit reorder",
        "blinkit routine",
        "blinkit regular order",
        "blinkit always buy",
        "blinkit every week",
        "grofers same order",
        "grofers repeat order",
        "grofers weekly order",
        "grofers reorder",
        "grofers routine",
    ],
    # Why users avoid certain categories
    "category_avoidance": [
        "blinkit only for grocery",
        "blinkit only use for",
        "blinkit never buy",
        "blinkit won't order",
        "blinkit don't buy",
        "blinkit just for",
        "blinkit only groceries",
        "blinkit not for",
        "grofers only for grocery",
        "grofers only use for",
        "grofers never buy",
        "grofers won't order",
    ],
    # Where users go instead of Blinkit for non-grocery
    "channel_preference": [
        "blinkit vs amazon",
        "blinkit vs nykaa",
        "blinkit pharmacy",
        "blinkit chemist",
        "blinkit local store",
        "blinkit vs swiggy instamart",
        "blinkit vs zepto",
        "blinkit vs bigbasket",
        "blinkit pet store",
        "blinkit electronics",
        "grofers vs amazon",
        "grofers vs bigbasket",
    ],
    # Trust / quality concerns blocking new category trial
    "trust_quality": [
        "blinkit quality",
        "blinkit expiry",
        "blinkit expired",
        "blinkit fake",
        "blinkit authentic",
        "blinkit fresh",
        "blinkit trust",
        "blinkit damaged",
        "blinkit wrong product",
        "blinkit product quality",
        "grofers quality",
        "grofers expiry",
        "grofers expired",
        "grofers fake",
    ],
    # Users discovering new categories (positive signal)
    "discovery": [
        "blinkit didn't know",
        "blinkit found out",
        "blinkit discovered",
        "blinkit surprised",
        "blinkit new category",
        "blinkit also sells",
        "blinkit started buying",
        "blinkit first time",
        "blinkit try new",
        "grofers didn't know",
        "grofers found out",
        "grofers also sells",
    ],
    # General brand mentions (catch-all for volume)
    "brand_general": [
        "blinkit review",
        "blinkit experience",
        "blinkit app",
        "blinkit delivery",
        "blinkit shopping",
        "blinkit opinion",
        "grofers review",
        "grofers experience",
        "grofers app",
        "quick commerce india",
        "quick commerce blinkit",
        "10 minute delivery blinkit",
    ],
}


def get_all_queries() -> list[str]:
    """Return a flat list of all unique query strings across all families."""
    seen: set[str] = set()
    result: list[str] = []
    for terms in QUERY_FAMILIES.values():
        for term in terms:
            if term not in seen:
                seen.add(term)
                result.append(term)
    return result


def get_family_queries(family: str) -> list[str]:
    """Return query strings for a specific family."""
    return QUERY_FAMILIES.get(family, [])


def classify_era(date_iso: str) -> str:
    """
    Return 'grofers' or 'blinkit' based on whether the date is before
    or after the Dec 2021 rebrand (C11).
    """
    if not date_iso:
        return "blinkit"
    # Simple string comparison works for ISO-8601 dates
    return "grofers" if date_iso < GROFERS_REBRAND_DATE else "blinkit"
