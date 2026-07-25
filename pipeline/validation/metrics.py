"""
pipeline/validation/metrics.py — Validation Metrics Roll-up (T4.3)

Aggregates key validation metrics into a single JSON report:
  • Spot-check agreement rate
  • Cross-model disagreement rate (counter-evidence hits)
  • Safety-blocked count (from LLM gateway session summaries)
  • Single-source-flag count (weak-signal themes)
  • Traceability audit pass/fail

Edge cases closed: A4, A12.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from pipeline.common import (
    ANALYSIS_DIR,
    DATA_DIR,
    iter_jsonl,
    setup_logging,
)

logger = logging.getLogger(__name__)

THEMES_PATH = ANALYSIS_DIR / "themes.json"
COUNTER_EV_PATH = DATA_DIR / "state" / "counter_evidence_results.jsonl"
AUDIT_REPORT_PATH = ANALYSIS_DIR / "traceability_audit.json"
SPOTCHECK_PATH = ANALYSIS_DIR / "spotcheck_sample.json"
METRICS_PATH = ANALYSIS_DIR / "validation_metrics.json"


def process() -> dict:
    setup_logging()
    logger.info("Starting T4.3 Validation Metrics Roll-up...")

    metrics: dict = {}

    # ── 1. Traceability audit result ───────────────────────────────────────
    if AUDIT_REPORT_PATH.exists():
        with AUDIT_REPORT_PATH.open("r", encoding="utf-8") as f:
            audit = json.load(f)
        metrics["traceability_audit"] = {
            "passed": audit.get("passed", False),
            "orphan_insights": len(audit.get("orphan_insights", [])),
            "themes_missing_evidence": len(audit.get("themes_missing_evidence", [])),
            "quotes_without_url_count": audit.get("quotes_without_url_count", 0),
        }
    else:
        metrics["traceability_audit"] = {"status": "not yet run"}

    # ── 2. Spot-check agreement ────────────────────────────────────────────
    if SPOTCHECK_PATH.exists():
        with SPOTCHECK_PATH.open("r", encoding="utf-8") as f:
            sc_data = json.load(f)
        items = sc_data.get("items", [])
        reviewed = [
            it for it in items
            if it.get("human_agrees_barriers") is not None
        ]
        if reviewed:
            total = len(reviewed)
            agree = sum(1 for it in reviewed if it["human_agrees_barriers"])
            rate = agree / total
            metrics["spotcheck"] = {
                "sample_size": len(items),
                "reviewed_count": total,
                "barrier_agreement_rate": f"{rate:.1%}",
                "passed": rate >= 0.80,
            }
        else:
            metrics["spotcheck"] = {
                "sample_size": len(items),
                "reviewed_count": 0,
                "status": "awaiting human review",
            }
    else:
        metrics["spotcheck"] = {"status": "not yet generated"}

    # ── 3. Counter-evidence (cross-model disagreement) ─────────────────────
    contradiction_count = 0
    total_ce_items = 0
    if COUNTER_EV_PATH.exists():
        for row in iter_jsonl(COUNTER_EV_PATH):
            total_ce_items += 1
            result = row.get("result", {})
            contradictions = result.get("contradictions", [])
            contradiction_count += len(contradictions)

    metrics["counter_evidence"] = {
        "total_items_scanned": total_ce_items,
        "total_contradictions_found": contradiction_count,
        "cross_model_disagreement_rate": (
            f"{contradiction_count / total_ce_items:.1%}"
            if total_ce_items > 0 else "N/A"
        ),
    }

    # ── 4. Weak-signal (single-source) themes ──────────────────────────────
    weak_signal_count = 0
    total_themes = 0
    if THEMES_PATH.exists():
        with THEMES_PATH.open("r", encoding="utf-8") as f:
            themes_data = json.load(f)
        themes = themes_data.get("themes", [])
        total_themes = len(themes)
        weak_signal_count = sum(1 for t in themes if t.get("is_weak_signal"))

    metrics["themes"] = {
        "total_themes": total_themes,
        "weak_signal_count": weak_signal_count,
        "single_source_flag_count": weak_signal_count,
    }

    # ── 5. Safety-blocked count ────────────────────────────────────────────
    # This is logged per-session by the LLM gateway. We check the dead-letter
    # files as a proxy for items that failed all retries.
    dead_letter_files = list((DATA_DIR / "state").glob("*_dead_letters.jsonl"))
    total_dead = 0
    for dlf in dead_letter_files:
        for _ in iter_jsonl(dlf):
            total_dead += 1

    metrics["llm_failures"] = {
        "total_dead_lettered_items": total_dead,
        "dead_letter_files": [str(f.name) for f in dead_letter_files],
    }

    # ── Save ───────────────────────────────────────────────────────────────
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    with METRICS_PATH.open("w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

    logger.info(f"Validation metrics saved to {METRICS_PATH}")
    logger.info(json.dumps(metrics, indent=2))
    return metrics


if __name__ == "__main__":
    process()
