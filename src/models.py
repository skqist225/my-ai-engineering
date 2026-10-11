"""Shared data models for the AI advisor agent."""

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class Finding:
    """Unified finding from any scanner or the AI advisor itself.

    Mirrors the schema in jenkinssetup/devsecops/generate-report.py
    for compatibility with existing DevSecOps reporting.
    """

    scanner: str = ""
    category: str = ""  # SAST, SCA, Secrets, License, Container, DAST, SBOM, Quality
    severity: str = "Info"  # Critical, High, Medium, Low, Info
    title: str = ""
    description: str = ""
    file_path: str = ""
    line: int = 0
    package: str = ""
    fixed_version: str = ""
    rule_id: str = ""
    metadata: dict = field(default_factory=dict)


@dataclass
class RubricResult:
    """Result of a single rubric check against a repo."""

    id: str
    category: str  # security, quality, pipeline, sbom, kubernetes
    title: str
    status: Literal["PASS", "FAIL", "WARN", "SKIP"]
    evidence: str
    file_path: str = ""
    line: int = 0
    existing_tool: str = ""


@dataclass
class Recommendation:
    """AI-generated recommendation."""

    id: str
    title: str
    category: str  # security, quality, pipeline, sbom, kubernetes
    risk: str  # Critical, High, Medium, Low
    effort: str  # XS, S, M, L, XL
    file_path: str = ""
    line: int = 0
    recommendation: str = ""
    existing_tool_covers: bool = False
    confidence: float = 0.0
