"""Report generator node — produces Markdown report from agent findings."""

from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader


def generate_report_node(state: dict) -> dict:
    """LangGraph node: Generate Markdown report from recommendations.

    Reads state['recommendations'] and state['rubric_results'].
    Writes state['report_path'] with path to generated report.
    """
    templates_dir = Path(__file__).parent.parent / "templates"
    output_dir = Path(state.get("output_dir", "./reports"))
    output_dir.mkdir(parents=True, exist_ok=True)

    env = Environment(loader=FileSystemLoader(str(templates_dir)))
    template = env.get_template("report.md.j2")

    # Build summary counts
    summary: dict[str, dict] = {}
    for repo_name, recs in state.get("recommendations", {}).items():
        for rec in recs:
            cat = rec.get("category", "other")
            if cat not in summary:
                summary[cat] = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0, "total": 0}
            risk = rec.get("risk", "Low")
            if risk in summary[cat]:
                summary[cat][risk] += 1
            summary[cat]["total"] += 1

    # Count rubric stats
    rubric_stats: dict[str, dict] = {}
    for repo_name, results in state.get("rubric_results", {}).items():
        rubric_stats[repo_name] = {
            "pass": sum(1 for r in results if r["status"] == "PASS"),
            "fail": sum(1 for r in results if r["status"] == "FAIL"),
            "warn": sum(1 for r in results if r["status"] == "WARN"),
            "total": len(results),
        }

    report = template.render(
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        scope=state.get("scope", "all"),
        repos=list(state.get("recommendations", {}).keys()),
        summary=summary,
        rubric_stats=rubric_stats,
        rubric_results=state.get("rubric_results", {}),
        recommendations=state.get("recommendations", {}),
    )

    report_filename = f"report-{datetime.now().strftime('%Y-%m-%d-%H%M')}.md"
    report_path = output_dir / report_filename
    report_path.write_text(report, encoding="utf-8")
    print(f"[report] Written to {report_path}")

    # Write summary for Teams/Slack notification
    summary_path = output_dir / "summary.md"
    top_findings = []
    for recs in state.get("recommendations", {}).values():
        top_findings.extend([r for r in recs if r.get("risk") in ("Critical", "High")])
    top_findings.sort(key=lambda r: 0 if r.get("risk") == "Critical" else 1)
    summary_text = "# DevSecOps AI Advisor — Top Findings\n\n"
    if top_findings:
        for r in top_findings[:10]:
            summary_text += f"- **{r.get('risk', '?')}** [{r.get('category', '?')}] {r.get('title', '?')}\n"
    else:
        summary_text += "_No critical or high-risk findings._\n"
    summary_path.write_text(summary_text, encoding="utf-8")

    state["report_path"] = str(report_path)
    return state
