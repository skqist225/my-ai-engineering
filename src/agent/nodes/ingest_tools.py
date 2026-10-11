"""Node 2: Ingest External DevSecOps Tool Findings (SonarQube, DefectDojo)."""

from src.agent.state import AgentState
from src.clients.sonarqube import SonarQubeClient
from src.clients.defectdojo import DefectDojoClient


def ingest_tools_node(state: AgentState) -> dict:
    """Ingest findings from external SAST and vulnerability management platforms."""
    repo_files = state.get("repo_files", {})
    tool_findings: dict[str, list[dict]] = {}

    sonar_client = SonarQubeClient()
    dojo_client = DefectDojoClient()

    for repo_name in repo_files:
        findings = []

        # 1. Fetch from SonarQube
        if sonar_client.is_configured():
            sonar_issues = sonar_client.get_issues_for_project(repo_name)
            findings.extend(sonar_issues)

        # 2. Fetch from DefectDojo
        if dojo_client.is_configured():
            dojo_findings = dojo_client.get_findings_for_engagement(repo_name)
            findings.extend(dojo_findings)

        tool_findings[repo_name] = findings

    return {"tool_findings": tool_findings}
