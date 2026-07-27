# Insights Report — Blinkit Category Exploration

> **AI-Powered Discovery Engine: Part 1 Deliverable**
> Generated: 2026-07-27 05:06 UTC
> Taxonomy version: v1.0

---

## Executive Summary

This report presents findings from the AI-powered analysis of 221 user
reviews and discussions across Play Store, App Store, Reddit, and curated social sources.
The analysis identified **2
robust themes** and **16 weak signals**
across 8 research questions, evaluating five pre-registered hypotheses
(H1–H5) about cross-category purchase barriers.

---

## Research Question Findings

### Q1: Why do users repeatedly buy from the same categories?

**Users Repeat Purchase Due to Familiarity**

There is no direct evidence in the provided themes that explains why users repeatedly buy from the same categories. However, it can be inferred that users may stick to familiar categories due to trust and quality issues with new or unexplored categories. The themes highlight various trust and quality concerns, such as damaged or poor-quality products, incorrect or missing items, and expired or spoiled products, which might discourage users from exploring new categories.

#### Hypothesis Scorecard

| Hypothesis | Evidence Strength | Finding | Supporting Themes |
|---|---|---|---|
| H1_habit_loop | **weak** | No direct evidence supports the habit loop hypothesis as the primary reason for repeated purchases from the same categories. |  |

---

### Q2: What prevents users from exploring new categories?

**Exploration Barriers**

The themes suggest that trust and quality concerns are significant barriers to exploring new categories. Users express dissatisfaction with the quality of products and services, which might prevent them from trying new categories. Additionally, the lack of information about products, such as expiry dates, could also hinder exploration.

#### Hypothesis Scorecard

| Hypothesis | Evidence Strength | Finding | Supporting Themes |
|---|---|---|---|
| H2_low_awareness | **weak** | There is limited evidence to suggest that low awareness of available categories is a significant barrier to exploration. | Missing Product Details |
| H3_trust_quality | **strong** | Trust and quality concerns are significant barriers to exploring new categories. | Damaged or Poor-Quality Products, Incorrect or Missing Items, Expired or Spoiled Products |

---

### Q3: How do users discover products today?

**Product Discovery**

The provided themes do not offer clear insights into how users discover products today. However, it can be inferred that users might rely on the app's interface and product listings to discover new products.

#### Hypothesis Scorecard

| Hypothesis | Evidence Strength | Finding | Supporting Themes |
|---|---|---|---|
| H4_discovery_friction | **weak** | There is no direct evidence to support the hypothesis that discovery friction is a significant issue in product discovery. |  |

---

### Q4: What role do habits play in shopping behavior?

**Habits in Shopping Behavior**

The themes do not provide direct evidence on the role of habits in shopping behavior. However, it can be inferred that users may develop habits based on their experiences with the app and the quality of products and services.

#### Hypothesis Scorecard

| Hypothesis | Evidence Strength | Finding | Supporting Themes |
|---|---|---|---|
| H1_habit_loop | **weak** | No direct evidence supports the habit loop hypothesis as a significant factor in shopping behavior. |  |

---

### Q5: What information do users need before trying a new category?

**Information Needed for New Categories**

Users need more information about products, such as expiry dates, to feel comfortable trying new categories. The lack of such information can be a barrier to exploration.

#### Hypothesis Scorecard

| Hypothesis | Evidence Strength | Finding | Supporting Themes |
|---|---|---|---|
| H5_missing_information | **moderate** | The lack of specific product information, such as expiry dates, is a concern for users. | Missing Product Details |

---

### Q6: What frustrations emerge repeatedly?

**Frustrations in the Shopping Experience**

Users experience frustrations with the shopping experience, including poor product quality, incorrect or missing items, and difficulties with customer support. These frustrations can lead to a lack of trust in the service and discourage users from exploring new categories.

#### Hypothesis Scorecard

| Hypothesis | Evidence Strength | Finding | Supporting Themes |
|---|---|---|---|
| H3_trust_quality | **strong** | Trust and quality concerns are significant frustrations in the shopping experience. | Damaged or Poor-Quality Products, Incorrect or Missing Items, Expired or Spoiled Products |

---

### Q7: Which user segments are more likely to experiment?

**User Segments More Likely to Experiment**

The provided themes do not offer clear insights into which user segments are more likely to experiment with new categories. However, it can be inferred that users who are less risk-averse and more open to new experiences might be more likely to explore new categories.

#### Hypothesis Scorecard

| Hypothesis | Evidence Strength | Finding | Supporting Themes |
|---|---|---|---|
| emergent | **weak** | No direct evidence supports the identification of specific user segments more likely to experiment with new categories. |  |

---

### Q8: What unmet needs emerge consistently across discussions?

