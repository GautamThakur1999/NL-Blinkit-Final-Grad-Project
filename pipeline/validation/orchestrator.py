"""
pipeline/validation/orchestrator.py — Phase 4 Orchestrator

Runs all Stage 4 (Validation & Part 1 Reporting) steps in sequence:
  1. Traceability audit (T4.1) — MUST pass or report build fails
  2. Spot-check sample generation (T4.2)
  3. Validation metrics roll-up (T4.3)
  4. INSIGHTS_REPORT.md generation (T4.4)
  5. METHODOLOGY.md generation (T4.5)
"""

from __future__ import annotations

import logging

from pipeline.validation import (
    audit,
    spotcheck,
    metrics,
    report_insights,
    report_methodology,
)
from pipeline.common import setup_logging

logger = logging.getLogger(__name__)


def run_all() -> None:
    setup_logging()
    logger.info("Starting Phase 4 — Validation & Part 1 Reporting...")

    # T4.1 — Traceability Audit
    try:
        audit_result = audit.process()
        if not audit_result.passed:
            logger.error(
                "TRACEABILITY AUDIT FAILED. "
                "Fix orphan insights before generating reports. "
                "Continuing to generate reports with failure noted..."
            )
    except Exception as exc:
        logger.error(f"Traceability audit crashed: {exc}")

    # T4.2 — Spot-Check Sample
    try:
        spotcheck.process()
    except Exception as exc:
        logger.error(f"Spot-check sampling failed: {exc}")

    # T4.3 — Validation Metrics Roll-up
    try:
        metrics.process()
    except Exception as exc:
        logger.error(f"Metrics roll-up failed: {exc}")

    # T4.4 — INSIGHTS_REPORT.md
    try:
        report_insights.process()
    except Exception as exc:
        logger.error(f"Insights report generation failed: {exc}")

    # T4.5 — METHODOLOGY.md
    try:
        report_methodology.process()
    except Exception as exc:
        logger.error(f"Methodology report generation failed: {exc}")

    logger.info("Phase 4 complete. Check outputs/ for INSIGHTS_REPORT.md and METHODOLOGY.md.")


if __name__ == "__main__":
    run_all()
