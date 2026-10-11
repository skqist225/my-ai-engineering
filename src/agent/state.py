"""Layer 4: State Schema for LangGraph Agent Pipeline."""

from typing import TypedDict, Annotated, Any
import operator


class AgentState(TypedDict):
    """Unified state flowing through the DevSecOps LangGraph pipeline."""

    # 1. Pipeline Inputs
    repos_dir: str
    scope: str                     # "all" or specific repo name (e.g. "infra-kubernetes")
    output_dir: str
    provider: str                  # LLM provider (gemini, groq, ollama, claude)

    # 2. Ingested Repository Data
    repo_files: dict[str, list[str]]      # repo_name -> [relative_file_paths]
    file_contents: dict[str, str]        # relative_file_path -> content string

    # 3. Layer 2: RAG Retrieved Standards
    retrieved_context: list[dict[str, Any]]  # Authoritative CIS & OWASP chunks

    # 4. Tool Findings (SonarQube, DefectDojo)
    tool_findings: dict[str, list[dict[str, Any]]]

    # 5. Rubric Evaluations
    rubric_results: dict[str, list[dict[str, Any]]]

    # 6. Layer 3: Structured AI Findings & Remediation
    findings: Annotated[list[dict[str, Any]], operator.add]
    remediation_summary: str

    # 7. Layer 4: Human-in-the-Loop Gate
    requires_human_approval: bool
    human_approved: bool

    # 8. Layer 6: Observability & Output
    report_path: str | None
    execution_metrics: dict[str, Any]
