# Final Grad Project — Problem Statement

## Blinkit: Driving Category Exploration Among Repeat Shoppers

**Role:** Product Manager, Growth Team — Blinkit
**Date:** July 2026
**Status:** Problem Definition — v1.0

---

## 1. Company & Product Context

**Chosen product: Blinkit** (quick-commerce platform, India; owned by Eternal Ltd,
formerly Zomato).

Blinkit delivers groceries, snacks, household essentials, and an expanding catalogue of
categories (personal care, baby care, pet supplies, electronics accessories, pharmacy,
stationery, festive/seasonal goods, and more) in ~10–15 minutes via a network of dark
stores across Indian cities.

Quick commerce has successfully embedded itself into users' **weekly routines**. For
millions of Monthly Active Customers (MACs), Blinkit is no longer a novelty — it is the
default way to restock the kitchen and the home.

---

## 2. The Business Problem

### 2.1 What is happening

Over time, shopping behavior on Blinkit becomes **highly repetitive**:

- Users purchase the **same set of products** week after week (milk, bread, eggs,
  snacks, beverages, cleaning supplies).
- Users **rarely explore new categories**, even though the platform's catalogue has
  grown far beyond groceries.
- Repeat purchase behavior — normally a strength — has created a **habit ceiling**:
  the very routines that drive retention also suppress discovery.

### 2.2 The strategic goal

> **Increase the percentage of Monthly Active Customers who purchase products from at
> least one *new* category every month.**

Illustrative examples of the desired behavior shift:

| Current behavior | Desired expansion |
|---|---|
| Buys groceries only | Starts buying **pet supplies** |
| Buys snacks & beverages | Starts buying **personal care** products |
| Buys household essentials | Starts buying **baby products** |

### 2.3 Why this matters to the business

- **AOV & basket depth:** Multi-category customers build larger, higher-margin baskets.
- **Margin mix:** Non-grocery categories (personal care, pet care, general merchandise)
  typically carry better margins than staple groceries.
- **Retention & LTV:** Customers who shop across more categories have more reasons to
  return and are harder for competitors (Zepto, Swiggy Instamart) to poach.
- **Catalogue ROI:** Blinkit has invested in expanding dark-store assortment; that
  investment only pays off if users actually discover and adopt new categories.

---

## 3. The User Problem (Hypothesis)

Users are not exploring new categories, likely because of some combination of:

- **Habit loops:** The app experience is optimized for speed and reorder — users open
  the app with a fixed mental list, buy, and leave in under 2 minutes.
- **Low awareness:** Users simply don't know Blinkit sells categories beyond groceries
  (e.g., pet supplies, pharmacy, electronics accessories).
- **Trust & quality anxiety:** For unfamiliar categories, users default to trusted
  specialist channels (chemist, pet store, Nykaa, Amazon) — price, authenticity, and
  quality concerns block trial.
- **Discovery friction:** Search-and-reorder flows dominate; there is little in-app
  browsing behavior or serendipity comparable to offline supermarket aisles.
- **Missing information:** Users may need reviews, comparisons, usage guidance, or
  social proof before trying a new category — information the current experience
  doesn't surface at the moment of decision.

*(These are hypotheses to be tested in Parts 1 and 2 — not conclusions.)*

---

## 4. Project Scope — Four Parts

### Part 1: Build an AI-Powered Discovery Engine

Before proposing any solution, build a **working AI system** that analyzes user
feedback **at scale**. Permitted stack: Claude, GPTs, agents, workflows, RAG systems,
n8n, Zapier, Perplexity, or any AI-native stack.

**Data sources to analyze:**

- App Store reviews
- Play Store reviews
- Reddit discussions
- Community forums
- Social media conversations
- Product reviews
- Quick-commerce discussions

**Questions the discovery engine must help answer:**

1. Why do users repeatedly buy from the same categories?
2. What prevents users from exploring new categories?
3. How do users discover products today?
4. What role do habits play in shopping behavior?
5. What information do users need before trying a new category?
6. What frustrations emerge repeatedly?
7. Which user segments are more likely to experiment?
8. What unmet needs emerge consistently across discussions?

**Must demonstrate:**

- How the workflow gathers and analyzes data
- How themes are identified
- How insights are generated
- How the quality of insights was validated

### Part 2: Validate the Opportunity Through User Research

AI-generated insights are only a starting point. Validate findings through **primary
research**: conduct **5–6 user interviews** with respondents belonging to the chosen
target segment.

### Part 3: Define the Problem

Based on the research, frame the problem by clearly articulating:

- The **target user segment**
- The **root cause** of the problem
- **Existing user workarounds**
- Why solving the problem creates **user value**
- Why solving the problem makes **business sense**

Must demonstrate how primary research **validated or challenged** the insights surfaced
by the AI-powered discovery engine.

### Part 4: Build an AI-Native MVP

Based on the insights, design and build a **functional MVP**, which may take the form of:

- A prototype for a feature within the existing product
- An AI-powered workflow
- An AI agent

**The MVP must be deployed to production** (a live, usable artifact — not a mockup).

---

## 5. Success Criteria for the Project

| Part | Evidence of success |
|---|---|
| 1 — Discovery Engine | A working pipeline with traceable insights (theme → supporting quotes → source), plus a documented validation method |
| 2 — User Research | 5–6 completed interviews with a defined segment; synthesized findings |
| 3 — Problem Definition | A crisp problem statement tying segment, root cause, workarounds, user value, and business value together — with explicit confirm/contradict mapping against AI insights |
| 4 — MVP | A deployed, functional AI-native product that addresses the validated root cause |

**North-star metric (product):** % of MACs purchasing from ≥1 new category per month.

**Supporting metrics (candidates):** new-category trial rate, repeat rate within a
newly tried category (2nd purchase in 30 days), categories per customer per month,
incremental AOV from expansion categories.

---

## 6. Guardrails & Notes

- Insights must be **evidence-backed** — every theme traceable to real user voice
  (reviews, Reddit threads, interview quotes), not model speculation.
- Primary research can **challenge** the AI findings; divergence is a feature of the
  process, not a failure.
- The MVP must map directly to the **validated root cause**, not to a generic
  "recommendations" idea.
- Solutions must respect why users love Blinkit today (speed, convenience) — discovery
  must not add friction to the core reorder loop.
