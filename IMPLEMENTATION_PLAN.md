# Implementation Plan — Blinkit Category-Exploration Project

> Executable build plan synthesizing `context.md` (goals, directives),
> `ARCHITECTURE.md` (design), and `edge.md` (edge cases C1–C23, P1–P7, A1–A13,
> V1–V4, R1–R7, D1–D3, M1–M14, X1–X5).
> Every **[MUST]** edge case is assigned to a concrete task — see the coverage
> matrix in §10 for proof that nothing is missed.

**Stack (fixed):** Python pipeline · Groq API (high-volume tagging) · Gemini API
(long-context synthesis) · Next.js on Vercel + FastAPI on Railway for the MVP ·
zero paid services.

**Standing rules on every task (from working directives):**
- No personal details of the project owner in any file, config, commit, URL, or artifact.
- Everything oriented at cross-category purchase barriers — not generic sentiment.
- Persist every intermediate; any stage re-runnable in isolation.

---

## Phase 0 — Foundations & Hardening

*Goal: a project skeleton where the cross-cutting edge cases are impossible by
construction, before any feature code exists.*

| Task | What to build | Edge cases closed |
|---|---|---|
| **T0.1** | `git init`; set **repo-local** `user.name`/`user.email` to neutral values **before the first commit**; neutral repo/folder naming throughout | M12, M13 |
| **T0.2** | `.gitignore` from day one: `.env*`, `data/raw/`, `node_modules/`, caches. Commit small representative data samples only | M8, X2 |
| **T0.3** | Python venv + `requirements.txt` with **pinned versions** (`google-play-scraper`, `requests`, `groq`, `google-genai`, `pydantic`, `rapidfuzz`) | C9 |
| **T0.4** | `pipeline/common.py`: UTF-8-explicit file I/O helpers (`encoding="utf-8"` mandatory — Windows defaults to cp1252), `pathlib` everywhere, JSONL read/write, UTC ISO-8601 date normalizer, ASCII-only console logging | P2, P7, X1 |
| **T0.5** | `.env.example` + config loader for `GEMINI_API_KEY`, `GROQ_API_KEY`; keys only ever read from environment | M8 |
| **T0.6** | `pipeline/llm.py` — single LLM gateway used by ALL later stages: provider abstraction (Gemini/Groq behind one interface), request batching, exponential backoff, **resume cursors persisted to disk**, strict Pydantic schema validation of responses, **dead-letter file** for repeat failures (never silent skips), Gemini `SAFETY`-block detection with automatic reroute to Groq + blocked-item counter, **model ID + timestamp logged on every call**, corpus text always passed inside clearly delimited data blocks with a data-not-instructions system preamble | A1, A3, A4, A8, A9 |

**Exit criteria:** UTF-8 round-trip test passes on a sample containing emoji + Devanagari + smart quotes; LLM gateway smoke-tests against both providers; `git log` shows neutral author only.

---

## Phase 1 — Stage 1: Collection (`pipeline/collectors/`)

*Goal: raw, schema-valid, provenance-complete data from every viable source.*

All collectors emit the **raw record schema** from ARCHITECTURE §3.1 and write
immediately to `data/raw/<source>.jsonl` (a crash never loses collected data — C9).
Author handles are anonymized/omitted at write time (C21-partial).

| Task | What to build | Edge cases closed |
|---|---|---|
| **T1.1** | `queries.py` — the keyword-steered **query family config** (reorder/habit, category-avoidance, channel-preference, trust/quality, discovery language) shared by all collectors; includes **"Grofers"** terms | C11 (partial) |
| **T1.2** | `play_store.py` — `google-play-scraper` against the Blinkit app id, **India storefront pinned** (`gl=IN`); progress cursor + resume; expected-vs-collected count logging; strip developer replies; drop rating-only reviews into a separate aggregate-stats file (not the corpus) | C1, C3, C7, C10 |
| **T1.3** | `app_store.py` — iTunes RSS review feed, `country=in`; output labeled `recency_limited: true` (RSS caps ~500 recent reviews) so METHODOLOGY reports it honestly | C2, C10 |
| **T1.4** | `reddit.py` — public JSON API over r/india, r/indiasocial, r/bangalore, r/delhi, r/mumbai + keyword search incl. Grofers; **era tag** (`era: grofers/blinkit`) by post date vs Dec-2021 rebrand; skip `[deleted]`/`[removed]`; known-bot + boilerplate filter; **store thread title + parent-comment snippet in `context`**; canonical-URL recording for cross-post dedupe; throttle + backoff (authenticated app creds if volume needs); **verbatim snapshot at collection time** so later deletions can't break traceability | C11, C12, C13, C16, C17, C18, C19 |
| **T1.5** | `forums.py` / `social.py` — curated collection: every item requires a public URL; records marked `collection_method: curated`, `supplementary: true`; no login-gated scraping, no circumvention, rate-limited fetches only | C20, C23 |
| **T1.6** | Brand-collision guard: context-window keyword check at collection ("blinkit/grofers" must co-occur with shopping context, not Blink cameras / "blink it") | C14 |
| **T1.7** | `collection_report.py` — per-source counts (expected vs collected), date ranges, regional-script counts, era split. Feeds METHODOLOGY.md | C1, C8 (visibility) |

