# Phase 7 MVP: Cart-Completion Interceptor

This directory contains the final MVP deliverable for the **Blinkit Category Exploration Project**.

## Architecture & Strategy

The feature chosen is the **Cart-Completion Interceptor**.
As discovered in Phase 6, the primary barrier to cross-category purchasing on Blinkit is **Intent Blindness**. Routine shoppers are so fast and focused on their grocery restock that they completely ignore traditional discovery surfaces (banners, search recommendations).

Instead of forcing users to browse, this MVP passively intercepts their checkout flow.
When they are on the "My Cart" screen, the AI analyzes their cart items, the time of day, and the day of the week to suggest exactly **one** highly relevant non-grocery item (e.g., suggesting UNO cards if they are buying party snacks on a Saturday night). 

This solves Intent Blindness with zero friction added to the 15-second reorder loop.

---

## Pre-Demo Test Matrix (T7.6)

Before demoing to evaluators, the following edge cases have been tested and mitigated:

- **[x] Blank/Gibberish Inputs:** The FastAPI backend uses strict Pydantic validation (`CartRequest`). Empty arrays return a 400. Gibberish cart items won't break the LLM; it will gracefully fall back or ignore them.
- **[x] Length Caps (M1):** The cart array is capped at 20 items. Each item string is capped at 50 chars to prevent prompt-injection attacks.
- **[x] Mobile Viewport:** The Next.js frontend is built mobile-first (`max-w-md`) simulating a real app experience. Evaluators should open the Vercel link on their phones.
- **[x] Cold-Start Timing (M9):** Because Railway/Vercel free tiers sleep, the frontend implements a shimmering loading skeleton. It gives immediate progress feedback so the user doesn't think the app is broken during a 4-second cold start.
- **[x] Provider Fallback & Degraded Mode (M3, M7):** The backend streams Gemini first. If Gemini fails/quota exhausts, it routes to Groq (Llama 3). If both fail, it streams a hardcoded fallback (`DEGRADED_RESPONSE`) so the UI never crashes.
- **[x] CORS Verified (M8):** The FastAPI backend explicitly allows `quick-commerce-discovery-agent.vercel.app` and localhost.

---

## Run Locally (Fallback Instructions)

If free-tier platforms (Vercel/Railway) suspend the app at grading time, you can run the MVP locally in 2 minutes.

### 1. Start the Backend (FastAPI)
```bash
cd mvp/api
pip install -r requirements.txt
# Ensure GEMINI_API_KEY and GROQ_API_KEY are in a .env file at the project root
uvicorn main:app --reload --port 8000
```

### 2. Start the Frontend (Next.js)
```bash
cd mvp/web
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

The frontend will be available at `http://localhost:3000`.
