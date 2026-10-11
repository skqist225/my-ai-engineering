"""Layer 5: Outbound Citation and Grounding Verification Guardrail."""

import logging
from typing import Any

from src.extraction.schemas import SecurityFinding

logger = logging.getLogger(__name__)


class GroundingViolationError(ValueError):
    """Raised when an LLM finding cites non-existent files or fabricated evidence."""
    pass


def verify_finding_grounding(
    finding: SecurityFinding,
    scanned_files: dict[str, str],
    raise_exception: bool = False,
) -> bool:
    """Verify that a generated finding is strictly grounded in actual scanned source files.

    Checks:
        1. file_path exists in scanned repository files.
        2. evidence snippet appears within the file content.

    Returns:
        True if grounded, False if hallucinated/ungrounded.
    """
    if finding.file_path not in scanned_files:
        msg = f"[GROUNDING VIOLATION] Finding {finding.finding_id} references non-existent file: {finding.file_path}"
        logger.warning(msg)
        if raise_exception:
            raise GroundingViolationError(msg)
        return False

    actual_content = scanned_files[finding.file_path]
    clean_evidence = finding.evidence.strip()

    # Check if exact snippet or first line of evidence appears in file
    first_evidence_line = clean_evidence.splitlines()[0].strip() if clean_evidence else ""
    if clean_evidence not in actual_content and first_evidence_line not in actual_content:
        msg = f"[GROUNDING VIOLATION] Finding {finding.finding_id} cites evidence not found in {finding.file_path}: '{first_evidence_line}'"
        logger.warning(msg)
        if raise_exception:
            raise GroundingViolationError(msg)
        return False

    return True


def filter_grounded_findings(
    findings: list[SecurityFinding],
    scanned_files: dict[str, str],
) -> tuple[list[SecurityFinding], list[SecurityFinding]]:
    """Partition findings into verified grounded findings and rejected hallucinated findings."""
    grounded = []
    rejected = []

    for f in findings:
        if verify_finding_grounding(f, scanned_files):
            grounded.append(f)
        else:
            rejected.append(f)

    return grounded, rejected