**Exit criteria:** `data/raw/` populated from ≥3 source types; every record schema-validates; collection report generated; zero owner-identifying data anywhere.

---

## Phase 2 — Stage 2: Normalize & Filter (`pipeline/processing/`)

*Goal: `data/clean/corpus.jsonl` — deduped, PII-safe, relevance-filtered, provenance-preserving.*

| Task | What to build | Edge cases closed |
|---|---|---|
| **T2.1** | `clean.py` — whitespace/emoji-noise normalization into `text` while preserving untouched `text_raw` (verbatim-quote ground truth); minimum-token filter drops emoji-only/one-word items | C4, P2 |
| **T2.2** | `dedupe.py` — fuzzy near-duplicate detection (`rapidfuzz` normalized similarity threshold), keeps earliest instance; catches templated fake-review clusters and cross-post repeats (using T1.4 canonical URLs) | C6, C16, P4 |
| **T2.3** | `language.py` — keep English + Latin-script Hinglish; regional-script (Devanagari/Tamil/Bengali…) items **counted and set aside**, never silently discarded; count goes to METHODOLOGY as a stated limitation | C8, P1 |
| **T2.4** | `pii_redact.py` — regex redaction of phone numbers, emails, order IDs, long digit runs from all text fields before anything reaches the corpus | C21 |
| **T2.5** | `burst_detect.py` — timestamp-cluster detection on normalized UTC dates; items inside date-spiked bursts get `burst_flag: true` (review-bombing context visible to theming and reporting) | C5, P7 |
| **T2.6** | `relevance.py` — two-pass filter: (1) cheap keyword pass with the hard rule that **ops/quality complaints are `partial` by default and never auto-dropped** (they are H3 trust-barrier evidence); (2) Groq LLM scoring `relevant_to_category_behavior: yes/partial/no` + one-line rationale, prompt explicitly primed for Hinglish input. Only `yes/partial` proceed | P1, P3 |
| **T2.7** | Rejection audit — random sample (~50) of `no`-scored items manually reviewed for false negatives before the corpus is frozen; result recorded in METHODOLOGY | P3 |
| **T2.8** | `composition_report.py` — corpus composition stats (source mix, ops-vs-category-signal ratio, sentiment mix) so class imbalance is visible and honestly reported | P6 |

**Exit criteria:** frozen `corpus.jsonl`; rejection audit passed; PII scan of corpus returns clean; composition report generated.

---

## Phase 3 — Stage 3: AI Analysis (`pipeline/analysis/`)

*Goal: tagged corpus → triangulated themes → insights answering the brief's 8 questions.*

| Task | What to build | Edge cases closed |
|---|---|---|
| **T3.1** | `taxonomy.py` — fixed barrier taxonomy (H1–H5 + `price_perception`, `assortment_gap`, `none`, `other_emergent`) with definitions + **gold examples including sarcasm and Hinglish cases**; version-controlled so tag runs cite a taxonomy version | C15, A6, A7 |
| **T3.2** | `tagger.py` (Groq, low temperature, via T0.6 gateway) — per-item structured tagging to the ARCHITECTURE §3.3a schema; `barriers` is an array (multi-barrier legal); `none` is a legal outcome; **programmatic verbatim check: `key_quote` must be a substring of `text_raw`, else reject + retry, then dead-letter**; long items chunked with quote-substring rule still enforced per chunk; fully resumable batches | A1, A2, A5, A6, A8, P5 |
| **T3.3** | `themer.py` (Gemini) — cross-source clustering of tagged items; **admission rule: ≥N items from ≥2 source types**; burst-flagged items can support but not solely constitute a theme; prompt constraints on theme count range and max single-theme share; sub-threshold themes routed to a **"weak signals" section** with explicit low-confidence labels; every theme stores its full evidence list (ids → quotes → URLs) | C5, A10, A11 |
| **T3.4** | **Human checkpoint** — manual review of the theme list before synthesis (merge/split/rename); documented in METHODOLOGY | A10 |
| **T3.5** | `insights.py` (Gemini) — synthesis against the **8 research questions**; consumes themes + evidence only (never raw corpus — bounded context); produces the **hypothesis scorecard** (H1–H5: strong/moderate/weak/contradicted + emergent findings) | A13 |
| **T3.6** | `counter_evidence.py` — for each major insight, the **opposite-provider model** searches the corpus for contradicting quotes (Gemini checks Groq-derived claims and vice versa); contradictions attached to the insight record, never dropped | A12, V2 |

