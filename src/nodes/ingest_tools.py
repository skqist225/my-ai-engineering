"""Tool findings ingestion node — fetches from DefectDojo and SonarQube."""

import os

from src.clients.defectdojo import DefectDojoClient
from src.clients.sonarqube import SonarQubeClient


def ingest_tools_node(state: dict) -> dict:
    """LangGraph node: Fetch existing findings from DevSecOps tools.

    Attempts to connect to DefectDojo and SonarQube APIs.
    Gracefully skips if credentials are not configured or APIs unreachable.

    Writes state['tool_findings'] with {repo_name: [finding_dicts]}.
    """
    tool_findings: dict[str, list[dict]] = {}

    dd_url = os.getenv("DEFECTDOJO_URL", "")
    dd_token = os.getenv("DEFECTDOJO_TOKEN", "")
    sq_url = os.getenv("SONARQUBE_URL", "")
    sq_token = os.getenv("SONARQUBE_TOKEN", "")

    for repo_name in state.get("repo_files", {}):
        findings: list[dict] = []

        # DefectDojo findings
        if dd_url and dd_token and dd_token != "your-token-here":
            try:
                dd = DefectDojoClient(dd_url, dd_token)
                dd_findings = dd.get_active_findings(product_name=repo_name)
                for f in dd_findings:
                    findings.append({
                        "source": "defectdojo",
                        "title": f.get("title", ""),
                        "severity": f.get("severity", "Info"),
                        "file_path": f.get("file_path", ""),
                        "line": f.get("line", 0),
                        "description": f.get("description", "")[:500],
                        "scanner": f.get("found_by", ["unknown"])[0] if f.get("found_by") else "unknown",
                    })
                print(f"[ingest_tools] {repo_name}: {len(dd_findings)} DefectDojo findings")
            except Exception as e:
                print(f"[ingest_tools] DefectDojo unavailable for {repo_name}: {e}")
        else:
            print(f"[ingest_tools] DefectDojo not configured, skipping")

        # SonarQube findings
        if sq_url and sq_token and sq_token != "your-token-here":
            try:
                sq = SonarQubeClient(sq_url, sq_token)
                sq_issues = sq.get_issues(project_key=repo_name)
                for issue in sq_issues:
                    findings.append({
                        "source": "sonarqube",
                        "title": issue.get("message", ""),
                        "severity": issue.get("severity", "INFO"),
                        "file_path": issue.get("component", "").split(":")[-1],
                        "line": issue.get("line", 0),
                        "description": issue.get("message", ""),
                        "scanner": "sonarqube",
                        "rule": issue.get("rule", ""),
                    })
                print(f"[ingest_tools] {repo_name}: {len(sq_issues)} SonarQube issues")
            except Exception as e:
                print(f"[ingest_tools] SonarQube unavailable for {repo_name}: {e}")
        else:
            print(f"[ingest_tools] SonarQube not configured, skipping")

        tool_findings[repo_name] = findings

    state["tool_findings"] = tool_findings
    return state
