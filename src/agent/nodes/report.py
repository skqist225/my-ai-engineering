"""Layer 4 Node: Markdown & Summary Report Generation."""

from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

from src.agent.state import AgentState


def generate_report_node(state: AgentState) -> dict:
    """Render structured findings and rubric baselines into Markdown & summary reports."""
    templates_dir = Path(__file__).resolve().parent.parent.parent / "templates"
    output_dir = Path(state.get("output_dir", "./reports"))
    output_dir.mkdir(parents=True, exist_ok=True)

    env = Environment(loader=FileSystemLoader(str(templates_dir)))
    template = env.get_template("report.md.j2")

    findings = state.get("findings", [])
    rubric_results = state.get("rubric_results", {})
    remediation_summary = state.get("remediation_summary", "Automated analysis complete.")
    human_approved = state.get("human_approved", True)
    scope = state.get("scope", "all")
    repos_dir = state.get("repos_dir", ".")

    # Calculate severity counts
    severity_counts = {
        "CRITICAL": 0,
        "HIGH": 0,
        "MEDIUM": 0,
        "LOW": 0,
        "INFORMATIONAL": 0,
    }
    for f in findings:
        sev = str(f.get("severity", "LOW")).upper()
        if sev in severity_counts:
            severity_counts[sev] += 1
        else:
            severity_counts["LOW"] += 1

    # Calculate rubric stats
    rubric_stats = {}
    for repo, results in rubric_results.items():
        rubric_stats[repo] = {
            "pass": sum(1 for r in results if r.get("status") == "PASS"),
            "fail": sum(1 for r in results if r.get("status") == "FAIL"),
            "warn": sum(1 for r in results if r.get("status") == "WARN"),
            "total": len(results),
        }

    rendered_markdown = template.render(
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        scope=scope,
        repos_dir=repos_dir,
        human_approved=human_approved,
        remediation_summary=remediation_summary,
        findings=findings,
        severity_counts=severity_counts,
        total_findings=len(findings),
        rubric_stats=rubric_stats,
        rubric_results=rubric_results,
    )

    report_filename = f"report-{datetime.now().strftime('%Y-%m-%d-%H%M%S')}.md"
    report_path = output_dir / report_filename
    report_path.write_text(rendered_markdown, encoding="utf-8")
    print(f"[report] [OK] Full audit report written to {report_path}")

    # Write summary for CI/CD, Slack, or GitHub Step Summary
    summary_path = output_dir / "summary.md"
    summary_lines = [
        "# DevSecOps AI Advisor - Executive Summary\n",
        f"- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- Scope: {scope}",
        f"- Critical: {severity_counts['CRITICAL']} | High: {severity_counts['HIGH']} | Medium: {severity_counts['MEDIUM']} | Low: {severity_counts['LOW']}",
        f"- Human Gate: {'[APPROVED]' if human_approved else '[PENDING]'}\n",
        "## Top Priority Findings\n",
    ]

    critical_and_high = [f for f in findings if str(f.get("severity", "")).upper() in ("CRITICAL", "HIGH")]
    if critical_and_high:
        for f in critical_and_high[:5]:
            summary_lines.append(f"- **[{f.get('severity')}]** `{f.get('file_path')}`: {f.get('title')}")
    else:
        summary_lines.append("- _No CRITICAL or HIGH risk findings discovered._")

    summary_path.write_text("\n".join(summary_lines), encoding="utf-8")
    print(f"[report] [OK] Step summary written to {summary_path}")

    return {"report_path": str(report_path)}
