"""SonarQube API client for ingesting code quality findings."""

import requests


class SonarQubeClient:
    """Read-only client for SonarQube Web API.

    Fetches issues and quality gate status to correlate with
    AI advisor analysis.
    """

    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip("/")
        self.auth = (token, "")  # SonarQube uses token as username, empty password

    def get_issues(
        self,
        project_key: str,
        severities: str = "CRITICAL,MAJOR",
        statuses: str = "OPEN,CONFIRMED",
        page_size: int = 100,
    ) -> list[dict]:
        """Fetch issues for a SonarQube project.

        Args:
            project_key: SonarQube project key.
            severities: Comma-separated severity filter.
            statuses: Comma-separated status filter.
            page_size: Results per page.

        Returns:
            List of issue dicts from SonarQube API.
        """
        issues = []
        page = 1
        while True:
            resp = requests.get(
                f"{self.base_url}/api/issues/search",
                auth=self.auth,
                params={
                    "componentKeys": project_key,
                    "severities": severities,
                    "statuses": statuses,
                    "ps": page_size,
                    "p": page,
                },
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            issues.extend(data.get("issues", []))
            if len(issues) >= data.get("total", 0):
                break
            page += 1
        return issues

    def get_quality_gate_status(self, project_key: str) -> dict:
        """Get quality gate status for a project.

        Returns:
            Dict with 'status' key ('OK', 'WARN', 'ERROR').
        """
        resp = requests.get(
            f"{self.base_url}/api/qualitygates/project_status",
            auth=self.auth,
            params={"projectKey": project_key},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json().get("projectStatus", {})
