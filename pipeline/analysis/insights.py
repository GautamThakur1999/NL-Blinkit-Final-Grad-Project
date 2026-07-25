"""
pipeline/analysis/insights.py — Insights Synthesis (T3.5)

Synthesizes generated themes against the 8 research questions.
Produces the hypothesis scorecard and maps evidence.
Only consumes themes + evidence (bounded context), never the raw corpus.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from pipeline.analysis.schemas import InsightsResponse, ThemerResponse
from pipeline.common import ANALYSIS_DIR, setup_logging
from pipeline.llm import Provider, get_gateway

logger = logging.getLogger(__name__)

THEMES_PATH = ANALYSIS_DIR / "themes.json"
INSIGHTS_PATH = ANALYSIS_DIR / "insights.json"

RESEARCH_QUESTIONS = [
    "Q1: Why do users repeatedly buy from the same categories?",
    "Q2: What prevents users from exploring new categories?",
    "Q3: How do users discover products today?",
    "Q4: What role do habits play in shopping behavior?",
    "Q5: What information do users need before trying a new category?",
    "Q6: What frustrations emerge repeatedly?",
    "Q7: Which user segments are more likely to experiment?",
    "Q8: What unmet needs emerge consistently across discussions?"
]

HYPOTHESES = [
    "H1: Habit loop (entrenched in routines)",
    "H2: Low awareness (don't know Blinkit has the category)",
    "H3: Trust/Quality anxiety (fear of bad produce/fakes)",
    "H4: Discovery friction (UI/UX makes it hard to find)",
    "H5: Missing information (no expiry/dimensions)"
]


def process() -> None:
    setup_logging()
    logger.info("Starting T3.5 Insights Synthesis...")

    if not THEMES_PATH.exists():
        logger.warning(f"Themes file not found: {THEMES_PATH}")
        return

    with THEMES_PATH.open("r", encoding="utf-8") as f:
        themes_data = json.load(f)
        
    themes = themes_data.get("themes", [])
    if not themes:
        logger.warning("No themes found to synthesize.")
        return

    gateway = get_gateway()
    
    system_msg = (
        "You are a lead product researcher synthesizing consumer insights for Blinkit.\n"
        "Your task is to analyze the provided 'Themes' (which contain clustered user quotes) "
        "and generate final insights against 8 specific Research Questions.\n\n"
        "Research Questions to Answer:\n"
        + "\n".join(f"- {q}" for q in RESEARCH_QUESTIONS) + "\n\n"
        "Initial Hypotheses to Evaluate:\n"
        + "\n".join(f"- {h}" for h in HYPOTHESES) + "\n\n"
        "CRITICAL RULES:\n"
        "1. GROUNDING: Base your insights STRICTLY on the provided themes and quotes. Do not hallucinate or guess.\n"
        "2. STRUCTURE: Return a JSON conforming to the requested schema. Ensure every research question is addressed.\n"
        "3. SCORECARD: For each insight, score the relevant hypotheses as 'strong', 'moderate', 'weak', or 'contradicted' based on the evidence volume and clarity in the themes. You can also define an 'emergent' hypothesis if a new one arises.\n"
        "4. THEME LINKING: Explicitly list the `theme_name`s that support each scorecard."
    )

    user_content = json.dumps({"themes": themes}, indent=2)

    logger.info("Sending themes to Gemini for insight synthesis...")
    try:
        parsed_res, meta = gateway.call(
            provider=Provider.GEMINI,
            system_prompt=system_msg,
            user_content=user_content,
            schema=InsightsResponse,
            temperature=0.3
        )
        
        with INSIGHTS_PATH.open("w", encoding="utf-8") as f:
            json.dump(parsed_res.model_dump(), f, indent=2, ensure_ascii=False)
            
        logger.info(f"Insights generated and saved to {INSIGHTS_PATH}")
        
    except Exception as e:
        logger.error(f"Insight synthesis failed: {e}")


if __name__ == "__main__":
    process()
