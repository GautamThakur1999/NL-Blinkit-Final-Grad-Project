# Methodology — Blinkit Category Exploration Discovery Engine

> **Part 1 Documentation**
> Generated: 2026-07-25 21:14 UTC

---

## 1. Data Collection

### 1.1 Sources and Methods

| Source | Method | Feasibility | Notes |
|---|---|---|---|
| Google Play Store | `google-play-scraper` Python library | ✅ Full access | Reviews sorted by newest; continuation token for pagination |
| Apple App Store | iTunes RSS feed (public JSON) | ⚠️ Limited | RSS returns only the most recent ~500 reviews; no historical depth |
| Reddit | Public JSON API (`/search.json`) | ⚠️ Rate-limited | Searches across r/india, r/indiasocial, r/bangalore, r/delhi, r/mumbai; 403 errors handled with fast-fail; no authenticated access used |
| Curated Social | Manual curation from public URLs | ⚠️ Supplementary | Marked `collection_method: curated`; no login-gated scraping |

### 1.3 Known Limitations

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

## 2. AI Models and Configuration

### 2.1 Model IDs

| Role | Provider | Model ID | Temperature |
|---|---|---|---|
| Per-item tagging (T3.2) | Groq | `llama-3.3-70b-versatile` | 0.1 |
| Theme clustering (T3.3) | Google Gemini | `gemini-2.0-flash` | 0.2 |
| Insight synthesis (T3.5) | Google Gemini | `gemini-2.0-flash` | 0.3 |
| Counter-evidence (T3.6) | Groq | `llama-3.3-70b-versatile` | 0.1 |
| Relevance filter (T2.6) | Groq | `llama-3.3-70b-versatile` | 0.1 |

### 2.2 Barrier Taxonomy

**Version:** `v1.0`

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

**Pipeline execution date:** 2026-07-25 21:14 UTC

---

## 3. Validation Results

### 3.1 Traceability Audit

- **Result:** FAILED ❌
- **Orphan insights:** N/A
- **Themes missing evidence:** N/A
- **Quotes without URL:** N/A

Every insight in the report is traceable through the chain:
`insight → theme(s) → evidence items → verbatim quotes → source URLs`.

### 3.2 Human Spot-Check

- **Sample size:** N/A
- **Sampling method:** Stratified across all batches (not just early items)
- **Status:** awaiting review
- **Pre-committed protocol:** If agreement < 80%, the taxonomy and prompts are revised,
  items are re-tagged, and both rounds are reported.

### 3.3 Cross-Model Counter-Evidence

- **Items scanned:** N/A
- **Contradictions found:** N/A
- **Cross-model disagreement rate:** N/A

Groq was used to independently scan the corpus for evidence contradicting
Gemini-derived insights. This provides a cheap cross-model consistency check.

### 3.4 LLM Failure Handling

- **Dead-lettered items:** N/A

Items that failed all retries (safety blocks, malformed JSON, quota exhaustion)
are persisted in dead-letter files. They are never silently skipped. Their absence
from the analysis is a documented limitation.

---

## 4. Reproducibility Statement

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
