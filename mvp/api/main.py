import json
import os
import asyncio
from pathlib import Path
from typing import List, AsyncGenerator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, constr
import httpx
from dotenv import load_dotenv

# Load env variables (for local dev, Railway sets them in the environment)
load_dotenv(Path(__file__).parent.parent.parent / ".env")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

app = FastAPI(title="Blinkit Discovery MVP API")

# M7: Explicit CORS allowlist.
#
# NOTE: production runs the recommender as a Next.js route handler at
# /api/recommend (same origin), so CORS does not apply there. This FastAPI
# service is the local-development and alternative-hosting path.
#
# Origins come from the ALLOWED_ORIGINS env var (comma-separated) so the
# deployed frontend domain is configured at deploy time rather than hardcoded —
# the previous hardcoded placeholder domains did not exist and would have failed
# silently in production.
_DEFAULT_ORIGINS = "http://localhost:3000,http://localhost:5173"
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("ALLOWED_ORIGINS", _DEFAULT_ORIGINS).split(",")
    if origin.strip()
]

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# M4: Grounding data
CATALOG_PATH = Path(__file__).parent.parent / "data" / "catalog.json"
with open(CATALOG_PATH, "r", encoding="utf-8") as f:
    CATALOG = json.load(f)

CATALOG_PROMPT_BLOCK = json.dumps([{
    "id": item["id"], 
    "name": item["name"], 
    "category": item["category"],
    "tags": item["tags"]
} for item in CATALOG])


# Input validation (M1: length caps, empty-input handling)
class CartRequest(BaseModel):
    items: List[constr(max_length=50, strip_whitespace=True)] = Field(
        ..., 
        max_length=20,
        description="List of items in the cart (max 20 items, max 50 chars each)"
    )
    time_of_day: constr(max_length=20, strip_whitespace=True)
    day_of_week: constr(max_length=20, strip_whitespace=True)

# Degraded mode (M7)
DEGRADED_RESPONSE = "We couldn't connect to our live discovery engine. But did you know we deliver UNO cards in 10 minutes?|||item_401"

SYSTEM_PROMPT = f"""You are a smart shopping assistant for Blinkit.
The user is about to checkout with some groceries. You must suggest EXACTLY ONE highly relevant non-grocery item from the provided catalog.

CATALOG:
{CATALOG_PROMPT_BLOCK}

CRITICAL RULES:
1. Do not recommend an item they already have.
2. The recommendation must make sense based on the cart items, time of day, and day of week.
3. Keep the rationale under 2 sentences. Be friendly and conversational.
4. You MUST output exactly in this format:
<rationale>|||<item_id>

Example Output:
Late night snack? You might also need a charger for your phone!|||item_102
"""

async def call_gemini_stream(user_prompt: str) -> AsyncGenerator[str, None]:
    # gemini-1.5-flash returns 404 for API keys issued after its retirement to
    # new users; gemini-flash-latest is the current free-tier alias.
    model = os.environ.get("MODEL_GEMINI", "gemini-flash-latest")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent?alt=sse&key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "systemInstruction": {"role": "system", "parts": [{"text": SYSTEM_PROMPT}]},
        "generationConfig": {"temperature": 0.5, "maxOutputTokens": 100}
    }
    
    async with httpx.AsyncClient() as client:
        async with client.stream("POST", url, json=payload, timeout=10.0) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        continue
                    try:
                        data = json.loads(data_str)
                        if "candidates" in data and len(data["candidates"]) > 0:
                            parts = data["candidates"][0]["content"].get("parts", [])
                            if parts:
                                text_chunk = parts[0].get("text", "")
                                if text_chunk:
                                    yield text_chunk
                    except json.JSONDecodeError:
                        pass

async def call_groq_stream(user_prompt: str) -> AsyncGenerator[str, None]:
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    payload = {
        # llama3-8b-8192 is decommissioned on Groq.
        "model": os.environ.get("MODEL_GROQ", "llama-3.3-70b-versatile"),
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.5,
        "max_tokens": 100,
        "stream": True
    }
    
    async with httpx.AsyncClient() as client:
        async with client.stream("POST", url, headers=headers, json=payload, timeout=10.0) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        continue
                    try:
                        data = json.loads(data_str)
                        if "choices" in data and len(data["choices"]) > 0:
                            delta = data["choices"][0].get("delta", {})
                            text_chunk = delta.get("content", "")
                            if text_chunk:
                                yield text_chunk
                    except json.JSONDecodeError:
                        pass

@app.post("/api/recommend")
async def recommend_item(req: CartRequest):
    # Empty-input handling (M1)
    if not req.items:
        raise HTTPException(status_code=400, detail="Cart cannot be empty.")
    
    user_prompt = (
        f"<USER_DATA>\n"
        f"Cart: {', '.join(req.items)}\n"
        f"Time: {req.time_of_day}\n"
        f"Day: {req.day_of_week}\n"
        f"</USER_DATA>"
    )

    async def stream_response() -> AsyncGenerator[str, None]:
        # Provider fallback (M3)
        try:
            if not GEMINI_API_KEY:
                raise ValueError("Gemini key missing")
            # Try Gemini first
            async for chunk in call_gemini_stream(user_prompt):
                yield chunk
            return
        except Exception as e:
            print(f"Gemini failed: {e}")
            
        try:
            if not GROQ_API_KEY:
                raise ValueError("Groq key missing")
            # Fallback to Groq
            async for chunk in call_groq_stream(user_prompt):
                yield chunk
            return
        except Exception as e:
            print(f"Groq failed: {e}")
            
        # Degraded Mode (M7)
        yield DEGRADED_RESPONSE

    return StreamingResponse(stream_response(), media_type="text/plain")

@app.get("/health")
def health_check():
    return {"status": "ok", "degraded": not GEMINI_API_KEY and not GROQ_API_KEY}
