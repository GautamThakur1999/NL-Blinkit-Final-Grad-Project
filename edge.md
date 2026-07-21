# Edge Cases — Blinkit Category-Exploration Project

> Catalogue of edge cases that can break, bias, or discredit each stage of the build,
> with the handling strategy for each. Companion to `ARCHITECTURE.md`.
> Convention: **[MUST]** = handled in code/process from day one · **[WATCH]** =
> monitored, handled if it occurs · **[ACCEPT]** = documented limitation.

---

## 1. Stage 1 — Data Collection

### 1.1 Play Store / App Store

| # | Edge case | Why it matters | Handling |
|---|---|---|---|
| C1 | **Scraper rate-limiting / IP blocks** mid-collection | Partial dataset silently treated as complete | **[MUST]** Persist progress cursor; resume support; log expected-vs-collected counts |
| C2 | **App Store RSS caps out** (~500 most recent reviews per storefront) | Small, recency-biased iOS sample | **[MUST]** Label iOS data as recency-limited in methodology; never claim parity with Play Store volume |
| C3 | **Rating-only reviews (no text)** | Inflate counts, add zero qualitative signal | **[MUST]** Drop from corpus, but keep aggregate rating stats separately |
| C4 | **Emoji-only / one-word reviews** ("good", "🔥🔥") | No analyzable signal | **[MUST]** Filter below minimum-token threshold in Stage 2 |
| C5 | **Review-bombing waves** (e.g., driver-strike or price-controversy periods where thousands of 1-star reviews land in days) | A one-off event masquerades as a stable theme | **[MUST]** Timestamp-cluster detection: flag date-spiked review bursts; triangulation rule already prevents single-source themes |
| C6 | **Fake / incentivized 5-star reviews** (templated praise) | Pollutes positive-signal analysis | **[MUST]** Near-duplicate/template detection in dedupe pass |
| C7 | **Developer replies scraped alongside reviews** | Non-user text contaminates the corpus | **[MUST]** Strip reply fields at collection time |
| C8 | **Regional-language reviews** (Devanagari Hindi, Tamil, Bengali…) | Dropping them biases toward English-speaking metro users — but mistranslating them corrupts quotes | **[MUST]** Keep English + Hinglish (Latin script) as primary corpus; regional-script reviews are counted and acknowledged as a limitation, not silently discarded — **[ACCEPT]** full multilingual analysis is out of scope |
| C9 | **Scraper library breaks** (Google/Apple change their frontend) | Collection stage fails entirely | **[WATCH]** Pin library versions; raw data persisted immediately so a break never loses collected data |
| C10 | **Wrong storefront/region** (non-India reviews) | Blinkit is India-only; foreign-store reviews are noise or a different app | **[MUST]** Pin collection to India storefronts (`gl=IN` / `country=in`) |

### 1.2 Reddit

| # | Edge case | Why it matters | Handling |
|---|---|---|---|
| C11 | **"Grofers" legacy mentions** — Blinkit was named Grofers until Dec 2021; older India threads discuss the same product under the old name | Missing this cuts out years of relevant discussion | **[MUST]** Include "Grofers" in query families; tag such items with `era: grofers` so time-sensitive claims aren't misattributed to current Blinkit |
| C12 | **`[deleted]` / `[removed]` comments** | Broken evidence chain if quoted | **[MUST]** Skip at collection; never quote content that can't be traced |
| C13 | **Bot comments** (AutoModerator, repost bots) | Non-human "user voice" | **[MUST]** Filter known bot authors + boilerplate patterns |
| C14 | **Brand-name collisions** ("blink it", Blink cameras, blinking) | Irrelevant matches pollute corpus | **[MUST]** Context-window keyword check at collection + Stage 2 relevance filter catches the rest |
| C15 | **Sarcasm / irony** ("Sure, I *love* paying ₹50 delivery for one Maggi") | Sentiment and barrier tags invert | **[WATCH]** Tagging prompt includes sarcasm gold examples; human spot-check measures the miss rate |
| C16 | **Cross-posts & quote-reposts of the same story** | One anecdote counted as many | **[MUST]** URL-canonical + text-similarity dedupe across subreddits |
| C17 | **Reddit API rate limits** (unauthenticated JSON ~ tight; authenticated better) | Slow/partial collection | **[MUST]** Throttle + backoff; authenticated app credentials if volume requires |
| C18 | **Thread context loss** — a comment saying "never again" is meaningless without its parent | Untraceable/uninterpretable evidence | **[MUST]** Store thread title + parent snippet in the `context` field of every record |
| C19 | **Posts later deleted after collection** — source URL dies before submission | Traceability audit "fails" on genuinely real data | **[MUST]** Snapshot verbatim text + metadata at collection time; audit distinguishes "URL dead" from "quote unverifiable at collection" |

