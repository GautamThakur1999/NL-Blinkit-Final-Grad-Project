"""
pipeline/analysis/orchestrator_part1.py — Phase 3 (Part 1: Tagging & Theming)

Runs T3.2 and T3.3.
After this completes, the human checkpoint (T3.4) occurs to review `data/analysis/themes.json`.
"""

from __future__ import annotations

import logging

from pipeline.analysis import tagger, themer
from pipeline.common import setup_logging

logger = logging.getLogger(__name__)


def run_all() -> None:
    setup_logging()
    logger.info("Starting Phase 3 (Part 1: Tagging & Theming)...")

    try:
        tagger.process()
    except Exception as exc:
        logger.error(f"Structured Tagging failed: {exc}")
        return

    try:
        themer.process()
    except Exception as exc:
        logger.error(f"Cross-source clustering (Theming) failed: {exc}")
        return
        
    logger.info("Part 1 Complete. Please review `data/analysis/themes.json` (Human Checkpoint T3.4).")


if __name__ == "__main__":
    run_all()
