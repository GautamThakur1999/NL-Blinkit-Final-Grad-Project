"""
pipeline/collectors/orchestrator.py — Collection Orchestrator

Runs all available collectors in sequence, followed by the collection report.
"""

from __future__ import annotations

import logging

from pipeline.collectors import (
    app_store,
    curated,
    play_store,
    reddit,
    collection_report,
)
from pipeline.common import setup_logging

logger = logging.getLogger(__name__)


def run_all() -> None:
    setup_logging()
    logger.info("Starting complete collection phase...")

    try:
        play_store.collect()
    except Exception as exc:
        logger.error(f"Play Store collection failed: {exc}")

    try:
        app_store.collect()
    except Exception as exc:
        logger.error(f"App Store collection failed: {exc}")

    try:
        reddit.collect()
    except Exception as exc:
        logger.error(f"Reddit collection failed: {exc}")

    try:
        curated.collect()
    except Exception as exc:
        logger.error(f"Curated collection failed: {exc}")

    logger.info("All collections finished. Generating report...")
    collection_report.generate_report()


if __name__ == "__main__":
    run_all()