### 1.3 Forums / Social / General

| # | Edge case | Why it matters | Handling |
|---|---|---|---|
| C20 | **Login-walled or JS-rendered content** (X/Twitter, some forums) | Can't collect at scale | **[ACCEPT]** Already architected as supplementary + curated-with-URL only; never load-bearing |
| C21 | **PII inside review/post text** (phone numbers, order IDs, full names — common in angry Indian app reviews) | Privacy violation if it lands in submission artifacts | **[MUST]** PII-redaction pass in Stage 2 (regex: phone/email/order-id patterns); author handles anonymized at collection |
| C22 | **Screenshots instead of text** (users post grievances as images) | Signal invisible to a text pipeline | **[ACCEPT]** Out of scope; documented limitation |
| C23 | **ToS / robots.txt constraints on scraping** | Academic-integrity and legal risk in a graded submission | **[MUST]** Public-data-only, rate-limited, documented collection methods; no login-gated scraping, no circumvention |

---

## 2. Stage 2 — Normalization & Filtering

| # | Edge case | Why it matters | Handling |
|---|---|---|---|
| P1 | **Hinglish code-switching** ("bhaiya ne late kar diya but sabzi fresh thi") | Naive language filters drop the most authentic Indian user voice | **[MUST]** Language filter keeps Latin-script Hinglish; relevance LLM prompt explicitly instructed it will see Hinglish |
| P2 | **Encoding corruption** (emoji, Devanagari, smart quotes → mojibake in JSON, especially on Windows) | Corrupted verbatim quotes fail the traceability audit | **[MUST]** UTF-8 everywhere explicitly (`encoding="utf-8"` on every read/write — Windows defaults to cp1252); round-trip test in CI of the pipeline |
| P3 | **Over-aggressive relevance filtering** — ops complaints (expiry, damaged items, wrong item) look "irrelevant" but ARE the trust-barrier evidence (H3) | The most important signal gets filtered out | **[MUST]** Filter rule: ops/quality complaints are `partial`-relevant by default, never auto-dropped; false-negative check on a sample of rejected items |
| P4 | **Near-duplicates with minor edits** (same user reposting, templated complaints) | Double-counted evidence | **[MUST]** Fuzzy dedupe (normalized text similarity threshold), keep earliest instance |
| P5 | **Extremely long posts** (2,000-word Reddit rants) exceeding tagging-call limits | Truncation loses the relevant part | **[MUST]** Chunk-then-tag long items; `key_quote` must still be a verbatim substring of the original |
| P6 | **Class imbalance** — delivery/app-bug complaints vastly outnumber category-behavior signal | Themes about ops drown out cross-category insights | **[MUST]** Purpose-built relevance filter is the defense; report corpus composition stats so the skew is visible and honest |
| P7 | **Timestamp chaos** (epoch vs ISO, IST vs UTC across sources) | Review-bomb detection (C5) and era-tagging (C11) break | **[MUST]** Normalize all dates to UTC ISO-8601 at collection |

---

## 3. Stage 3 — AI Analysis (Gemini / Groq)

