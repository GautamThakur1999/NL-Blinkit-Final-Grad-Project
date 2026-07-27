"""
pipeline/validation/dashboard_data.py — build the Insights Dashboard payload

Produces a single self-contained JSON artifact (`data/analysis/dashboard.json`)
that the deployed dashboard reads. Because the dashboard consumes a pre-built
file, it deploys as a *static* site: no server, no API keys, no quota, nothing
to fall over while it is being graded.

Design rule: the payload carries the study's limitations alongside its findings —
sample size vs population, weak-signal flags, null findings, and the barriers
with zero evidence. A dashboard that hides how thin its evidence is would
misrepresent the research.

Usage:
    python -m pipeline.validation.dashboard_data
"""

from __future__ import annotations

import collections
import json
import logging
from typing import Any

from pipeline.common import ANALYSIS_DIR, DATA_DIR, iter_jsonl, setup_logging, utc_now_iso

logger = logging.getLogger(__name__)

CORPUS_PATH = DATA_DIR / "clean" / "corpus.jsonl"
TAGS_PATH = ANALYSIS_DIR / "tags_results.jsonl"
THEMES_PATH = ANALYSIS_DIR / "themes.json"
INSIGHTS_PATH = ANALYSIS_DIR / "insights.json"
AUDIT_PATH = ANALYSIS_DIR / "traceability_audit.json"
SAMPLING_PATH = ANALYSIS_DIR / "sampling_report.json"
COLLECTION_PATH = ANALYSIS_DIR / "collection_report.json"
OUTPUT_PATH = ANALYSIS_DIR / "dashboard.json"

# Barriers derived from the five pre-registered hypotheses. Listing them
# explicitly means a barrier with zero evidence still appears in the dashboard
# as a zero — an absence you can see, rather than a row that quietly vanishes.
HYPOTHESIS_BARRIERS = {
    "habit_loop": "H1",
    "low_awareness": "H2",
    "trust_quality": "H3",
    "discovery_friction": "H4",
    "missing_information": "H5",
}


