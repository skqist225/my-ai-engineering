"""Unit tests for Layer 3: Structured Outputs & Self-Healing Extraction."""

import pytest
from unittest.mock import MagicMock, patch
from pydantic import ValidationError
from src.extraction.schemas import (
    Severity,
    RemediationStep,
    SecurityFinding,
    RubricEvaluation,
    SecurityAuditReport,
)
from src.extraction.extractor import StructuredExtractor


def test_schema_valid_instantiation():
    step = RemediationStep(
        step_number=1,
        action_title="Add non-root user",
        code_diff_patch="+ USER appuser:appgroup",
        verification_command="docker run --rm image whoami"
    )

    finding = SecurityFinding(
        finding_id="SEC-001",
        title="Root container execution",
        severity=Severity.HIGH,
        category="Dockerfile",
        file_path="Dockerfile",
        line_number=10,
        evidence="FROM python:3.11",
        cve_reference="CIS-DOCKER-4.1",
        remediation_steps=[step]
    )

    report = SecurityAuditReport(
        repository_name="infra-kubernetes",
        scan_timestamp="2026-10-11T12:00:00Z",
        compliance_score=85.5,
        summary="Audit completed with 1 HIGH risk finding.",
        rubric_evaluations=[],
        findings=[finding],
        immediate_actions=["Apply non-root user patch"]
    )

    dumped = report.model_dump()
    assert dumped["compliance_score"] == 85.5
    assert len(dumped["findings"]) == 1
    assert dumped["findings"][0]["severity"] == "HIGH"


def test_schema_invalid_compliance_score():
    with pytest.raises(ValidationError):
        SecurityAuditReport(
            repository_name="infra-kubernetes",
            scan_timestamp="2026-10-11T12:00:00Z",
            compliance_score=150.0,  # Invalid: must be <= 100.0
            summary="Invalid score test",
            rubric_evaluations=[],
            findings=[],
            immediate_actions=[]
        )


def test_extractor_self_healing_retry():
    extractor = StructuredExtractor(provider="gemini", max_retries=2)

    broken_json = '{"repository_name": "test", "compliance_score": 90.0, broken...'
    valid_json = (
        '{"repository_name": "test", "scan_timestamp": "2026-10-11T12:00:00Z", '
        '"compliance_score": 90.0, "summary": "Clean", "rubric_evaluations": [], '
        '"findings": [], "immediate_actions": []}'
    )

    mock_llm = MagicMock()
    mock_llm.invoke.side_effect = [
        MagicMock(content=broken_json),
        MagicMock(content=valid_json),
    ]

    with patch.object(extractor.router, "get_llm", return_value=mock_llm):
        report = extractor.extract(
            schema=SecurityAuditReport,
            system_prompt="Extract JSON",
            user_content="Test data"
        )
        assert report.repository_name == "test"
        assert report.compliance_score == 90.0
        assert mock_llm.invoke.call_count == 2