| # | Edge case | Why it matters | Handling |
|---|---|---|---|
| A1 | **Invalid / malformed JSON from LLM** | Batch tagging crashes or silently drops items | **[MUST]** Strict schema validation per response; auto-retry with error feedback; dead-letter file for repeated failures (never silently skip) |
| A2 | **Hallucinated or "cleaned-up" quotes** — model paraphrases instead of extracting verbatim | Breaks the core evidence-traceability guarantee | **[MUST]** Programmatic substring check: `key_quote` must appear verbatim in source text, else the tag is rejected and retried |
| A3 | **Prompt injection via review text** — a review/post containing text like "ignore previous instructions…" | Corpus content is untrusted input to the LLM | **[MUST]** Reviews passed as clearly delimited data blocks; system prompt states user content is data, never instructions; spot-check injection-looking items |
| A4 | **Gemini safety filters blocking profane reviews** (angry Indian app reviews contain abuse) | Legitimate data silently dropped → sampling bias | **[MUST]** Detect `SAFETY`-blocked responses; route those items to Groq instead; count and report blocked items |
| A5 | **Multi-barrier items** (one review shows both trust anxiety AND price perception) | Forcing single labels loses signal | **[MUST]** `barriers` is an array by schema design (already in ARCHITECTURE.md) |
| A6 | **Items fitting no barrier** | Forced classification fabricates evidence | **[MUST]** `none` and `other/emergent` are legal tags; "no signal" is a valid outcome |
| A7 | **Tag drift across batches** (model tags "price" as `trust_quality` in batch 1, `price_perception` in batch 40) | Inconsistent taxonomy corrupts theme counts | **[MUST]** Fixed taxonomy + gold examples in every batch prompt; low temperature; spot-check spread across batches, not just the start |
| A8 | **Quota exhaustion mid-run** (Gemini daily caps, Groq RPM) | Half-tagged corpus | **[MUST]** Already architected: batching, backoff, persisted intermediates, resumable stages |
| A9 | **Model deprecation/change between runs** (free-tier models rotate) | Results not reproducible at submission time | **[MUST]** Record exact model IDs + run dates in METHODOLOGY.md; persist all outputs — the submission cites persisted artifacts, not "re-run it yourself" |
| A10 | **Degenerate clustering** — one mega-theme ("delivery problems") swallows everything, or themes fragment into 40 micro-themes | Useless synthesis | **[MUST]** Clustering prompt constraints (theme count range, max share per theme); human review of the theme list before insight generation |
| A11 | **Theme below triangulation threshold but genuinely important** (e.g., pet-owner signal is rare but pointed) | Rigid threshold discards a real niche insight | **[MUST]** Sub-threshold themes reported in a separate "weak signals" section with explicit low-confidence labeling — visible, not promoted, not hidden |
| A12 | **Cross-model disagreement** (Gemini's counter-evidence pass contradicts Groq's tags) | Which one is right? | **[MUST]** Disagreements resolved by human review; disagreement rate itself is reported as a validation metric |
| A13 | **Context overflow on synthesis** (corpus too large even for Gemini's window) | Synthesis silently sees partial data | **[MUST]** Synthesis consumes themes+evidence (already the design), not raw corpus; if theme evidence is huge, sample quotes with counts noted |

---

## 4. Stage 4 — Validation & Reporting

| # | Edge case | Why it matters | Handling |
|---|---|---|---|
| V1 | **Spot-check agreement comes back low** (< ~80%) | Insights built on unreliable tags | **[MUST]** Pre-committed protocol: revise taxonomy/prompt, re-tag affected batches, re-check — and report both rounds honestly |
| V2 | **An insight survives triangulation but is contradicted by counter-evidence** | Cherry-picking accusation risk | **[MUST]** Report both sides with quote counts; downgrade confidence label; carry the open question into interviews |
| V3 | **All five hypotheses confirmed, nothing emergent** | Smells like confirmation bias to any good evaluator | **[WATCH]** If emergent slot stays empty, explicitly interrogate: was the taxonomy too coarse? Document the check |
| V4 | **Evidence overload in the report** (500 quotes) | Unreadable deliverable | **[MUST]** Report shows top exemplar quotes per theme + full counts; complete evidence lives in `data/analysis/` as the auditable layer |

---

## 5. Part 2 — User Interviews

| # | Edge case | Why it matters | Handling |
|---|---|---|---|
| R1 | **Recruits don't match the target segment** (friends-of-convenience sampling) | Validation is theater | **[MUST]** 3–4 question screener derived from segment definition; screener + responses included in research artifacts |
| R2 | **Leading questions** ("Don't you think Blinkit's discovery is bad?") | Manufactured confirmation | **[MUST]** Guide reviewed for neutrality; insights tested indirectly (behavior questions before opinion questions) |
| R3 | **Social desirability + recall bias** — people can't accurately say *why* they don't explore categories | Self-report ≠ behavior | **[MUST]** Anchor on concrete recent behavior ("open your Blinkit order history — walk me through the last 5 orders") not hypotheticals |
| R4 | **Interviews flatly contradict the AI insights** | Feels like project failure | **[MUST]** Pre-committed framing: contradiction is a *finding* (already a guardrail); confirm/contradict matrix has a `contradicted` column by design |
| R5 | **n=5–6 overgeneralization** | "All users want X" from six people | **[MUST]** Findings phrased as "5 of 6 participants…"; qualitative claims only, no percentages |
| R6 | **Interviewee privacy** | Same anonymity bar the owner requires for themselves | **[MUST]** Participants coded P1–P6; no names/contacts in any artifact; verbal consent noted |
| R7 | **No-shows / dropouts below 5 completed interviews** | Fails the assignment's explicit 5–6 requirement | **[MUST]** Over-recruit (8–9 scheduled for 6 completed) |

---

## 6. Part 3 — Problem Definition

| # | Edge case | Why it matters | Handling |
|---|---|---|---|
| D1 | **Multiple root causes with comparable evidence** | Unfocused problem statement → unfocused MVP | **[MUST]** Pick primary root cause by explicit criteria (evidence strength × addressability × business impact); others documented as secondary |
| D2 | **Root cause isn't app-addressable** (e.g., "Blinkit's non-grocery prices are just higher") | MVP can't fix pricing | **[WATCH]** MVP then targets the *decision layer* around the barrier (e.g., value transparency), and the framing says so honestly |
| D3 | **Chosen segment too narrow to matter** (e.g., pet owners ≪ MAC base) | Business-sense section falls apart | **[MUST]** Sanity-check segment size against public market data before locking Part 3 |

---

## 7. Part 4 — MVP (Vercel + Railway + Gemini/Groq)

### 7.1 Build & runtime

| # | Edge case | Why it matters | Handling |
|---|---|---|---|
| M1 | **Serverless timeout vs LLM latency** — Vercel hobby function limits vs multi-second LLM calls | Requests die mid-generation | **[MUST]** Streaming responses; latency-sensitive calls go to Groq (fastest); long reasoning pre-computed, not done per-request |
| M2 | **Railway free-tier sleep/credit exhaustion** — backend cold or dead exactly when the evaluator opens the link | Demo fails at grading time | **[MUST]** Keep backend thin enough that Vercel-only is viable fallback; check credit balance before submission week; document a local-run fallback in README |
| M3 | **LLM provider outage/quota during evaluation** | Live demo breaks | **[MUST]** Provider fallback flag (Gemini↔Groq, already architected) + graceful degraded mode (cached example responses clearly labeled as cached) |
| M4 | **Hallucinated recommendations** — suggesting products/categories Blinkit doesn't actually sell | Instantly discredits the MVP | **[MUST]** Ground generation against the curated catalogue sample; validate outputs against it before display; never free-generate product names |
| M5 | **Prompt injection / abuse by MVP users** | Public URL = untrusted input | **[MUST]** Input length caps, delimited user input, no tool/secret access from the prompt path, output filtered to the feature's scope |
| M6 | **Empty/adversarial inputs** (blank cart, gibberish, 10,000-char paste) | Unhandled crashes in front of the evaluator | **[MUST]** Input validation + sensible empty states; test matrix before submission |
| M7 | **CORS between Vercel frontend and Railway backend** | Classic silent integration failure | **[MUST]** Explicit CORS allowlist for the Vercel domain; verified in deployed environment, not just localhost |
| M8 | **Secrets leakage** — API keys in client bundle, committed `.env`, or exposed error traces | Key theft → quota drained → demo dead | **[MUST]** Keys server-side only; `.env` gitignored from first commit; error responses sanitized |
| M9 | **Cold-start UX** (first request after idle takes 10–15s) | Evaluator's first impression is a spinner | **[MUST]** Loading states with progress feedback; optional warm-up ping documented |
| M10 | **Mobile rendering** — evaluators may open the link on a phone; the subject *is* a mobile app | Broken mobile layout undermines credibility | **[MUST]** Mobile-first responsive check before submission |

### 7.2 Anonymity (cross-cutting with owner directive)

| # | Edge case | Why it matters | Handling |
|---|---|---|---|
| M11 | **Vercel/Railway default URLs contain the account username** | Identity leak in the submission link | **[MUST]** Neutral project names → neutral generated URLs; verify final URL before submission |
| M12 | **Git commit author name/email in repo history** | Identity leak if repo is shared/public | **[MUST]** Set repo-local `user.name`/`user.email` to neutral values *before first commit* (history rewrites are painful) |
| M13 | **GitHub account visible via repo link** | Same leak, different door | **[MUST]** If a repo link is required in submission, use a neutrally-named org/account, or submit code as a zip |
| M14 | **Page metadata / package.json author field / LICENSE name** | Small print leaks | **[MUST]** Pre-submission grep for the owner's name/email across all artifacts |

---

## 8. Cross-Cutting

| # | Edge case | Why it matters | Handling |
|---|---|---|---|
| X1 | **Windows dev environment quirks** (cp1252 default encoding, path separators, console emoji crashes) | Pipeline works "on my machine" only, corrupts UTF-8 data | **[MUST]** Explicit UTF-8 on all file I/O; `pathlib` everywhere; no emoji in console logging |
| X2 | **Large data files bloating the repo** | Push failures, unreviewable repo | **[MUST]** `data/raw/` gitignored; small representative samples committed for reviewability |
| X3 | **Reproducibility of LLM outputs** | Evaluator re-runs get different results | **[ACCEPT + MUST]** LLM outputs are inherently nondeterministic — mitigate by persisting every artifact and citing artifacts (not re-runs) in the submission; model IDs + dates recorded |
| X4 | **Copyright/quoting hygiene** — verbatim user quotes in a public deliverable | Over-quoting third-party content | **[MUST]** Quotes kept short (excerpts), attributed to source platform + URL, used for research commentary — standard fair-dealing research practice |
| X5 | **Scope creep** — pipeline gold-plating eats the time budget for Parts 2–4 | Unfinished project beats polished Part 1 | **[MUST]** Each stage has a "good enough" bar (defined in ARCHITECTURE.md outputs); MVP feature intentionally thin |

---

## 9. Top 10 Highest-Risk (build these defenses first)

1. **A2 — Verbatim-quote enforcement** (substring check): the whole evidence story rests on it.
2. **P3 — Relevance filter false negatives**: don't filter out the trust-barrier evidence.
3. **C5 — Review-bomb distortion**: date-spike detection before theming.
4. **C11 — Grofers-era data**: include it, era-tag it.
5. **A1/A8 — Malformed responses + quota exhaustion**: resumable, validated batch processing.
6. **M4 — Hallucinated recommendations**: catalogue-grounded generation only.
7. **M2/M3 — Demo dies at evaluation time**: fallbacks + pre-submission checks.
8. **M11–M14 — Anonymity leaks**: neutral naming from the very first commit.
9. **P2/X1 — Windows encoding corruption**: UTF-8 discipline from file one.
10. **R1/R3 — Interview validity**: screener + behavior-anchored questions.
