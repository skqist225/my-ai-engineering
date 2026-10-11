"""Tests for DefectDojo and SonarQube clients."""

import pytest
from unittest.mock import MagicMock, patch
from src.clients.defectdojo import DefectDojoClient
from src.clients.sonarqube import SonarQubeClient


class TestDefectDojoClient:

    def test_fetches_active_findings(self):
        """Should parse findings from DefectDojo API response."""
        client = DefectDojoClient(base_url="http://fake", api_token="fake-token")

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "count": 2,
            "next": None,
            "results": [
                {"id": 1, "title": "CVE-2024-1234", "severity": "High",
                 "file_path": "package.json", "line": 0, "active": True},
                {"id": 2, "title": "Hardcoded secret", "severity": "Critical",
                 "file_path": "config.py", "line": 42, "active": True},
            ]
        }
        mock_response.status_code = 200

        with patch("requests.get", return_value=mock_response):
            findings = client.get_active_findings(product_name="test-project")

        assert len(findings) == 2
        assert findings[0]["severity"] == "High"
        assert findings[1]["severity"] == "Critical"

    def test_paginates_results(self):
        """Should follow 'next' links for paginated results."""
        client = DefectDojoClient(base_url="http://fake", api_token="fake-token")

        page1 = MagicMock()
        page1.json.return_value = {
            "count": 2, "next": "http://fake/api/v2/findings/?offset=1",
            "results": [{"id": 1, "title": "Finding 1", "severity": "High"}]
        }
        page1.status_code = 200

        page2 = MagicMock()
        page2.json.return_value = {
            "count": 2, "next": None,
            "results": [{"id": 2, "title": "Finding 2", "severity": "Medium"}]
        }
        page2.status_code = 200

        with patch("requests.get", side_effect=[page1, page2]):
            findings = client.get_active_findings()

        assert len(findings) == 2


class TestSonarQubeClient:

    def test_fetches_issues(self):
        """Should parse issues from SonarQube API response."""
        client = SonarQubeClient(base_url="http://fake", token="fake-token")

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "total": 1,
            "issues": [
                {"key": "AX1", "rule": "java:S1234", "severity": "MAJOR",
                 "message": "Remove unused import", "component": "src:Main.java", "line": 5}
            ]
        }
        mock_response.status_code = 200

        with patch("requests.get", return_value=mock_response):
            issues = client.get_issues(project_key="test-project")

        assert len(issues) == 1
        assert issues[0]["severity"] == "MAJOR"
