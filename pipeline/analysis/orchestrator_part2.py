"""
pipeline/analysis/orchestrator_part2.py — Phase 3 (Part 2: Synthesis & Counter Evidence)

Runs T3.5 and T3.6.
Executes AFTER the human checkpoint (T3.4) has reviewed and potentially edited `data/analysis/themes.json`.
"""

from __future__ import annotations

import logging

from pipeline.analysis import insights, counter_evidence
from pipeline.common import setup_logging

logger = logging.getLogger(__name__)


def run_all() -> None:
    setup_logging()
    logger.info("Starting Phase 3 (Part 2: Synthesis & Counter Evidence)...")

    try:
        insights.process()
    except Exception as exc:
        logger.error(f"Insights Synthesis failed: {exc}")
        return

    try:
        counter_evidence.process()
    except Exception as exc:
        logger.error(f"Counter Evidence pass failed: {exc}")
        return
        
    logger.info("Part 2 Complete. Phase 3 Analysis finished.")


if __name__ == "__main__":
    run_all()
