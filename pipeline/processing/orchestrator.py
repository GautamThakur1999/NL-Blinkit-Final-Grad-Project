"""
pipeline/processing/orchestrator.py — Phase 2 Orchestrator

Runs all Stage 2 (Normalize & Filter) processing steps in sequence.
"""

from __future__ import annotations

import logging

from pipeline.processing import (
    clean,
    dedupe,
    language,
    pii_redact,
    burst_detect,
    relevance,
    audit,
    composition_report,
)
from pipeline.common import setup_logging

logger = logging.getLogger(__name__)


def run_all() -> None:
    setup_logging()
    logger.info("Starting Phase 2 Processing pipeline...")

    try:
        clean.process()
    except Exception as exc:
        logger.error(f"Cleaning failed: {exc}")
        return

    try:
        dedupe.process()
    except Exception as exc:
        logger.error(f"Deduplication failed: {exc}")
        return

    try:
        language.process()
    except Exception as exc:
        logger.error(f"Language filtering failed: {exc}")
        return

    try:
        pii_redact.process()
    except Exception as exc:
        logger.error(f"PII Redaction failed: {exc}")
        return

    try:
        burst_detect.process()
    except Exception as exc:
        logger.error(f"Burst detection failed: {exc}")
        return

    try:
        relevance.process()
    except Exception as exc:
        logger.error(f"Relevance filtering failed: {exc}")
        return

    try:
        audit.process()
    except Exception as exc:
        logger.error(f"Rejection audit failed: {exc}")

    try:
        composition_report.generate_report()
    except Exception as exc:
        logger.error(f"Composition report generation failed: {exc}")


if __name__ == "__main__":
    run_all()