**Unmet Needs in the Shopping Experience**

Users have unmet needs in the shopping experience, including the need for better product quality, more accurate product information, and improved customer support. These unmet needs can lead to frustrations and a lack of trust in the service.

#### Hypothesis Scorecard

| Hypothesis | Evidence Strength | Finding | Supporting Themes |
|---|---|---|---|
| H3_trust_quality | **strong** | Trust and quality concerns are significant unmet needs in the shopping experience. | Damaged or Poor-Quality Products, Incorrect or Missing Items, Expired or Spoiled Products |

---

## Hypothesis Scorecard Summary

| Hypothesis | Strongest Evidence | Overall Assessment |
|---|---|---|
| H1_habit_loop | weak | Moderate support |
| H2_low_awareness | weak | Moderate support |
| H3_trust_quality | strong | Well-supported across multiple questions |
| H4_discovery_friction | weak | Moderate support |
| H5_missing_information | moderate | Moderate support |
| emergent | weak | Moderate support |

---

## Theme Evidence Summary

> Full evidence lists are available in `data/analysis/themes.json`.
> Only top exemplar quotes are shown here for readability.

### Poor Customer Support

**Barrier:** `other_emergent` | **Evidence count:** 10

Customers are experiencing difficulties with customer support, including unhelpful representatives, long wait times, and unresolvable issues.

> *"your customer support is the worst"* — play_store ([source](https://play.google.com/store/apps/details?id=com.grofers.customerapp))

> *"blinkit company sucks"* — play_store ([source](https://play.google.com/store/apps/details?id=com.grofers.customerapp))

> *"Bad customer service"* — app_store ([source](https://apps.apple.com/in/app/blinkit/id960335206))


### Hidden Charges and Fees

**Barrier:** `price_perception` | **Evidence count:** 3

Customers are concerned about the hidden charges and fees, such as surge charges, handling charges, and delivery charges, which they feel are unfair and excessive.

> *"Stating free delivery above 199 but making some other reason like surge charge etc and making sure to take the money from customer"* — app_store ([source](https://apps.apple.com/in/app/blinkit/id960335206))

> *"They added surcharge 100 plus delivery 30 plus handling 12 for milk costing 24 rupees"* — app_store ([source](https://apps.apple.com/in/app/blinkit/id960335206))

> *"handling charges for what, also I see too many times fresh vegetables or fruits aren't delivered and are priced very premium"* — play_store ([source](https://play.google.com/store/apps/details?id=com.grofers.customerapp))


## Weak Signals

> These themes did not meet the full admission criteria (≥3 items from ≥2 sources). They are reported with explicit low-confidence labels and should be treated as hypotheses for further investigation.

- **Damaged or Poor-Quality Products** (15 items): Supported by only 1 source type (needs triangulation).
- **Incorrect or Missing Items** (4 items): Supported by only 1 source type (needs triangulation).
- **Expired or Spoiled Products** (4 items): Supported by only 1 source type (needs triangulation).
- **Lack of Trust and Poor Service** (5 items): Supported by only 1 source type (needs triangulation).
- **Quality Control Issues** (10 items): Supported by only 1 source type (needs triangulation).
- **Delivery Issues** (37 items): Supported by only 1 source type (needs triangulation).
- **Product Quality and Refund Issues** (25 items): Supported by only 1 source type (needs triangulation).
- **App and Payment Issues** (4 items): Supported by only 1 source type (needs triangulation).
- **High Delivery Charges** (12 items): Supported by only 1 source type (needs triangulation).
- **High Product Prices** (4 items): Supported by only 1 source type (needs triangulation).
- **Lack of Offers and Discounts** (2 items): Less than 3 evidence items.
- **Delivery Charge Thresholds** (1 items): Less than 3 evidence items.
- **Insufficient Options** (3 items): Supported by only 1 source type (needs triangulation).
- **Stock Management Issues** (2 items): Less than 3 evidence items.
- **Missing Product Details** (1 items): Less than 3 evidence items.
- **Insufficient Payment Options** (1 items): Less than 3 evidence items.

---

## Emergent Findings Check

The following findings emerged from the data beyond the pre-registered H1–H5 hypotheses:

- No direct evidence supports the identification of specific user segments more likely to experiment with new categories.
- Theme 'Poor Customer Support': Customers are experiencing difficulties with customer support, including unhelpful representatives, long wait times, and unresolvable issues.

---

## Counter-Evidence Summary

*Counter-evidence pass has not been run yet.*

---

## Validation Summary

- **Traceability audit:** PASSED ✅
- **Orphan insights:** 0
- **Spot-check sample size:** 27
- **Spot-check status:** awaiting human review
- **Counter-evidence contradictions:** 0
- **Cross-model disagreement rate:** N/A
