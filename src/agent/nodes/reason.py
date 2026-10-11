"""Node 5: LLM Reasoning, Remediation Synthesis, and Grounding Verification."""

import os
import json
from src.agent.state import AgentState
from src.extraction.extractor import StructuredExtractor
from src.extraction.schemas import SecurityAuditReport, SecurityFinding, Severity, RemediationStep
from src.guardrails.grounding import filter_grounded_findings
from src.prompts.system import SYSTEM_REASON_PROMPT


def build_analysis_context(state: AgentState) -> str:
    """Format observed rubrics, RAG context, and code snippets into an analysis prompt."""
    rubric_results = state.get("rubric_results", {})
    retrieved_context = state.get("retrieved_context", [])
    file_contents = state.get("file_contents", {})

    context_parts = []

    # 1. Authoritative RAG Standards
    if retrieved_context:
        context_parts.append("### AUTHORITATIVE CIS & OWASP GUIDELINES (RETRIEVED VIA RAG):")
        for chunk in retrieved_context[:3]:
            context_parts.append(chunk["content"])
        context_parts.append("\n" + "="*50 + "\n")

    # 2. Baseline Check Failures
    context_parts.append("### OBSERVED REPOSITORY BASELINE CHECK RESULTS:")
    for repo, evals in rubric_results.items():
        failures = [e for e in evals if e.get("status") in ("FAIL", "WARN")]
        context_parts.append(f"Repository: {repo} (Issues: {len(failures)})")
        for f in failures:
            context_parts.append(f"  - [{f.get('status')}] {f.get('title')}: {f.get('evidence')} (Ref: {f.get('rule_reference')})")

    # 3. Source File Samples
    context_parts.append("\n" + "="*50 + "\n### OFFENDING SOURCE FILE SNIPPETS:")
    for path, content in list(file_contents.items())[:5]:
        sample = "\n".join(content.splitlines()[:25])
        context_parts.append(f"File: {path}\n```\n{sample}\n```")

    return "\n".join(context_parts)


def reason_node(state: AgentState) -> dict:
    """Run structured LLM reasoning to produce prioritized, grounded findings."""
    provider = state.get("provider", os.environ.get("LLM_PROVIDER", "gemini"))
    extractor = StructuredExtractor(provider=provider, max_retries=2)

    user_context = build_analysis_context(state)
    target_repo = state.get("scope", "all")

    try:
        report: SecurityAuditReport = extractor.extract(
            schema=SecurityAuditReport,
            system_prompt=SYSTEM_REASON_PROMPT,
            user_content=f"Please analyze these repository configurations and produce a SecurityAuditReport:\n{user_context}",
        )

        # Apply Layer 5 Outbound Grounding Guardrail
        file_contents = state.get("file_contents", {})
        grounded_findings, rejected_findings = filter_grounded_findings(report.findings, file_contents)

        # Check if human approval is required (CRITICAL findings gate)
        has_critical = any(f.severity == Severity.CRITICAL for f in grounded_findings)

        return {
            "findings": [f.model_dump() for f in grounded_findings],
            "remediation_summary": report.summary,
            "requires_human_approval": has_critical,
            "execution_metrics": {
                "grounded_findings_count": len(grounded_findings),
                "rejected_hallucinations_count": len(rejected_findings),
            }
        }

    except Exception as exc:
        # Graceful fallback: construct findings deterministically from rubric failures
        fallback_findings = []
        rubric_results = state.get("rubric_results", {})
        for repo, evals in rubric_results.items():
            for idx, e in enumerate(evals):
                if e.get("status") == "FAIL":
                    fallback_findings.append(
                        SecurityFinding(
                            finding_id=f"FALLBACK-{idx+1:03d}",
                            title=e.get("title", "Security Check Failed"),
                            severity=Severity.HIGH,
                            category="Baseline",
                            file_path=e.get("evidence", "").split(":")[0] or "configuration",
                            evidence=e.get("evidence", "Policy violation"),
                            cve_reference=e.get("rule_reference"),
                            remediation_steps=[
                                RemediationStep(
                                    step_number=1,
                                    action_title=f"Fix {e.get('title')}",
                                    code_diff_patch=None,
                                    verification_command="python -m learning.dry_run"
                                )
                            ]
                        ).model_dump()
                    )

        return {
            "findings": fallback_findings,
            "remediation_summary": f"Automated analysis completed with fallback due to API: {str(exc)}",
            "requires_human_approval": False,
            "execution_metrics": {"fallback_reasoning_used": True}
        }
