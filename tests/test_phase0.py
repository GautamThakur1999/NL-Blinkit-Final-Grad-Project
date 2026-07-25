"""
tests/test_phase0.py — Phase 0 exit-criteria verification

Run:  python -m tests.test_phase0

Tests:
  1. UTF-8 round-trip (emoji + Devanagari + smart quotes via JSONL helpers)
  2. LLM gateway unit tests (mocked — no API keys needed)
  3. Config loader basics
  4. Date normalizer edge cases
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.common import (
    read_jsonl,
    write_jsonl,
    append_jsonl,
    normalize_utc,
    read_text,
    write_text,
    setup_logging,
)

# Set up logging so we see output
setup_logging()

PASS = 0
FAIL = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    """Record a pass/fail and print the result."""
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  PASS  {name}")
    else:
        FAIL += 1
        msg = f"  FAIL  {name}"
        if detail:
            msg += f" -- {detail}"
        print(msg)


# ═══════════════════════════════════════════════════════════════════════════
# 1. UTF-8 Round-Trip Test
# ═══════════════════════════════════════════════════════════════════════════
def test_utf8_roundtrip() -> None:
    """
    Exit criteria: 'UTF-8 round-trip test passes on a sample containing
    emoji + Devanagari + smart quotes.'
    """
    print("\n--- UTF-8 Round-Trip Test ---")

    sample_records = [
        {
            "id": "utf8-emoji",
            "text": "Love this app! \U0001f525\U0001f525\U0001f525 Best delivery ever \U0001f60d",
            "source": "play_store",
        },
        {
            "id": "utf8-devanagari",
            "text": "\u092c\u094d\u0932\u093f\u0902\u0915\u093f\u091f \u092c\u0939\u0941\u0924 \u0905\u091a\u094d\u091b\u093e \u0939\u0948, \u0938\u092c\u094d\u091c\u093c\u0940 \u0924\u093e\u091c\u093c\u093e \u0906\u0924\u0940 \u0939\u0948",
            "source": "reddit",
        },
        {
            "id": "utf8-smartquotes",
            "text": "They said \u201cwe\u2019ll deliver in 10 min\u201d but it took 45\u2026 \u201cfast\u201d indeed",
            "source": "app_store",
        },
        {
            "id": "utf8-hinglish",
            "text": "Bhai pet food nahi milta yahan, sirf grocery ke liye use karta hoon \U0001f937\u200d\u2642\ufe0f",
            "source": "reddit",
        },
        {
            "id": "utf8-mixed",
            "text": "Price \u20b9200 for Maggi?! \u0915\u094d\u092f\u093e \u092e\u091c\u093c\u093e\u0915 \u0939\u0948 blinkit \U0001f644\U0001f92c",
            "source": "play_store",
        },
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "test_utf8.jsonl"

        # Write
        write_jsonl(path, sample_records)
        check("JSONL write completes", path.exists())

        # Read back
        loaded = read_jsonl(path)
        check(
            "JSONL record count matches",
            len(loaded) == len(sample_records),
            f"expected {len(sample_records)}, got {len(loaded)}",
        )

        # Verify each record round-trips exactly
        for orig, loaded_rec in zip(sample_records, loaded):
            match = orig == loaded_rec
            check(
                f"Round-trip exact match: {orig['id']}",
                match,
                f"orig={orig!r}\nloaded={loaded_rec!r}" if not match else "",
            )

        # Append test
        extra = {
            "id": "utf8-append",
            "text": "Tamil: \u0ba4\u0bb0\u0bae\u0bbe\u0ba9 \u0baa\u0bca\u0bb0\u0bc1\u0b9f\u0bcd\u0b95\u0bb3\u0bcd \U0001f44d",
            "source": "forum",
        }
        append_jsonl(path, extra)
        reloaded = read_jsonl(path)
        check(
            "Append preserves existing + adds new",
            len(reloaded) == len(sample_records) + 1,
        )
        check(
            "Appended record round-trips",
            reloaded[-1] == extra,
        )

        # Plain text round-trip
        txt_path = Path(tmpdir) / "test_utf8.txt"
        mixed_text = "Emoji \U0001f525 | Devanagari \u0939\u093f\u0902\u0926\u0940 | Smart \u201cquotes\u201d | Tamil \u0ba4\u0bae\u0bbf\u0bb4\u0bcd"
        write_text(txt_path, mixed_text)
        check(
            "Plain-text UTF-8 round-trip",
            read_text(txt_path) == mixed_text,
        )


# ═══════════════════════════════════════════════════════════════════════════
# 2. Date Normalizer Tests
# ═══════════════════════════════════════════════════════════════════════════
def test_date_normalizer() -> None:
    """Verify UTC ISO-8601 normalization for various input formats."""
    print("\n--- Date Normalizer Test ---")

    # ISO-8601 passthrough
    result = normalize_utc("2025-07-18T14:30:00+00:00")
    check("ISO-8601 with tz", "2025-07-18" in result and "14:30" in result)

    # ISO-8601 without tz (assumed UTC)
    result = normalize_utc("2025-07-18T14:30:00")
    check("ISO-8601 naive -> UTC", "2025-07-18" in result)

    # Unix timestamp
    result = normalize_utc("1721312400")
    check("Unix timestamp", "2024-07-18" in result)

    # Human format: "Jul 18, 2025"
    result = normalize_utc("Jul 18, 2025")
    check("Human date 'Jul 18, 2025'", "2025-07-18" in result)

    # d/m/y format
    result = normalize_utc("18/07/2025")
    check("Date '18/07/2025'", "2025-07-18" in result)

    # Unparseable — returns original
    result = normalize_utc("not a date")
    check("Unparseable returns original", result == "not a date")

    # Empty / None
    result = normalize_utc("")
    check("Empty string returns empty", result == "")


# ═══════════════════════════════════════════════════════════════════════════
# 3. LLM Gateway Unit Tests (no API keys needed)
# ═══════════════════════════════════════════════════════════════════════════
def test_llm_gateway_units() -> None:
    """Test gateway internals without making real API calls."""
    print("\n--- LLM Gateway Unit Tests ---")

    from pydantic import BaseModel
    from pipeline.llm import (
        LLMGateway,
        Provider,
        CallMeta,
        DATA_PREAMBLE,
        LLMError,
        SafetyBlockedError,
        RateLimitError,
        TransientError,
        SchemaValidationError,
        wrap_corpus_text,
        _classify_and_raise,
    )

    # 3a. Schema validation — valid JSON
    class SimpleTag(BaseModel):
        barrier: str
        confidence: float

    gw = LLMGateway()

    valid_json = '{"barrier": "habit_loop", "confidence": 0.85}'
    parsed = gw._parse_and_validate(valid_json, SimpleTag)
    check("Parse valid JSON", parsed.barrier == "habit_loop")
    check("Parse confidence value", parsed.confidence == 0.85)

    # 3b. Schema validation — JSON wrapped in markdown fences
    fenced_json = '```json\n{"barrier": "trust_quality", "confidence": 0.9}\n```'
    parsed2 = gw._parse_and_validate(fenced_json, SimpleTag)
    check("Parse fenced JSON", parsed2.barrier == "trust_quality")

    # 3c. Schema validation — invalid JSON
    try:
        gw._parse_and_validate("not json at all", SimpleTag)
        check("Reject invalid JSON", False, "should have raised")
    except json.JSONDecodeError:
        check("Reject invalid JSON", True)

    # 3d. Schema validation — valid JSON, wrong schema
    try:
        gw._parse_and_validate('{"wrong_field": 123}', SimpleTag)
        check("Reject schema mismatch", False, "should have raised")
    except Exception:
        check("Reject schema mismatch", True)

    # 3e. Data wrapping
    wrapped = wrap_corpus_text("Hello world")
    check("wrap_corpus_text adds delimiters", "<USER_DATA>" in wrapped)
    check("wrap_corpus_text contains text", "Hello world" in wrapped)
    check("wrap_corpus_text closes delimiter", "</USER_DATA>" in wrapped)

    # 3f. DATA_PREAMBLE exists and mentions key concepts
    check("DATA_PREAMBLE mentions RAW DATA", "RAW DATA" in DATA_PREAMBLE)
    check(
        "DATA_PREAMBLE mentions not instructions",
        "NOT instructions" in DATA_PREAMBLE or "not instructions" in DATA_PREAMBLE.lower(),
    )

    # 3g. Resume cursor round-trip
    with tempfile.TemporaryDirectory() as tmpdir:
        cursor_path = Path(tmpdir) / "test_cursor.json"

        # Empty load
        loaded = gw._load_cursor(cursor_path)
        check("Empty cursor returns empty set", len(loaded) == 0)

        # Save and reload
        ids = {"item-1", "item-2", "item-3"}
        gw._save_cursor(cursor_path, ids)
        reloaded = gw._load_cursor(cursor_path)
        check("Cursor round-trip", reloaded == ids)

        # Corrupt cursor handled gracefully
        cursor_path.write_text("not json", encoding="utf-8")
        corrupt_loaded = gw._load_cursor(cursor_path)
        check("Corrupt cursor returns empty set", len(corrupt_loaded) == 0)

    # 3h. Exception classification
    for keyword, expected_type in [
        ("429 Too Many Requests", RateLimitError),
        ("rate_limit_exceeded", RateLimitError),
        ("quota exceeded", RateLimitError),
        ("resource_exhausted", RateLimitError),
        ("500 Internal Server Error", TransientError),
        ("503 Service Unavailable", TransientError),
        ("Connection timeout", TransientError),
        ("Unknown error occurred", LLMError),
    ]:
        try:
            _classify_and_raise(Exception(keyword), "Test")
            check(f"classify '{keyword}'", False, "should have raised")
        except expected_type:
            check(f"classify '{keyword}' -> {expected_type.__name__}", True)
        except Exception as e:
            check(
                f"classify '{keyword}' -> {expected_type.__name__}",
                False,
                f"got {type(e).__name__} instead",
            )

    # 3i. CallMeta serialization
    meta = CallMeta(
        provider="groq",
        model_id="llama-3.3-70b-versatile",
        timestamp="2025-07-18T10:00:00+00:00",
        prompt_tokens=150,
        completion_tokens=50,
    )
    meta_dict = meta.to_dict()
    check("CallMeta.to_dict has provider", meta_dict["provider"] == "groq")
    check("CallMeta.to_dict has model_id", "llama" in meta_dict["model_id"])

    # 3j. Gateway stats
    gw2 = LLMGateway()
    check("Fresh gateway: 0 calls", gw2.total_calls == 0)
    check("Fresh gateway: 0 safety blocks", gw2.safety_blocked_count == 0)
    check("Fresh gateway: empty call log", len(gw2.call_log) == 0)
    summary = gw2.session_summary()
    check("Session summary is a dict", isinstance(summary, dict))


# ═══════════════════════════════════════════════════════════════════════════
# 4. Config Module Test
# ═══════════════════════════════════════════════════════════════════════════
def test_config_module() -> None:
    """Verify config module loads defaults correctly."""
    print("\n--- Config Module Test ---")

    from pipeline.config import GEMINI_MODEL, GROQ_MODEL, GEMINI_RPM, GROQ_RPM

    check("GEMINI_MODEL has a value", len(GEMINI_MODEL) > 0)
    check("GROQ_MODEL has a value", len(GROQ_MODEL) > 0)
    check("GEMINI_RPM is positive", GEMINI_RPM > 0)
    check("GROQ_RPM is positive", GROQ_RPM > 0)


# ═══════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 60)
    print("Phase 0 — Exit Criteria Verification")
    print("=" * 60)

    test_utf8_roundtrip()
    test_date_normalizer()
    test_llm_gateway_units()
    test_config_module()

    print("\n" + "=" * 60)
    print(f"Results: {PASS} passed, {FAIL} failed")
    print("=" * 60)

    if FAIL > 0:
        sys.exit(1)
    else:
        print("\nAll Phase 0 exit criteria PASSED.")
        sys.exit(0)
