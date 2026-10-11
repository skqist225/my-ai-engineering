"""Tests for rubric evaluator."""

import pytest
from pathlib import Path
from src.nodes.evaluate_rubric import evaluate_repo


def test_detects_missing_gitleaks_config(tmp_path):
    """A repo without .gitleaks.toml should flag S1 as FAIL."""
    (tmp_path / "Jenkinsfile").write_text("pipeline { agent any }")

    results = evaluate_repo(tmp_path, repo_name="test-repo")

    s1 = next((r for r in results if r["id"] == "S1"), None)
    assert s1 is not None
    assert s1["status"] == "FAIL"
    assert ".gitleaks.toml" in s1["evidence"]


def test_passes_gitleaks_config_present(tmp_path):
    """A repo with .gitleaks.toml should flag S1 as PASS."""
    (tmp_path / ".gitleaks.toml").write_text('[rules]\n  description = "test"')

    results = evaluate_repo(tmp_path, repo_name="test-repo")

    s1 = next((r for r in results if r["id"] == "S1"), None)
    assert s1 is not None
    assert s1["status"] == "PASS"


def test_detects_missing_timeout(tmp_path):
    """A Jenkinsfile without timeout should flag P3 as FAIL."""
    (tmp_path / "Jenkinsfile").write_text("""
pipeline {
    agent any
    stages {
        stage('Build') { steps { echo 'hi' } }
    }
}
""")

    results = evaluate_repo(tmp_path, repo_name="test-repo")

    p3 = next((r for r in results if r["id"] == "P3"), None)
    assert p3 is not None
    assert p3["status"] == "FAIL"


def test_passes_timeout_present(tmp_path):
    """A Jenkinsfile with timeout should flag P3 as PASS."""
    (tmp_path / "Jenkinsfile").write_text("""
pipeline {
    agent any
    options { timeout(time: 1, unit: 'HOURS') }
    stages {
        stage('Build') { steps { echo 'hi' } }
    }
}
""")

    results = evaluate_repo(tmp_path, repo_name="test-repo")

    p3 = next((r for r in results if r["id"] == "P3"), None)
    assert p3 is not None
    assert p3["status"] == "PASS"


def test_detects_missing_cleanws(tmp_path):
    """A Jenkinsfile without cleanWs should flag P5 as FAIL."""
    (tmp_path / "Jenkinsfile").write_text("pipeline { agent any }")

    results = evaluate_repo(tmp_path, repo_name="test-repo")

    p5 = next((r for r in results if r["id"] == "P5"), None)
    assert p5 is not None
    assert p5["status"] == "FAIL"


def test_detects_unpinned_dockerfile(tmp_path):
    """A Dockerfile with :latest should flag B5 as FAIL."""
    (tmp_path / "Dockerfile").write_text("FROM node:latest\nRUN echo hi")

    results = evaluate_repo(tmp_path, repo_name="test-repo")

    b5 = next((r for r in results if r["id"] == "B5"), None)
    assert b5 is not None
    assert b5["status"] == "FAIL"
    assert "latest" in b5["evidence"]


def test_passes_pinned_dockerfile(tmp_path):
    """A Dockerfile with pinned tag should not flag B5."""
    (tmp_path / "Dockerfile").write_text("FROM node:18.17.0-alpine\nRUN echo hi")

    results = evaluate_repo(tmp_path, repo_name="test-repo")

    b5_fails = [r for r in results if r["id"] == "B5" and r["status"] == "FAIL"]
    assert len(b5_fails) == 0


def test_detects_missing_resource_limits(tmp_path):
    """K8s deployment without resources should flag K3 as FAIL."""
    (tmp_path / "deployment.yaml").write_text("""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test
spec:
  template:
    spec:
      containers:
      - name: app
        image: nginx:1.25
""")

    results = evaluate_repo(tmp_path, repo_name="test-repo")

    k3 = next((r for r in results if r["id"] == "K3"), None)
    assert k3 is not None
    assert k3["status"] == "FAIL"


def test_detects_missing_health_probes(tmp_path):
    """K8s deployment without probes should flag K4 as FAIL."""
    (tmp_path / "deployment.yaml").write_text("""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test
spec:
  template:
    spec:
      containers:
      - name: app
        image: nginx:1.25
""")

    results = evaluate_repo(tmp_path, repo_name="test-repo")

    k4 = next((r for r in results if r["id"] == "K4"), None)
    assert k4 is not None
    assert k4["status"] == "FAIL"


def test_detects_kyverno_audit_mode(tmp_path):
    """Kyverno policy in Audit mode should flag K2 as WARN."""
    (tmp_path / "policy.yaml").write_text("""
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: test-policy
spec:
  validationFailureAction: Audit
  rules:
  - name: check
    validate:
      message: "test"
""")

    results = evaluate_repo(tmp_path, repo_name="test-repo")

    k2 = next((r for r in results if r["id"] == "K2"), None)
    assert k2 is not None
    assert k2["status"] == "WARN"
    assert "Audit" in k2["evidence"]
