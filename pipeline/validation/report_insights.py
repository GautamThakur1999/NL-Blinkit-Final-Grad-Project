"""
pipeline/validation/report_insights.py — INSIGHTS_REPORT.md Generator (T4.4)

Generates `outputs/INSIGHTS_REPORT.md` containing:
  • Answers to all 8 research questions
  • Top exemplar quotes per theme (full evidence stays in data/analysis/)
  • Hypothesis scorecard (H1–H5: strong/moderate/weak/contradicted + emergent)
  • Weak-signals section
  • Explicit emergent-findings check
  • Counter-evidence summary

Edge cases closed: V3, V4, X4.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from pipeline.common import (
    ANALYSIS_DIR,
    DATA_DIR,
    OUTPUTS_DIR,
    iter_jsonl,
    setup_logging,
    write_text,
)

logger = logging.getLogger(__name__)

INSIGHTS_PATH = ANALYSIS_DIR / "insights.json"
THEMES_PATH = ANALYSIS_DIR / "themes.json"
COUNTER_EV_PATH = DATA_DIR / "state" / "counter_evidence_results.jsonl"
METRICS_PATH = ANALYSIS_DIR / "validation_metrics.json"
REPORT_PATH = OUTPUTS_DIR / "INSIGHTS_REPORT.md"

RESEARCH_QUESTIONS = {
    "Q1": "Why do users repeatedly buy from the same categories?",
    "Q2": "What prevents users from exploring new categories?",
    "Q3": "How do users discover products today?",
    "Q4": "What role do habits play in shopping behavior?",
    "Q5": "What information do users need before trying a new category?",
    "Q6": "What frustrations emerge repeatedly?",
    "Q7": "Which user segments are more likely to experiment?",
    "Q8": "What unmet needs emerge consistently across discussions?",
}


def _load_json(path: Path) -> dict | list:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _format_scorecard_table(scorecards: list[dict]) -> str:
    """Render a scorecard list as a Markdown table."""
    lines = [
        "| Hypothesis | Evidence Strength | Finding | Supporting Themes |",
        "|---|---|---|---|",
    ]
    for sc in scorecards:
        hyp = sc.get("hypothesis_id", "")
        strength = sc.get("evidence_strength", "")
        finding = sc.get("finding_summary", "").replace("\n", " ")
        themes = ", ".join(sc.get("supporting_theme_names", []))
        lines.append(f"| {hyp} | **{strength}** | {finding} | {themes} |")
    return "\n".join(lines)


def process() -> None:
    setup_logging()
    logger.info("Starting T4.4 INSIGHTS_REPORT.md generation...")

    insights_data = _load_json(INSIGHTS_PATH)
    themes_data = _load_json(THEMES_PATH)
    metrics_data = _load_json(METRICS_PATH)

    insights = insights_data.get("insights", [])
    themes = themes_data.get("themes", [])

    if not insights:
        logger.error("No insights found. Cannot generate report.")
        return

    # ── Build the report ───────────────────────────────────────────────────
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    sections = []

    # Header
    sections.append(f"""# Insights Report — Blinkit Category Exploration

> **AI-Powered Discovery Engine: Part 1 Deliverable**
> Generated: {now}
> Taxonomy version: v1.0

---

## Executive Summary

This report presents findings from the AI-powered analysis of {_count_corpus()} user
reviews and discussions across Play Store, App Store, Reddit, and curated social sources.
The analysis identified **{len([t for t in themes if not t.get('is_weak_signal')])}
robust themes** and **{len([t for t in themes if t.get('is_weak_signal')])} weak signals**
across {len(insights)} research questions, evaluating five pre-registered hypotheses
(H1–H5) about cross-category purchase barriers.

