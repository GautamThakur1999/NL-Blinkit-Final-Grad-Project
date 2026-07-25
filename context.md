# Project Context — Final Grad Project (Blinkit)

> Condensed working context for this project. Full details in `PROBLEM_STATEMENT.md`.

## ▶ Start Here (for any new agent / environment, e.g. Antigravity)

1. **Read these first, in order:** `context.md` (this file) → `ARCHITECTURE.md` →
   `edge.md` → `IMPLEMENTATION_PLAN.md`. They contain the full plan; nothing critical
   lives only in chat history.
2. **Then begin at the first unchecked item** in the Status checklist at the bottom of
   this file, following `IMPLEMENTATION_PLAN.md` phase by phase (currently: Phase 0).
3. **On a fresh clone, set the neutral git identity BEFORE committing** (a new clone
   uses your global git config, which may carry personal details — see Anonymity
   directive):
   ```
   git config user.name "blinkit-growth-pm"
   git config user.email "blinkit-growth-pm@users.noreply.github.com"
   ```
4. **API keys needed for the pipeline** (set as environment variables, never commit):
   `GEMINI_API_KEY` (Google AI Studio) and `GROQ_API_KEY` (Groq console).
5. **Honor every Working Directive below** — anonymity, free-tools-only stack, and the
   cross-category-barrier focus are non-negotiable.

## Who / What

- **Project:** Final grad project — acting as a **Product Manager, Growth Team at Blinkit**.
- **Product chosen:** **Blinkit** (quick-commerce, India; owned by Eternal Ltd, formerly Zomato; ~10–15 min delivery via dark stores).

## The Problem

Quick commerce is now a weekly habit, but shopping behavior has become **highly
repetitive**: users buy the same groceries/snacks/household essentials on repeat and
**rarely explore new categories** (pet supplies, personal care, baby products, pharmacy,
etc.) despite Blinkit's expanded catalogue.

## Strategic Goal (North Star)

> **Increase the % of Monthly Active Customers (MACs) who purchase from at least one
> NEW category every month.**

Examples of desired shift: groceries → pet supplies; snacks → personal care;
household essentials → baby products.

**Why it matters:** bigger baskets/AOV, better margin mix from non-grocery categories,
higher retention/LTV vs. Zepto & Swiggy Instamart, ROI on catalogue expansion.

## Hypotheses (to test, not conclusions)

1. **Habit loops** — app optimized for fast reorder; users enter with a fixed list, exit in <2 min.
2. **Low awareness** — users don't know Blinkit sells non-grocery categories.
3. **Trust/quality anxiety** — unfamiliar categories default to trusted specialists (chemist, Nykaa, Amazon).
4. **Discovery friction** — search-and-reorder dominates; no serendipity like supermarket aisles.
5. **Missing information** — users need reviews/social proof/guidance before trying a new category.

## Project Structure (4 Parts)

| Part | Deliverable |
|---|---|
| **1. AI Discovery Engine** | Working AI pipeline (Claude/GPT/n8n/RAG/etc.) analyzing app store reviews, Reddit, forums, social media. Must show: data gathering, theme identification, insight generation, quality validation. Answers 8 research questions (why repetitive, what blocks exploration, how discovery happens, role of habit, info needs, frustrations, which segments experiment, unmet needs). |
| **2. User Research** | 5–6 primary interviews with the chosen target segment to validate/challenge AI insights. |
| **3. Problem Definition** | Target segment, root cause, existing workarounds, user value, business value + explicit confirm/contradict mapping vs. AI insights. |
| **4. AI-Native MVP** | Functional MVP (feature prototype / AI workflow / AI agent) — **deployed to production**, addressing the validated root cause. |

## Guardrails

- Every insight must be **evidence-backed and traceable** to real user voice (quote → source).
- Interviews may **contradict** AI findings — that's valid and must be documented.
- MVP must map to the **validated root cause**, not a generic recommender.
- Do not add friction to the core reorder loop (speed is why users love Blinkit).

## Candidate Metrics

- North star: % of MACs buying from ≥1 new category/month.
- Supporting: new-category trial rate, 2nd purchase in new category within 30 days,
  categories per customer per month, incremental AOV from expansion categories.

## Working Directives (from project owner)

- **Anonymity:** The project owner's name, email, or any personal details must NOT
  appear anywhere in any submission file, document, code, or deployed artifact.
- **Free-tools-only stack:** LLM layer = **Google Gemini API** (AI Studio free tier)
  + **Groq API** (free tier). Deployment = **Vercel** (frontend) + **Railway**
  (backend). No paid APIs or services anywhere in the project.

- **Reddit is out of scope.** Reddit's API returns HTTP 403 to unauthenticated
  requests, and the project owner manually searched Reddit for quick-commerce
  category discussions and found the yield poor. The collector retains OAuth
  support but Reddit is not part of the corpus; record this as a documented
  collection limitation in METHODOLOGY, not as an unfilled gap.
- **Build a real data pipeline** for Part 1 — not a one-off analysis. It must *collect*
  reviews/feedback from all viable sources (Play Store, App Store, Reddit, community
  forums, social media, product reviews, quick-commerce discussions), then
  clean → theme → generate insights.
- The pipeline's purpose is specifically to surface **why customers don't purchase
  from other categories/segments** — every collection and analysis step should be
  oriented toward cross-category purchase barriers, not generic sentiment analysis.
- Upcoming steps/prompts from the project owner will build on this pipeline —
  integrate this directive into all future work on Parts 1–4.

## Status

- [x] Problem statement written (`PROBLEM_STATEMENT.md`)
- [x] System architecture designed (`ARCHITECTURE.md`)
- [x] Edge cases catalogued (`edge.md`) — build defenses per its Top-10 list
- [x] Implementation plan written (`IMPLEMENTATION_PLAN.md`) — 9 phases, T-numbered tasks, 66/66 edge-case coverage
- [ ] Part 1: Discovery engine built
- [ ] Part 2: Interviews conducted & synthesized
- [ ] Part 3: Problem definition finalized
- [ ] Part 4: MVP built & deployed
