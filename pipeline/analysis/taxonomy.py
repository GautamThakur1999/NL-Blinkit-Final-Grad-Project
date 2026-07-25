"""
pipeline/analysis/taxonomy.py — Barrier Taxonomy Definition (T3.1)

Defines the fixed barrier taxonomy (H1-H5 + price_perception, assortment_gap, none, other_emergent)
along with definitions and gold examples (including sarcasm and Hinglish cases).
Version-controlled so tag runs cite a taxonomy version (A6, A7).
"""

from typing import Any

TAXONOMY_VERSION = "v1.0"

# Taxonomy definition
BARRIERS = {
    "habit_loop": {
        "definition": "Users are entrenched in existing habits (e.g., going to a local kirana store or supermarket) and don't think of quick commerce for this category.",
        "examples": [
            "I still prefer going to the local market for veggies, it's just what I'm used to.",
            "Subah subah doodh lane ki aadat hai, app se order karna ajeeb lagta hai."
        ]
    },
    "low_awareness": {
        "definition": "Users simply do not know that Blinkit/Grofers carries this category or these specific products.",
        "examples": [
            "Wait, you guys sell electronics too? Since when?",
            "Blinkit pe pet food milta hai mujhe pata hi nahi tha!"
        ]
    },
    "trust_quality": {
        "definition": "Anxiety about product quality, freshness, authenticity, or handling (especially for fresh produce, electronics, or high-value items).",
        "examples": [
            "I ordered apples once and they were rotten. Never buying fruits from here again.",
            "Electronics order karne mein darr lagta hai, pata nahi asli hoga ya nakli."
        ]
    },
    "discovery_friction": {
        "definition": "Users tried to find something but the UI/UX, search, or category navigation made it too hard.",
        "examples": [
            "Search is terrible. Type 'face wash' and it shows me hand wash.",
            "Category find karna itna mushkil hai, I just gave up and used Amazon."
        ]
    },
    "missing_information": {
        "definition": "Lack of crucial details (expiry dates, ingredients, warranty, dimensions) preventing a purchase decision.",
        "examples": [
            "No expiry date mentioned on the milk carton listing. Great job.",
            "Size nahi likha diaper ka, kaise order karoon?"
        ]
    },
    "price_perception": {
        "definition": "Belief that the platform is too expensive, has high delivery fees, or lacks good discounts compared to alternatives.",
        "examples": [
            "₹50 delivery charge for a ₹100 item? No thanks.",
            "Local shop gives better discount on MRP. Yeh log MRP pe bechte hain."
        ]
    },
    "assortment_gap": {
        "definition": "The desired brand, variant, or product size is out of stock or simply not carried by the platform.",
        "examples": [
            "Why is my dog's favorite pedigree always out of stock?",
            "Sirf chote packets milte hain surf excel ke, mujhe 5kg wala chahiye."
        ]
    },
    "none": {
        "definition": "Explicitly states no barrier, or is purely positive praise without mentioning a barrier.",
        "examples": [
            "Best app ever! 10 min delivery is magic.",
            "Bohot accha service hai, always on time."
        ]
    },
    "other_emergent": {
        "definition": "A clear barrier to purchase that does not fit into any of the above categories.",
        "examples": [
            "The delivery guy called me 5 times because he couldn't find the address.",
            "Customer care is unresponsive when items are missing."
        ]
    }
}

def get_taxonomy_prompt_text() -> str:
    """Formats the taxonomy into a string for LLM prompts."""
    lines = [
        f"--- BARRIER TAXONOMY (Version {TAXONOMY_VERSION}) ---",
        "You must classify the user's primary barrier(s) into one or more of the following exact keys:",
        ""
    ]
    for key, data in BARRIERS.items():
        lines.append(f"• {key}: {data['definition']}")
        lines.append("  Examples:")
        for ex in data['examples']:
            lines.append(f"    - \"{ex}\"")
        lines.append("")
    return "\n".join(lines)
