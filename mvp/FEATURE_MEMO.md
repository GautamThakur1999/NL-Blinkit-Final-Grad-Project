# MVP Feature Decision Memo (T7.1)

**Target Problem (Root Cause):** Intent Blindness (Users are too fast/grocery-focused to browse for non-groceries).

## Candidate Feature Shapes
1. **Trust-Builder Overlay:** AI-generated summaries of reviews and specs on product detail pages (electronics, cosmetics).
   - *Verdict:* Discard. If users never navigate to the product page due to intent blindness, they will never see this feature.
2. **List-to-Suggestions Agent:** User types a raw list ("I need stuff for a party"), AI converts to items.
   - *Verdict:* Discard. High friction. Requires the user to change their behavior and *choose* to type a prompt instead of using the reorder widget they love.
3. **Category-Bridge Recommender (Cart-Completion Interceptor):** A passive intelligence layer on the Cart screen that observes the grocery basket and time-context to surface *exactly one* highly relevant non-grocery item right before checkout.
   - *Verdict:* **Selected.**

## The Selected Feature: Cart-Completion Interceptor
**How it works:**
- The user shops normally for their routine groceries.
- On the Cart page, the AI intercepts the context: `Cart Items` + `Time of Day` + `Day of Week`.
- It selects the single most relevant cross-category product from the Blinkit catalogue and displays a native-looking "Forgot this?" tile.
- Example: Cart contains [Milk, Bread, Eggs] on a Saturday at 8 PM → AI suggests "Playing Cards" or "Bluetooth Speaker".

**Why this shape?**
- **Zero Friction:** It does not interrupt the 15-second reorder loop. It is a single, passive tap target on the cart screen.
- **Directly Addresses Intent Blindness:** It bypasses the need for the user to browse banners. It pushes discovery directly into the high-intent checkout flow.
- **Thin Scope:** We only need to build a single API endpoint that takes a cart array and returns one item ID, plus a minimal UI component in the cart.
