"""
pipeline/validation/report_methodology.py — METHODOLOGY.md Generator (T4.5)

Generates `outputs/METHODOLOGY.md` documenting:
  • Collection methods per source + feasibility labels
  • Regional-language and screenshot limitations
  • Exact model IDs + run dates
  • Taxonomy version
  • Validation results (spot-check, traceability audit)
  • Reproducibility statement

Edge cases closed: C2, C8, C20, C22, A9, X3.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from pipeline.analysis.taxonomy import TAXONOMY_VERSION
from pipeline.common import (
    ANALYSIS_DIR,
    DATA_DIR,
    OUTPUTS_DIR,
    RAW_DIR,
    setup_logging,
    write_text,
)
from pipeline import config

logger = logging.getLogger(__name__)

METRICS_PATH = ANALYSIS_DIR / "validation_metrics.json"
COMPOSITION_PATH = ANALYSIS_DIR / "composition_report.json"
REPORT_PATH = OUTPUTS_DIR / "METHODOLOGY.md"


def _load_json_safe(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def process() -> None:
    setup_logging()
    logger.info("Starting T4.5 METHODOLOGY.md generation...")

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    metrics = _load_json_safe(METRICS_PATH)
    composition = _load_json_safe(COMPOSITION_PATH)

    sections = []

    # ── Header ─────────────────────────────────────────────────────────────
    sections.append(f"""# Methodology — Blinkit Category Exploration Discovery Engine

> **Part 1 Documentation**
> Generated: {now}

---

## 1. Data Collection

### 1.1 Sources and Methods

| Source | Method | Feasibility | Notes |
|---|---|---|---|
| Google Play Store | `google-play-scraper` Python library | ✅ Full access | Reviews sorted by newest; continuation token for pagination |
| Apple App Store | iTunes RSS feed (public JSON) | ⚠️ Limited | RSS returns only the most recent ~500 reviews; no historical depth |
| Reddit | Public JSON API (`/search.json`) | ⚠️ Rate-limited | Searches across r/india, r/indiasocial, r/bangalore, r/delhi, r/mumbai; 403 errors handled with fast-fail; no authenticated access used |
| Curated Social | Manual curation from public URLs | ⚠️ Supplementary | Marked `collection_method: curated`; no login-gated scraping |
""")

    # Composition stats
    source_mix = composition.get("source_mix", {})
    if source_mix:
        sections.append("### 1.2 Corpus Composition\n")
        sections.append("| Source | Count |")
        sections.append("|---|---|")
        for source, count in sorted(source_mix.items()):
            sections.append(f"| {source} | {count} |")
        sections.append(f"\n**Total corpus size:** {composition.get('total_records', 'N/A')}")
        sections.append("")

    # ── Limitations ────────────────────────────────────────────────────────
    sections.append("""### 1.3 Known Limitations

- **iOS recency cap:** App Store RSS feed returns only the most recent ~500 reviews.
  Historical reviews are not accessible without a paid API.
- **Regional-language coverage:** Reviews in non-Latin scripts (Devanagari, Tamil,
  Bengali, etc.) were identified and set aside for transparency. They are NOT silently
  discarded — they are logged in `data/intermediate/03_language_dropped.jsonl`.
  Latin-script Hinglish (e.g., "sabzi kharab aayi") is retained and analyzed.
- **Reddit availability:** Some subreddits return 403 errors to unauthenticated
  requests. The collector detects this and aborts immediately rather than hanging.
- **Screenshot evidence:** No screenshots were used as evidence. All data is text-based
  and programmatically extractable.
- **Curated items:** Items marked `supplementary: true` come from manual curation and
  should be weighted accordingly in interpretation.

---
""")

    # ── Models & Configuration ─────────────────────────────────────────────
    sections.append(f"""## 2. AI Models and Configuration

### 2.1 Model IDs

| Role | Provider | Model ID | Temperature |
|---|---|---|---|
| Per-item tagging (T3.2) | Groq | `{config.GROQ_MODEL}` | 0.1 |
| Theme clustering (T3.3) | Google Gemini | `{config.GEMINI_MODEL}` | 0.2 |
| Insight synthesis (T3.5) | Google Gemini | `{config.GEMINI_MODEL}` | 0.3 |
| Counter-evidence (T3.6) | Groq | `{config.GROQ_MODEL}` | 0.1 |
| Relevance filter (T2.6) | Groq | `{config.GROQ_MODEL}` | 0.1 |

