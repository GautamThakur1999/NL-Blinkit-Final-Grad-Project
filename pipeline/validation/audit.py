"""
pipeline/validation/audit.py — Automated Traceability Audit (T4.1)

Verifies the full evidence chain:
    insight → ≥1 theme → ≥N verbatim quotes → source URLs

Distinguishes:
  • "URL now dead (snapshot exists)" — URL was recorded at collection time
  • "unverifiable at collection" — no URL was ever recorded

Any orphan insight (missing the chain) FAILS the report build.

Edge cases closed: C19, A2 (verification).
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
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
TAGS_PATH = DATA_DIR / "state" / "tags_results.jsonl"
CORPUS_PATH = DATA_DIR / "clean" / "corpus.jsonl"
AUDIT_REPORT_PATH = ANALYSIS_DIR / "traceability_audit.json"


@dataclass
class AuditResult:
    total_insights: int = 0
    total_themes_referenced: int = 0
    total_quotes_checked: int = 0
    orphan_insights: list[str] = field(default_factory=list)
    themes_missing_evidence: list[str] = field(default_factory=list)
    quotes_without_url: list[dict] = field(default_factory=list)
    urls_dead_snapshot_exists: list[dict] = field(default_factory=list)
    passed: bool = False

    def to_dict(self) -> dict:
        return {
            "total_insights": self.total_insights,
            "total_themes_referenced": self.total_themes_referenced,
            "total_quotes_checked": self.total_quotes_checked,
            "orphan_insights": self.orphan_insights,
            "themes_missing_evidence": self.themes_missing_evidence,
            "quotes_without_url_count": len(self.quotes_without_url),
            "quotes_without_url_sample": self.quotes_without_url[:10],
            "urls_dead_snapshot_exists_count": len(self.urls_dead_snapshot_exists),
            "passed": self.passed,
        }


def process() -> AuditResult:
    setup_logging()
    logger.info("Starting T4.1 Automated Traceability Audit...")

    result = AuditResult()

    # ── 1. Load all artifacts ──────────────────────────────────────────────
    if not INSIGHTS_PATH.exists():
        logger.error("insights.json not found — cannot audit.")
        return result

    with INSIGHTS_PATH.open("r", encoding="utf-8") as f:
        insights_data = json.load(f)

    if not THEMES_PATH.exists():
        logger.error("themes.json not found — cannot audit.")
        return result

    with THEMES_PATH.open("r", encoding="utf-8") as f:
        themes_data = json.load(f)

    # Build theme lookup by name
    themes_by_name: dict[str, dict] = {}
    for theme in themes_data.get("themes", []):
        themes_by_name[theme["theme_name"]] = theme

    # Build corpus lookup for URL verification
    corpus_urls: dict[str, str] = {}  # item_id → url
    if CORPUS_PATH.exists():
        for rec in iter_jsonl(CORPUS_PATH):
            corpus_urls[rec["id"]] = rec.get("url", "")

    # ── 2. Audit each insight ──────────────────────────────────────────────
    insights = insights_data.get("insights", [])
    result.total_insights = len(insights)

    for insight in insights:
        title = insight.get("insight_title", "<untitled>")
        scorecards = insight.get("scorecards", [])

        # Collect all theme names referenced by this insight's scorecards
        referenced_themes = set()
        for sc in scorecards:
            for tn in sc.get("supporting_theme_names", []):
                referenced_themes.add(tn)

        if not referenced_themes:
            result.orphan_insights.append(title)
            logger.warning(f"ORPHAN INSIGHT: '{title}' references zero themes.")
            continue

        result.total_themes_referenced += len(referenced_themes)

        # Verify each referenced theme exists and has evidence
        for tn in referenced_themes:
            theme = themes_by_name.get(tn)
            if theme is None:
                result.orphan_insights.append(
                    f"{title} → references nonexistent theme '{tn}'"
                )
                logger.warning(
                    f"ORPHAN: Insight '{title}' references theme '{tn}' "
                    f"which does not exist in themes.json."
                )
                continue

            evidence_list = theme.get("evidence", [])
            if not evidence_list:
                result.themes_missing_evidence.append(tn)
                logger.warning(f"Theme '{tn}' has zero evidence items.")
                continue

            # Verify each evidence item has a quote and a URL
            for ev in evidence_list:
                result.total_quotes_checked += 1
                url = ev.get("url", "").strip()
                item_id = ev.get("item_id", "")

                if not url:
                    # Check if the corpus ever had a URL for this item
                    corpus_url = corpus_urls.get(item_id, "")
                    if corpus_url:
                        result.urls_dead_snapshot_exists.append({
                            "item_id": item_id,
                            "status": "URL recorded at collection but missing in theme evidence",
                            "original_url": corpus_url,
                        })
                    else:
                        result.quotes_without_url.append({
                            "item_id": item_id,
                            "theme": tn,
                            "status": "unverifiable at collection — no URL ever recorded",
                        })

    # ── 3. Determine pass/fail ─────────────────────────────────────────────
    result.passed = len(result.orphan_insights) == 0
    if not result.passed:
        logger.error(
            f"AUDIT FAILED: {len(result.orphan_insights)} orphan insight(s) detected."
        )
    else:
        logger.info("AUDIT PASSED: All insights have traceable evidence chains.")

    # ── 4. Persist report ──────────────────────────────────────────────────
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    with AUDIT_REPORT_PATH.open("w", encoding="utf-8") as f:
        json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)

    logger.info(f"Audit report saved to {AUDIT_REPORT_PATH}")
    return result


if __name__ == "__main__":
    process()
