"""
tests/test_llm_smoke.py — LLM gateway smoke test (needs API keys)

Run:  python -m tests.test_llm_smoke

Exit criteria: 'LLM gateway smoke-tests against both providers.'

Requires GEMINI_API_KEY and GROQ_API_KEY in .env or environment.
Makes one real call to each provider with a trivial prompt.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pydantic import BaseModel
from pipeline.common import setup_logging
from pipeline.llm import LLMGateway, Provider


class SmokeResult(BaseModel):
    """Minimal schema for the smoke test."""
    answer: str
    number: int


def main() -> None:
    setup_logging()
    gw = LLMGateway()

    system_prompt = (
        "You are a test assistant. Respond with valid JSON matching this schema: "
        '{"answer": "<your one-word answer>", "number": <any integer>}. '
        "Answer the question in the data block."
    )
    user_content = "What color is the sky on a clear day?"

    print("=" * 60)
    print("LLM Gateway Smoke Test")
    print("=" * 60)

    passed = 0
    failed = 0

    # ── Groq ──────────────────────────────────────────────────────────────
    print("\n--- Testing Groq ---")
    try:
        result, meta = gw.call(
            Provider.GROQ, system_prompt, user_content, SmokeResult
        )
        print(f"  Response: answer={result.answer!r}, number={result.number}")
        print(f"  Meta: model={meta.model_id}, tokens={meta.prompt_tokens}+{meta.completion_tokens}")
        print("  PASS: Groq call succeeded")
        passed += 1
    except Exception as exc:
        print(f"  FAIL: Groq call failed — {exc}")
        failed += 1

    # ── Gemini ────────────────────────────────────────────────────────────
    print("\n--- Testing Gemini ---")
    try:
        result, meta = gw.call(
            Provider.GEMINI, system_prompt, user_content, SmokeResult
        )
        print(f"  Response: answer={result.answer!r}, number={result.number}")
        print(f"  Meta: model={meta.model_id}, tokens={meta.prompt_tokens}+{meta.completion_tokens}")
        print("  PASS: Gemini call succeeded")
        passed += 1
    except Exception as exc:
        print(f"  FAIL: Gemini call failed — {exc}")
        failed += 1

    # ── Summary ───────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    summary = gw.session_summary()
    print(f"Session: {summary['total_calls']} calls, {summary['safety_blocked']} blocked")
    print(f"Models used: {summary['models_used']}")
    print(f"\nResults: {passed} passed, {failed} failed")
    print("=" * 60)

    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()