### 2.2 Barrier Taxonomy

**Version:** `{TAXONOMY_VERSION}`

The taxonomy consists of 9 barrier categories derived from the five pre-registered
hypotheses (H1–H5) plus three additional categories (`price_perception`,
`assortment_gap`, `other_emergent`) and a `none` label. Full definitions and gold
examples (including sarcasm and Hinglish cases) are in `pipeline/analysis/taxonomy.py`.

### 2.3 Prompt Architecture

- All corpus text is wrapped in `<USER_DATA>` delimiters with a "data-not-instructions"
  system preamble to mitigate prompt injection (A3).
- Tagging prompts include the full taxonomy with definitions and gold examples.
- A **programmatic verbatim check** enforces that `key_quote` is an exact (normalized)
  substring of the original `text_raw`. Failures trigger automatic retries; persistent
  failures are dead-lettered (never silently skipped).

### 2.4 Run Date

**Pipeline execution date:** {now}

---
""")

    # ── Validation ─────────────────────────────────────────────────────────
    sections.append("## 3. Validation Results\n")

    # Traceability audit
    audit = metrics.get("traceability_audit", {})
    sections.append(f"""### 3.1 Traceability Audit

- **Result:** {'PASSED ✅' if audit.get('passed') else audit.get('status', 'FAILED ❌')}
- **Orphan insights:** {audit.get('orphan_insights', 'N/A')}
- **Themes missing evidence:** {audit.get('themes_missing_evidence', 'N/A')}
- **Quotes without URL:** {audit.get('quotes_without_url_count', 'N/A')}

Every insight in the report is traceable through the chain:
`insight → theme(s) → evidence items → verbatim quotes → source URLs`.
""")

    # Spot-check
    sc = metrics.get("spotcheck", {})
    sections.append(f"""### 3.2 Human Spot-Check

- **Sample size:** {sc.get('sample_size', 'N/A')}
- **Sampling method:** Stratified across all batches (not just early items)
- **Status:** {sc.get('status', sc.get('barrier_agreement_rate', 'awaiting review'))}
- **Pre-committed protocol:** If agreement < 80%, the taxonomy and prompts are revised,
  items are re-tagged, and both rounds are reported.
""")

    # Counter-evidence
    ce = metrics.get("counter_evidence", {})
    sections.append(f"""### 3.3 Cross-Model Counter-Evidence

- **Items scanned:** {ce.get('total_items_scanned', 'N/A')}
- **Contradictions found:** {ce.get('total_contradictions_found', 'N/A')}
- **Cross-model disagreement rate:** {ce.get('cross_model_disagreement_rate', 'N/A')}

Groq was used to independently scan the corpus for evidence contradicting
Gemini-derived insights. This provides a cheap cross-model consistency check.
""")

    # LLM failures
    llm = metrics.get("llm_failures", {})
    sections.append(f"""### 3.4 LLM Failure Handling

- **Dead-lettered items:** {llm.get('total_dead_lettered_items', 'N/A')}

Items that failed all retries (safety blocks, malformed JSON, quota exhaustion)
are persisted in dead-letter files. They are never silently skipped. Their absence
from the analysis is a documented limitation.

---
""")

    # ── Reproducibility ────────────────────────────────────────────────────
    sections.append("""## 4. Reproducibility Statement

This pipeline produces **deterministic data processing** (collection, cleaning,
deduplication, PII redaction, burst detection) and **non-deterministic AI analysis**
(tagging, theming, synthesis, counter-evidence).

**What is reproducible:**
- The same raw data will always produce the same clean corpus.
- The same clean corpus with the same taxonomy version will produce the same
  tag prompts.

**What is not reproducible:**
- LLM outputs are inherently non-deterministic. Even with `temperature=0.1`,
  re-running the tagging or synthesis stages may produce slightly different outputs.
- The persisted intermediates (`data/state/`, `data/analysis/`) ARE the record of
  each run. They should be versioned or archived alongside the report.

**Artifact preservation:**
All intermediate files are persisted to disk. Any stage can be re-run in isolation
without affecting prior or subsequent stages. The `data/state/` directory contains
cursor files enabling crash-safe resume of batch LLM calls.
""")

    # Write
    report_text = "\n".join(sections)
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    write_text(REPORT_PATH, report_text)

    logger.info(f"METHODOLOGY.md generated at {REPORT_PATH}")


if __name__ == "__main__":
    process()
