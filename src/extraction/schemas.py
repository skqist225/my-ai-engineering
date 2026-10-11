"""Layer 3: Production Pydantic v2 Domain Schemas."""

from enum import Enum
from pydantic import BaseModel, Field


class Severity(str, Enum):
    """Categorized severity level for DevSecOps findings."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"
    INFORMATIONAL = "INFORMATIONAL"



class RemediationStep(BaseModel):
    """Actionable, verified remediation procedure."""
    step_number: int = Field(ge=1, description="Sequential order of the step")
    action_title: str = Field(description="Short imperative command, e.g. 'Add USER appuser'")
    code_diff_patch: str | None = Field(default=None, description="Unified diff or exact code snippet")
    verification_command: str | None = Field(default=None, description="CLI command to verify the fix")


class SecurityFinding(BaseModel):
    """Individual security flaw or policy violation."""
    finding_id: str = Field(description="Unique identifier, e.g. SEC-001")
    title: str = Field(description="Concise description of the flaw")
    severity: Severity = Field(description="Severity rating")
    category: str = Field(description="Domain category: Dockerfile, Kubernetes, CI/CD, Secrets, Terraform")
    file_path: str = Field(description="Relative path to offending file")
    line_number: int | None = Field(default=None, ge=1, description="Line number if identifiable")
    evidence: str = Field(description="Exact offending line or snippet from the scanned repository")
    cve_reference: str | None = Field(default=None, description="Related CVE ID or CIS rule, if applicable")
    remediation_steps: list[RemediationStep] = Field(default_factory=list, description="Step-by-step fix guide")


class RubricEvaluation(BaseModel):
    """Evaluation result of a predefined security rubric."""
    rubric_id: str = Field(description="Rubric ID, e.g. SEC-DOCKER-ROOT")
    title: str = Field(description="Rubric title")
    status: str = Field(pattern=r"^(PASS|FAIL|WARN)$", description="Rubric compliance status: PASS, FAIL, or WARN")
    rule_reference: str = Field(description="Authoritative reference, e.g. CIS-DOCKER-4.1")
    evidence: str = Field(description="Observed evidence supporting the status")


class SecurityAuditReport(BaseModel):
    """Executive & technical audit report synthesized by the AI agent."""
    repository_name: str = Field(description="Name of the audited repository")
    scan_timestamp: str = Field(description="ISO-8601 timestamp of analysis")
    compliance_score: float = Field(ge=0.0, le=100.0, description="Overall security compliance score from 0.0 to 100.0")
    summary: str = Field(description="Executive summary of posture, critical risks, and priorities")
    rubric_evaluations: list[RubricEvaluation] = Field(default_factory=list, description="Evaluated baseline rubrics")
    findings: list[SecurityFinding] = Field(default_factory=list, description="Detailed actionable findings")
    immediate_actions: list[str] = Field(default_factory=list, description="Top 3 immediate actions for the engineering team")
