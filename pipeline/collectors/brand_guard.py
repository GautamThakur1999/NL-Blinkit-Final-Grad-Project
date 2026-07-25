"""
pipeline/collectors/brand_guard.py — brand-collision filter (T1.6)

Context-window keyword check: "blinkit" / "grofers" must co-occur with
shopping/delivery context.  Filters out Blink cameras, "blink it" as a
phrase, and other false positives.

Edge cases closed: C14.
"""

from __future__ import annotations

import re

# ── Shopping-context keywords ──────────────────────────────────────────────
# If a text mentions "blinkit" or "grofers", it should also contain at least
# one of these to be considered relevant to our research topic.
_SHOPPING_CONTEXT: set[str] = {
    # Delivery / ordering
    "deliver", "delivery", "order", "ordered", "ordering", "cart", "checkout",
    "payment", "pay", "paid", "refund", "cancel", "cancelled",
    # App / platform
    "app", "install", "update", "notification", "coupon", "offer", "promo",
    "discount", "cashback",
    # Products / categories
    "grocery", "groceries", "vegetable", "vegetables", "fruit", "fruits",
    "milk", "bread", "egg", "eggs", "rice", "atta", "dal", "oil",
    "snack", "snacks", "beverage", "drink", "water",
    "shampoo", "soap", "toothpaste", "cream", "lotion",
    "diaper", "baby", "pet", "dog", "cat", "medicine", "pharmacy",
    "stationery", "electronics", "charger", "cable",
    "product", "item", "category", "catalogue",
    # Quick-commerce ecosystem
    "quick commerce", "dark store", "10 minute", "10 min", "15 min",
    "instamart", "zepto", "bigbasket", "swiggy", "zomato", "dunzo",
    "amazon fresh",
    # Shopping behavior
    "buy", "bought", "buying", "purchase", "shop", "shopping",
    "reorder", "repeat", "basket", "stock", "store",
    # Quality / trust
    "expiry", "expired", "fresh", "quality", "authentic", "fake",
    "damaged", "wrong", "missing",
    # Pricing
    "price", "expensive", "cheap", "costly", "rupee", "rs", "inr",
}

# ── False-positive patterns ────────────────────────────────────────────────
# These suggest the text is NOT about Blinkit the shopping app.
_FALSE_POSITIVE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bblink\s+camera", re.IGNORECASE),
    re.compile(r"\bblink\s+security", re.IGNORECASE),
    re.compile(r"\bblink\s+doorbell", re.IGNORECASE),
    re.compile(r"\bblink\s+mini", re.IGNORECASE),
    re.compile(r"\bamazon\s+blink\b", re.IGNORECASE),
    re.compile(r"\bblink\s+outdoor", re.IGNORECASE),
    re.compile(r"\bblink\s+xt\b", re.IGNORECASE),
]

# Brand terms to look for
_BRAND_TERMS = re.compile(r"\b(blinkit|grofers)\b", re.IGNORECASE)


def is_blinkit_related(text: str) -> bool:
    """
    Check whether *text* is about Blinkit/Grofers the shopping platform.

    Returns True if the text mentions blinkit/grofers AND has shopping
    context.  Returns False for Blink cameras, generic "blink it", etc.

    Used at collection time (C14) and again in Stage 2 relevance filtering.
    """
    if not text:
        return False

    text_lower = text.lower()

    # Step 1: Must mention the brand
    if not _BRAND_TERMS.search(text_lower):
        return False

    # Step 2: Check for known false-positive patterns
    for pattern in _FALSE_POSITIVE_PATTERNS:
        if pattern.search(text):
            return False

    # Step 3: Check for shopping context
    # For short texts (e.g. tweet-length), brand mention alone is enough
    if len(text_lower) < 100:
        return True

    # For longer texts, require at least one shopping-context keyword
    for keyword in _SHOPPING_CONTEXT:
        if keyword in text_lower:
            return True

    # No shopping context found in a long text — probably not relevant
    return False


def has_brand_mention(text: str) -> bool:
    """Quick check: does the text mention blinkit or grofers at all?"""
    if not text:
        return False
    return bool(_BRAND_TERMS.search(text.lower()))