**Exit criteria:** `tags.jsonl` 100% schema-valid with zero unverifiable quotes; theme list human-approved; insights generated with scorecard; counter-evidence attached.

---

## Phase 4 — Stage 4: Validation & Part 1 Reporting (`pipeline/validation/`, `outputs/`)

*Goal: provable insight quality — the assignment's explicit "how you validated" requirement.*

| Task | What to build | Edge cases closed |
|---|---|---|
| **T4.1** | `audit.py` — automated traceability audit: every insight → ≥1 theme → ≥N verbatim quotes → source URLs; **distinguishes "URL now dead (snapshot exists)" from "unverifiable at collection"**; any orphan insight fails the report build | C19, A2 (verification) |
| **T4.2** | `spotcheck.py` — sampling tool: 10–15% of tagged items **spread across all batches** (not just early ones), presented for human tag agreement; **pre-committed protocol: if agreement < 80% → revise taxonomy/prompt → re-tag → re-check, and report both rounds** | A7, V1 |
| **T4.3** | Validation metrics roll-up — spot-check agreement rate, cross-model disagreement rate, safety-blocked count, single-source-flag count | A4, A12 |
| **T4.4** | `outputs/INSIGHTS_REPORT.md` — answers to all 8 questions; top exemplar quotes per theme + full counts (full evidence stays in `data/analysis/` as the audit layer); quotes kept short and attributed (platform + URL); weak-signals section; **explicit emergent-findings check** — if nothing emergent surfaced, interrogate and document why | V3, V4, X4 |
| **T4.5** | `outputs/METHODOLOGY.md` — collection methods per source, feasibility labels (iOS recency cap, curated social), regional-language and screenshot limitations, exact **model IDs + run dates**, taxonomy version, validation results, reproducibility statement (artifacts are the record; LLM outputs are nondeterministic) | C2, C8, C20, C22, A9, X3 |

**Exit criteria:** audit passes with zero orphans; spot-check ≥80% (or documented second round); both reports built. **→ Part 1 deliverable complete.**

---

## Phase 5 — Part 2: User Research (`research/`)