def _load_json(path, default: Any = None) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def build() -> dict[str, Any]:
    corpus = {rec["id"]: rec for rec in iter_jsonl(CORPUS_PATH)}
    tags = list(iter_jsonl(TAGS_PATH))
    themes = (_load_json(THEMES_PATH, {}) or {}).get("themes", [])
    insights = (_load_json(INSIGHTS_PATH, {}) or {}).get("insights", [])
    audit = _load_json(AUDIT_PATH, {}) or {}
    sampling = _load_json(SAMPLING_PATH, {}) or {}
    collection = _load_json(COLLECTION_PATH, {}) or {}

    # ── Barrier counts ────────────────────────────────────────────────────
    barrier_counts: collections.Counter[str] = collections.Counter()
    sentiment_counts: collections.Counter[str] = collections.Counter()
    channels: collections.Counter[str] = collections.Counter()
    categories: collections.Counter[str] = collections.Counter()
    quotes_with_text = 0

    for row in tags:
        res = row.get("result", {})
        for b in res.get("barriers", []):
            barrier_counts[b] += 1
        sentiment_counts[res.get("sentiment", "unknown")] += 1
        for c in res.get("channel_alternatives", []):
            channels[c.strip().lower()] += 1
        for c in res.get("categories_mentioned", []):
            categories[c.strip().lower()] += 1
        if (res.get("key_quote") or "none").lower() != "none":
            quotes_with_text += 1

    tagged_total = len(tags) or 1
    barriers = [
        {
            "id": name,
            "hypothesis": HYPOTHESIS_BARRIERS.get(name),
            "count": count,
            "share": round(count / tagged_total, 4),
        }
        for name, count in barrier_counts.most_common()
        if name != "none"
    ]

    # Hypothesis barriers that produced no evidence at all — reported as
    # explicit zeros so their absence is visible in the UI.
    zero_evidence = [
        {"id": name, "hypothesis": hyp, "count": 0, "share": 0.0}
        for name, hyp in HYPOTHESIS_BARRIERS.items()
        if barrier_counts.get(name, 0) == 0
    ]

    # ── Source mix of the tagged corpus ───────────────────────────────────
    source_counts: collections.Counter[str] = collections.Counter()
    for row in tags:
        rec = corpus.get(row["item_id"])
        if rec:
            source_counts[rec.get("source", "unknown")] += 1

    # ── Themes ────────────────────────────────────────────────────────────
    def theme_payload(t: dict) -> dict:
        evidence = t.get("evidence", [])
        return {
            "theme_name": t.get("theme_name"),
            "description": t.get("description"),
            "barrier": t.get("barrier"),
            "evidence_count": len(evidence),
            "source_types": sorted({e.get("source", "unknown") for e in evidence}),
            "is_weak_signal": t.get("is_weak_signal", False),
            "weak_signal_reason": t.get("weak_signal_reason"),
            # Exemplar quotes only — the full evidence set stays in
            # data/analysis/ as the auditable layer (edge case V4).
            "exemplar_quotes": [
                {
                    "text": e.get("quote", ""),
                    "source": e.get("source", ""),
                    "source_url": e.get("url", ""),
                }
                for e in evidence[:3]
            ],
        }

    strong = [theme_payload(t) for t in themes if not t.get("is_weak_signal")]
    weak = [theme_payload(t) for t in themes if t.get("is_weak_signal")]

    # ── Hypothesis scorecard ──────────────────────────────────────────────
    scorecard: dict[str, dict[str, Any]] = {}
    for ins in insights:
        for sc in ins.get("scorecards", []):
            hid = sc.get("hypothesis_id", "unknown")
            entry = scorecard.setdefault(
                hid, {"hypothesis_id": hid, "strengths": [], "findings": []}
            )
            entry["strengths"].append(sc.get("evidence_strength"))
            summary = sc.get("finding_summary")
            if summary and summary not in entry["findings"]:
                entry["findings"].append(summary)

    strength_rank = {"strong": 3, "moderate": 2, "weak": 1, "contradicted": 0}
    for entry in scorecard.values():
        strengths = [s for s in entry["strengths"] if s]
        entry["evidence_strength"] = (
            max(strengths, key=lambda s: strength_rank.get(s, 0)) if strengths else "weak"
        )
        entry.pop("strengths", None)

    # Hypotheses never scored at all — no evidence surfaced for them
    for name, hyp in HYPOTHESIS_BARRIERS.items():
        key = f"{hyp}_{name}"
        if key not in scorecard:
            scorecard[key] = {
                "hypothesis_id": key,
                "evidence_strength": "no_evidence",
                "findings": ["No supporting evidence found in the analysed corpus."],
            }

    payload = {
        "meta": {
            "generated_at": utc_now_iso(),
            "corpus_size": len(corpus),
            "tagged_items": len(tags),
            "sources": sorted(source_counts.keys()),
            "source_counts": dict(source_counts),
            "collection_total_records": collection.get("total_records"),
            "collection_date_range": collection.get("date_range"),
            "sampling": {
                "population_size": sampling.get("population_size"),
                "sample_size": sampling.get("sample_size"),
                "method": sampling.get("sampling_method"),
                "seed": sampling.get("random_seed"),
                "reason": sampling.get("reason"),
            },
        },
        "kpis": {
            "reviews_collected": collection.get("total_records", 0),
            "corpus_analysed": len(corpus),
            "items_tagged": len(tags),
            "quotes_verbatim_verified": quotes_with_text,
            "themes_total": len(themes),
            "themes_strong": len(strong),
            "sentiment": dict(sentiment_counts),
        },
        "barriers": barriers,
        "barriers_zero_evidence": zero_evidence,
        "themes_strong": strong,
        "themes_weak": weak,
        "hypothesis_scorecard": sorted(
            scorecard.values(), key=lambda e: e["hypothesis_id"]
        ),
        "research_questions": [
            {
                "id": ins.get("research_question_id"),
                "title": ins.get("insight_title"),
                "answer": ins.get("synthesis_narrative"),
                "supporting_themes": sorted(
                    {
                        tn
                        for sc in ins.get("scorecards", [])
                        for tn in sc.get("supporting_theme_names", [])
                    }
                ),
            }
            for ins in insights
        ],
        "validation": {
            "traceability_passed": audit.get("passed", False),
            "orphan_insights": audit.get("orphan_insights", []),
            "null_finding_insights": audit.get("null_finding_insights", []),
            "quotes_checked": audit.get("total_quotes_checked", 0),
            "quotes_without_url": audit.get("quotes_without_url_count", 0),
        },
        "channel_alternatives": dict(channels.most_common(10)),
        "categories_mentioned": dict(categories.most_common(10)),
    }
    return payload


def process() -> None:
    setup_logging()
    logger.info("Building dashboard payload...")
    payload = build()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    logger.info(
        "dashboard.json written: %d barriers, %d strong themes, %d questions",
        len(payload["barriers"]),
        len(payload["themes_strong"]),
        len(payload["research_questions"]),
    )


if __name__ == "__main__":
    process()