---
""")

    # Research Question sections
    sections.append("## Research Question Findings\n")
    for insight in insights:
        qid = insight.get("research_question_id", "")
        q_text = RESEARCH_QUESTIONS.get(qid, qid)
        title = insight.get("insight_title", "")
        narrative = insight.get("synthesis_narrative", "")
        scorecards = insight.get("scorecards", [])

        sections.append(f"### {qid}: {q_text}\n")
        sections.append(f"**{title}**\n")
        sections.append(f"{narrative}\n")

        if scorecards:
            sections.append("#### Hypothesis Scorecard\n")
            sections.append(_format_scorecard_table(scorecards))
            sections.append("")

        sections.append("---\n")

    # Hypothesis Scorecard Summary
    sections.append("## Hypothesis Scorecard Summary\n")
    scorecard_agg = _aggregate_scorecards(insights)
    sections.append(
        "| Hypothesis | Strongest Evidence | Overall Assessment |\n"
        "|---|---|---|"
    )
    for hyp_id, data in scorecard_agg.items():
        sections.append(
            f"| {hyp_id} | {data['strongest']} | {data['assessment']} |"
        )
    sections.append("\n---\n")

    # Theme Evidence Summary (top quotes only)
    sections.append("## Theme Evidence Summary\n")
    sections.append(
        "> Full evidence lists are available in `data/analysis/themes.json`.\n"
        "> Only top exemplar quotes are shown here for readability.\n"
    )

    robust_themes = [t for t in themes if not t.get("is_weak_signal")]
    for theme in robust_themes:
        name = theme.get("theme_name", "")
        desc = theme.get("description", "")
        barrier = theme.get("barrier", "")
        evidence = theme.get("evidence", [])

        sections.append(f"### {name}\n")
        sections.append(f"**Barrier:** `{barrier}` | **Evidence count:** {len(evidence)}\n")
        sections.append(f"{desc}\n")

        # Show up to 3 exemplar quotes
        for ev in evidence[:3]:
            quote = ev.get("quote", "")
            source = ev.get("source", "")
            url = ev.get("url", "")
            url_text = f" ([source]({url}))" if url else ""
            sections.append(f"> *\"{quote}\"* — {source}{url_text}\n")
        sections.append("")

    # Weak Signals
    weak_themes = [t for t in themes if t.get("is_weak_signal")]
    if weak_themes:
        sections.append("## Weak Signals\n")
        sections.append(
            "> These themes did not meet the full admission criteria "
            "(≥3 items from ≥2 sources). They are reported with explicit "
            "low-confidence labels and should be treated as hypotheses "
            "for further investigation.\n"
        )
        for theme in weak_themes:
            name = theme.get("theme_name", "")
            reason = theme.get("weak_signal_reason", "")
            evidence = theme.get("evidence", [])
            sections.append(f"- **{name}** ({len(evidence)} items): {reason}")
        sections.append("\n---\n")

    # Emergent Findings Check
    sections.append("## Emergent Findings Check\n")
    emergent = _find_emergent(insights, themes)
    if emergent:
        sections.append(
            "The following findings emerged from the data beyond the "
            "pre-registered H1–H5 hypotheses:\n"
        )
        for e in emergent:
            sections.append(f"- {e}")
    else:
        sections.append(
            "**No emergent findings surfaced beyond the pre-registered hypotheses.**\n"
            "This warrants scrutiny: the taxonomy may be overfitting to "
            "pre-existing beliefs. The `other_emergent` barrier category "
            "captured no themes that met the admission threshold. "
            "User interviews (Part 2) should probe for undiscovered barriers.\n"
        )
    sections.append("\n---\n")

    # Counter-Evidence
    sections.append("## Counter-Evidence Summary\n")
    ce_summary = _summarize_counter_evidence()
    sections.append(ce_summary)
    sections.append("\n---\n")

    # Validation Summary
    sections.append("## Validation Summary\n")
    if metrics_data:
        audit = metrics_data.get("traceability_audit", {})
        sc = metrics_data.get("spotcheck", {})
        ce = metrics_data.get("counter_evidence", {})

        sections.append(f"- **Traceability audit:** {'PASSED ✅' if audit.get('passed') else 'FAILED ❌'}")
        sections.append(f"- **Orphan insights:** {audit.get('orphan_insights', 'N/A')}")
        sections.append(f"- **Spot-check sample size:** {sc.get('sample_size', 'N/A')}")
        sections.append(f"- **Spot-check status:** {sc.get('status', sc.get('barrier_agreement_rate', 'N/A'))}")
        sections.append(f"- **Counter-evidence contradictions:** {ce.get('total_contradictions_found', 'N/A')}")
        sections.append(f"- **Cross-model disagreement rate:** {ce.get('cross_model_disagreement_rate', 'N/A')}")
    else:
        sections.append("*Validation metrics not yet generated.*")
    sections.append("")

    # Write report
    report_text = "\n".join(sections)
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    write_text(REPORT_PATH, report_text)

    logger.info(f"INSIGHTS_REPORT.md generated at {REPORT_PATH}")


def _count_corpus() -> int:
    corpus_path = DATA_DIR / "clean" / "corpus.jsonl"
    if not corpus_path.exists():
        return 0
    count = 0
    for _ in iter_jsonl(corpus_path):
        count += 1
    return count


def _aggregate_scorecards(insights: list[dict]) -> dict:
    """Aggregate hypothesis scores across all insights."""
    hyp_scores: dict[str, list[str]] = {}
    for insight in insights:
        for sc in insight.get("scorecards", []):
            hyp_id = sc.get("hypothesis_id", "")
            strength = sc.get("evidence_strength", "")
            hyp_scores.setdefault(hyp_id, []).append(strength)

    STRENGTH_ORDER = {"strong": 4, "moderate": 3, "weak": 2, "contradicted": 1}
    result = {}
    for hyp_id, strengths in sorted(hyp_scores.items()):
        strongest = max(strengths, key=lambda s: STRENGTH_ORDER.get(s, 0))
        # Overall assessment
        strong_count = strengths.count("strong")
        contra_count = strengths.count("contradicted")
        if strong_count >= 2:
            assessment = "Well-supported across multiple questions"
        elif contra_count > 0 and strong_count > 0:
            assessment = "Mixed evidence — supported and contradicted"
        elif contra_count > strong_count:
            assessment = "Predominantly contradicted"
        else:
            assessment = "Moderate support"
        result[hyp_id] = {"strongest": strongest, "assessment": assessment}

    return result


def _find_emergent(insights: list[dict], themes: list[dict]) -> list[str]:
    """Check for emergent findings beyond H1–H5."""
    emergent = []
    for insight in insights:
        for sc in insight.get("scorecards", []):
            if sc.get("hypothesis_id") == "emergent":
                emergent.append(sc.get("finding_summary", ""))
    for theme in themes:
        if theme.get("barrier") == "other_emergent" and not theme.get("is_weak_signal"):
            emergent.append(
                f"Theme '{theme['theme_name']}': {theme.get('description', '')}"
            )
    return emergent


def _summarize_counter_evidence() -> str:
    """Summarize counter-evidence findings from the batch results."""
    if not COUNTER_EV_PATH.exists():
        return "*Counter-evidence pass has not been run yet.*"

    contradictions = []
    for row in iter_jsonl(COUNTER_EV_PATH):
        result = row.get("result", {})
        for c in result.get("contradictions", []):
            contradictions.append(c)

    if not contradictions:
        return (
            "The cross-model counter-evidence pass (Groq scanning Gemini-derived "
            "insights) found **zero explicit contradictions** in the corpus. "
            "This does not mean the insights are unassailable — it means the "
            "corpus does not contain strong opposing evidence. "
            "User interviews (Part 2) should probe for unrepresented viewpoints."
        )

    lines = [
        f"The counter-evidence pass found **{len(contradictions)} contradiction(s)**:\n"
    ]
    for c in contradictions[:10]:
        lines.append(
            f"- **{c.get('insight_title', '')}**: "
            f"*\"{c.get('contradicting_quote', '')}\"* — {c.get('explanation', '')}"
        )
    if len(contradictions) > 10:
        lines.append(f"\n*...and {len(contradictions) - 10} more (see full data in `data/state/counter_evidence_results.jsonl`).*")

    return "\n".join(lines)


if __name__ == "__main__":
    process()