| Task | What to build | Edge cases closed |
|---|---|---|
| **T5.1** | Segment selection memo — pick target segment from `segment_hints` distribution + hypothesis scorecard; **early segment-size sanity check** vs public market data (don't wait for Part 3 to discover the segment is too small) | D3 (early) |
| **T5.2** | `research/SCREENER.md` — 3–4 question screener derived from the segment definition; screener + anonymized responses kept as artifacts | R1 |
| **T5.3** | `research/INTERVIEW_GUIDE.md` — neutral, non-leading; **behavior-anchored**: order-history walkthrough ("open Blinkit, walk me through your last 5 orders") before any opinion questions; each top AI insight mapped to an indirect probe; guide reviewed against a leading-question checklist | R2, R3 |
| **T5.4** | Recruiting plan — **schedule 8–9 to complete ≥6** (assignment floor is 5) | R7 |
| **T5.5** | Conduct interviews — participants coded **P1–P6**, verbal consent noted, zero names/contacts in any artifact; notes per participant in `research/notes/` | R6 |
| **T5.6** | `research/SYNTHESIS.md` — notes coded with the **same taxonomy version** as Stage 3; findings phrased as "5 of 6 participants…" (no percentages, no "all users"); contradictions of AI insights recorded as first-class findings | R4, R5 |

**Exit criteria:** ≥5 completed screened interviews, synthesis coded on the shared taxonomy. **→ Part 2 deliverable complete.**

---

## Phase 6 — Part 3: Problem Definition (`outputs/PROBLEM_DEFINITION.md`)

| Task | What to build | Edge cases closed |
|---|---|---|
| **T6.1** | **Confirm/contradict matrix** — every Part 1 insight × interview evidence → `confirmed / partially confirmed / contradicted / untested` | R4 |
| **T6.2** | Root-cause selection — explicit scoring: evidence strength × app-addressability × business impact; secondary causes documented, not hidden; if the root cause isn't directly app-addressable (e.g., pricing), the MVP targets the decision layer around it and the doc says so plainly | D1, D2 |
| **T6.3** | Final segment-size validation vs public data (revisit T5.1 with interview learnings) | D3 |
| **T6.4** | Assemble the document: target segment, root cause, existing workarounds (channel-alternative tags + interview evidence), user value, business value tied to the north-star metric | — |

**Exit criteria:** one primary root cause selected by stated criteria; matrix complete. **→ Part 3 deliverable complete. MVP feature decision unblocked.**

---

## Phase 7 — Part 4: MVP Build & Deploy (`mvp/`)

*Feature is chosen in T7.1 from the validated root cause (deferred by design —
ADR 7). Infrastructure tasks below hold regardless of feature choice.*

| Task | What to build | Edge cases closed |
|---|---|---|
| **T7.1** | Feature decision memo — map root cause → the candidate shapes (category-bridge recommender / trust-builder overlay / list-to-suggestions agent) → pick one, scoped deliberately thin; must not add friction to the reorder loop | X5 |
| **T7.2** | Grounding data — curated Blinkit catalogue sample (real categories/products) + insight-derived rules; **generation validates against it: no free-generated product names, ever** | M4 |
| **T7.3** | Backend (`mvp/api/`, FastAPI → Railway) — provider fallback flag (Gemini↔Groq); **streaming responses**; input validation: length caps, delimited user input, empty-input handling; no secrets/tools reachable from the prompt path; sanitized error responses; **explicit CORS allowlist for the Vercel domain**; degraded mode serving clearly-labeled cached examples if both providers fail | M1, M3, M5, M6, M7, M8 |
| **T7.4** | Frontend (`mvp/web/`, Next.js → Vercel) — **mobile-first** (the subject is a mobile app; evaluators will open on phones); loading states with progress feedback for cold starts; sensible empty states | M6, M9, M10 |
| **T7.5** | Deploy — **neutral project names on both platforms → neutral URLs (verify before sharing)**; API keys via platform env vars only; if backend stays thin, Vercel API routes alone are the fallback deployment (Railway optional) | M2, M8, M11 |
| **T7.6** | Pre-demo test matrix — blank/gibberish/10k-char inputs, mobile viewport, cold-start timing, quota-exhausted degraded mode, CORS verified **on the deployed URLs** (not just localhost) | M3, M6, M7, M9, M10 |
| **T7.7** | `mvp/README.md` — run-locally fallback instructions (if free tiers die at grading time), architecture note linking the feature to the validated root cause | M2 |

**Exit criteria:** live public URL passes the full test matrix; a stranger's phone can use it. **→ Part 4 deliverable complete.**

---

## Phase 8 — Final QA & Submission Gate

Run in order; all must pass:

1. **Identity grep** — search every artifact (docs, code, configs, `package.json`
   author fields, LICENSE, page metadata, MVP UI) for the owner's name/email → zero hits. (M14)
2. **Git history check** — `git log --format="%an %ae"` shows neutral identity only. (M12)
3. **URL check** — deployed URLs contain no username/identity. (M11)
4. **Repo-link policy** — neutral account/org, or submit code as zip. (M13)
5. **Free-tier health** — Railway credit balance, provider quotas, warm-up ping done in submission week. (M2, M3)
6. **Artifact completeness** — all Part 1–4 outputs persisted and cited by the
   submission (never "re-run to see"); model IDs + dates present in METHODOLOGY. (A9, X3)
7. **Secrets scan** — no keys in repo history; `.env` never committed. (M8)
8. **Data hygiene** — `data/raw/` excluded; committed samples PII-clean. (C21, X2)

---

## 9. Sequencing, Dependencies & Scope Guards

```
Phase 0 ──► Phase 1 ──► Phase 2 ──► Phase 3 ──► Phase 4 ──► Phase 5 ──► Phase 6 ──► Phase 7 ──► Phase 8
(found.)   (collect)   (clean)     (analyze)   (validate)  (interviews) (define)    (MVP)       (QA gate)
                                                    │
                                                    └── T5.2/T5.3 (screener+guide) can start as soon as
                                                        the hypothesis scorecard exists (overlap allowed)
```

- **Interviews are the schedule bottleneck** (human availability) — start recruiting
  (T5.4) as soon as the segment memo (T5.1) exists, in parallel with Phase 4.
- **Scope guard (X5):** each phase's exit criteria above **is** the good-enough bar.
  When a phase meets its bar, move on — an unfinished Part 4 loses more marks than an
  unpolished Part 1. MVP is intentionally thin by decision T7.1.
- **Build-first defenses:** Phase 0 exists precisely to close the Top-10 list from
  `edge.md` §9 before feature work begins (verbatim-quote check lands with T3.2, the
  first task that generates quotes).

---

## 10. Edge-Case Coverage Matrix (completeness proof)

Every edge case from `edge.md` → owning task(s):

| Edge case | Owner | | Edge case | Owner | | Edge case | Owner |
|---|---|---|---|---|---|---|---|
| C1 | T1.2, T1.7 | | P1 | T2.3, T2.6 | | M1 | T7.3 |
| C2 | T1.3, T4.5 | | P2 | T0.4, T2.1 | | M2 | T7.5, T7.7, QA-5 |
| C3 | T1.2 | | P3 | T2.6, T2.7 | | M3 | T7.3, T7.6, QA-5 |
| C4 | T2.1 | | P4 | T2.2 | | M4 | T7.2 |
| C5 | T2.5, T3.3 | | P5 | T3.2 | | M5 | T7.3 |
| C6 | T2.2 | | P6 | T2.8 | | M6 | T7.3, T7.4, T7.6 |
| C7 | T1.2 | | P7 | T0.4, T2.5 | | M7 | T7.3, T7.6 |
| C8 | T1.7, T2.3, T4.5 | | A1 | T0.6, T3.2 | | M8 | T0.2, T0.5, T7.3, T7.5, QA-7 |
| C9 | T0.3, Phase-1 write-immediately rule | | A2 | T3.2, T4.1 | | M9 | T7.4, T7.6 |
| C10 | T1.2, T1.3 | | A3 | T0.6 | | M10 | T7.4, T7.6 |
| C11 | T1.1, T1.4 | | A4 | T0.6, T4.3 | | M11 | T7.5, QA-3 |
| C12 | T1.4 | | A5 | T3.2 | | M12 | T0.1, QA-2 |
| C13 | T1.4 | | A6 | T3.1, T3.2 | | M13 | T0.1, QA-4 |
| C14 | T1.6, T2.6 | | A7 | T3.1, T4.2 | | M14 | QA-1 |
| C15 | T3.1 | | A8 | T0.6, T3.2 | | X1 | T0.4 |
| C16 | T1.4, T2.2 | | A9 | T0.6, T4.5, QA-6 | | X2 | T0.2, QA-8 |
| C17 | T1.4 | | A10 | T3.3, T3.4 | | X3 | T4.5, QA-6 |
| C18 | T1.4 | | A11 | T3.3 | | X4 | T4.4 |
| C19 | T1.4, T4.1 | | A12 | T3.6, T4.3 | | X5 | T7.1, §9 scope guard |
| C20 | T1.5, T4.5 | | A13 | T3.5 | | R1 | T5.2 |
| C21 | Phase-1 anonymize, T2.4, QA-8 | | V1 | T4.2 | | R2 | T5.3 |
| C22 | T4.5 (documented limit) | | V2 | T3.6 | | R3 | T5.3 |
| C23 | T1.5 | | V3 | T4.4 | | R4 | T5.6, T6.1 |
| — | — | | V4 | T4.4 | | R5 | T5.6 |
| — | — | | D1 | T6.2 | | R6 | T5.5 |
| — | — | | D2 | T6.2 | | R7 | T5.4 |
| — | — | | D3 | T5.1, T6.3 | | — | — |

**Coverage: 66/66 edge cases assigned.** [ACCEPT]-class cases (C8-full-multilingual,
C20, C22, X3-nondeterminism) are owned as *documented limitations* in T4.5, which is
itself a task — acceptance is explicit, never silent.

---

## 11. Deliverable → Assignment Requirement Map

| Assignment requirement | Produced by |
|---|---|
| Part 1: workflow gathers & analyzes data | Phases 1–3 code + METHODOLOGY.md |
| Part 1: how themes are identified | T3.3 + T3.4 (documented in METHODOLOGY) |
| Part 1: how insights are generated | T3.5 + INSIGHTS_REPORT.md |
| Part 1: how insight quality was validated | Phase 4 (audit, spot-check, counter-evidence, triangulation) |
| Part 1: answers the 8 research questions | INSIGHTS_REPORT.md structure |
| Part 2: 5–6 interviews in chosen segment | T5.4/T5.5 (over-recruited, screened) |
| Part 3: segment, root cause, workarounds, user value, business value | PROBLEM_DEFINITION.md (T6.4) |
| Part 3: AI insights validated/challenged by research | Confirm/contradict matrix (T6.1) |
| Part 4: functional AI-native MVP | Phase 7 |
| Part 4: deployed to production | T7.5 (Vercel + Railway, public URL) |
