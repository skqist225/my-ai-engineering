"""DefectDojo API client for ingesting existing security findings."""

import requests


class DefectDojoClient:
    """Read-only client for DefectDojo v2 API.

    Fetches active findings to correlate with AI advisor analysis,
    preventing duplicate recommendations.
    """

    def __init__(self, base_url: str, api_token: str):
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Authorization": f"Token {api_token}",
            "Accept": "application/json",
        }

    def get_active_findings(
        self,
        product_name: str | None = None,
        severity: str | None = None,
        limit: int = 100,
    ) -> list[dict]:
        """Fetch active findings, optionally filtered by product and severity.

        Args:
            product_name: DefectDojo product name (maps to Jenkins PROJECT_NAME).
            severity: Filter by severity (e.g. "Critical", "High").
            limit: Max results per page.

        Returns:
            List of finding dicts from DefectDojo API.
        """
        params: dict = {"active": "true", "limit": limit}
        if product_name:
            params["test__engagement__product__name"] = product_name
        if severity:
            params["severity"] = severity

        findings = []
        url: str | None = f"{self.base_url}/api/v2/findings/"

        while url:
            resp = requests.get(
                url, headers=self.headers, params=params, timeout=30
            )
            resp.raise_for_status()
            data = resp.json()
            findings.extend(data.get("results", []))
            url = data.get("next")
            params = {}  # next URL already includes params

        return findings

    def get_products(self) -> list[dict]:
        """List all products in DefectDojo."""
        resp = requests.get(
            f"{self.base_url}/api/v2/products/",
            headers=self.headers,
            params={"limit": 200},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json().get("results", [])
