"""Rubric evaluator node — deterministic checks against DevSecOps best practices.

Each check is a pure Python function that inspects file contents,
directory structure, or config patterns. No LLM needed here.
"""

import re
from pathlib import Path

# Directories to skip (same as ingest_repos.IGNORE_DIRS)
_IGNORE_DIRS = {
    ".git", "node_modules", "bin", "obj", ".gradle", "build",
    "__pycache__", ".venv", "dist", ".scannerwork", "packages",
    ".agent", ".antigravitycli", "logs", "output", "tmp",
}


def _safe_rglob(repo_path: Path, pattern: str) -> list[Path]:
    """Recursively glob while skipping ignored directories and handling errors.

    Filters out paths containing any directory from _IGNORE_DIRS
    and silently skips files that raise PermissionError.
    """
    results = []
    try:
        for p in repo_path.rglob(pattern):
            if any(part in _IGNORE_DIRS for part in p.parts):
                continue
            results.append(p)
    except PermissionError:
        pass
    return results


def _safe_read_text(path: Path) -> str | None:
    """Read file text, returning None on permission or encoding errors."""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except (PermissionError, OSError):
        return None


def evaluate_repo(repo_path: Path, repo_name: str) -> list[dict]:
    """Run all rubric checks against a single repo.

    Returns list of result dicts with keys:
    id, category, title, status, evidence, file_path, line, existing_tool
    """
    results: list[dict] = []

    results.extend(_check_security(repo_path, repo_name))
    results.extend(_check_pipeline(repo_path, repo_name))
    results.extend(_check_sbom(repo_path, repo_name))
    results.extend(_check_kubernetes(repo_path, repo_name))
    results.extend(_check_quality(repo_path, repo_name))

    return results


def _check_security(repo_path: Path, repo_name: str) -> list[dict]:
    """Security-related rubric checks (S1-S9)."""
    results = []

    # S1: Gitleaks config present
    gitleaks_files = _safe_rglob(repo_path, ".gitleaks.toml")
    results.append({
        "id": "S1", "category": "security",
        "title": "Gitleaks configured with custom .gitleaks.toml",
        "status": "PASS" if gitleaks_files else "FAIL",
        "evidence": f"Found: {gitleaks_files[0].relative_to(repo_path)}" if gitleaks_files
                    else "No .gitleaks.toml found in repo",
        "existing_tool": "gitleaks",
    })

    # S2: Semgrep ignore not overly broad
    semgrepignore = _safe_rglob(repo_path, ".semgrepignore")
    if semgrepignore:
        content = _safe_read_text(semgrepignore[0]) or ""
        line_count = len([l for l in content.strip().split("\n") if l.strip() and not l.startswith("#")])
        status = "WARN" if line_count > 20 else "PASS"
        results.append({
            "id": "S2", "category": "security",
            "title": "Semgrep ignore file not overly broad",
            "status": status,
            "evidence": f".semgrepignore has {line_count} active rules" + (" — review for over-exclusion" if status == "WARN" else ""),
            "file_path": str(semgrepignore[0].relative_to(repo_path)),
            "existing_tool": "semgrep",
        })

    # S6: Secrets in Jenkinsfile environment blocks
    for jf in _find_jenkinsfiles(repo_path):
        content = _safe_read_text(jf)
        if content is None:
            continue
        env_blocks = re.findall(r"environment\s*\{([^}]+)\}", content, re.DOTALL)
        for block in env_blocks:
            for line_num, line in enumerate(block.strip().split("\n"), 1):
                line_stripped = line.strip()
                if "=" in line_stripped and "credentials(" not in line_stripped:
                    if re.search(r"(?i)(key|token|password|secret|api_key|apikey)", line_stripped):
                        results.append({
                            "id": "S6", "category": "security",
                            "title": "Potential secret in environment block without credentials()",
                            "status": "WARN",
                            "evidence": f"Suspicious env var: {line_stripped[:80]}",
                            "file_path": str(jf.relative_to(repo_path)),
                            "existing_tool": "",
                        })

    # S8: Security context in K8s deployments
    for yml in _safe_rglob(repo_path, "*.yaml"):
        content = _safe_read_text(yml)
        if content is None:
            continue
        if "kind: Deployment" in content or "kind: StatefulSet" in content:
            has_security_ctx = "securityContext:" in content
            has_run_as_non_root = "runAsNonRoot:" in content
            if not has_security_ctx or not has_run_as_non_root:
                results.append({
                    "id": "S8", "category": "security",
                    "title": f"Security context incomplete ({yml.name})",
                    "status": "FAIL",
                    "evidence": f"securityContext={'yes' if has_security_ctx else 'NO'}, "
                               f"runAsNonRoot={'yes' if has_run_as_non_root else 'NO'}",
                    "file_path": str(yml.relative_to(repo_path)),
                    "existing_tool": "",
                })

    # S9: Network policies
    yaml_files = _safe_rglob(repo_path, "*.yaml")
    if yaml_files:
        has_netpol = any(
            "kind: NetworkPolicy" in (_safe_read_text(f) or "")
            for f in yaml_files
            if f.is_file() and f.stat().st_size < 100_000
        )
        if not has_netpol and _is_k8s_repo(repo_path):
            results.append({
                "id": "S9", "category": "security",
                "title": "No NetworkPolicy resources defined",
                "status": "FAIL",
                "evidence": "No YAML file with 'kind: NetworkPolicy' found",
                "existing_tool": "",
            })

    return results


def _check_pipeline(repo_path: Path, repo_name: str) -> list[dict]:
    """CI/CD pipeline hygiene checks (P1-P8)."""
    results = []

    jenkinsfiles = _find_jenkinsfiles(repo_path)

    for jf in jenkinsfiles:
        content = _safe_read_text(jf)
        if content is None:
            continue
        rel_path = str(jf.relative_to(repo_path))

        # P3: Timeout configured
        results.append({
            "id": "P3", "category": "pipeline",
            "title": f"Pipeline timeout configured ({jf.name})",
            "status": "PASS" if "timeout(" in content else "FAIL",
            "evidence": "timeout() option found" if "timeout(" in content
                        else "No timeout() — stuck builds risk",
            "file_path": rel_path,
            "existing_tool": "",
        })

        # P4: Build discarder
        results.append({
            "id": "P4", "category": "pipeline",
            "title": f"Build discarder configured ({jf.name})",
            "status": "PASS" if "buildDiscarder" in content else "FAIL",
            "evidence": "buildDiscarder found" if "buildDiscarder" in content
                        else "No buildDiscarder — Jenkins accumulates builds forever",
            "file_path": rel_path,
            "existing_tool": "",
        })

        # P5: Workspace cleanup
        results.append({
            "id": "P5", "category": "pipeline",
            "title": f"Workspace cleanup in post ({jf.name})",
            "status": "PASS" if "cleanWs()" in content else "FAIL",
            "evidence": "cleanWs() found in post" if "cleanWs()" in content
                        else "No cleanWs() — workspace disk leak",
            "file_path": rel_path,
            "existing_tool": "",
        })

        # P6: Scan stage present
        has_scan = "scan(" in content or "scan " in content
        results.append({
            "id": "P6", "category": "pipeline",
            "title": f"Security scan stage present ({jf.name})",
            "status": "PASS" if has_scan else "WARN",
            "evidence": "scan() invocation found" if has_scan
                        else "No scan() call found — may rely on downstream scan pipeline",
            "file_path": rel_path,
            "existing_tool": "",
        })

        # P8: Credential usage pattern
        cred_matches = re.findall(r"credentials\(['\"]([^'\"]+)['\"]\)", content)
        env_without_cred = []
        for match in re.finditer(r"(\w+)\s*=\s*['\"]([^'\"]{8,})['\"]", content):
            var_name = match.group(1)
            if re.search(r"(?i)(key|token|password|secret)", var_name):
                env_without_cred.append(var_name)
        if env_without_cred:
            results.append({
                "id": "P8", "category": "pipeline",
                "title": f"Hardcoded credential-like values ({jf.name})",
                "status": "WARN",
                "evidence": f"Suspicious vars: {', '.join(env_without_cred[:5])}",
                "file_path": rel_path,
                "existing_tool": "",
            })

    return results


def _check_sbom(repo_path: Path, repo_name: str) -> list[dict]:
    """Supply chain / SBOM checks (B1-B6)."""
    results = []

    # B5: Pinned Dockerfile base images
    dockerfiles = _safe_rglob(repo_path, "Dockerfile") + _safe_rglob(repo_path, "Dockerfile.*")
    for df in dockerfiles:
        content = _safe_read_text(df)
        if content is None:
            continue
        for line_num, line in enumerate(content.split("\n"), 1):
            stripped = line.strip()
            if stripped.startswith("FROM ") and not stripped.startswith("FROM scratch"):
                parts = stripped.split()
                if len(parts) >= 2:
                    image_ref = parts[1]
                    tag_part = image_ref.split("/")[-1]
                    if ":latest" in image_ref or ":" not in tag_part:
                        results.append({
                            "id": "B5", "category": "sbom",
                            "title": f"Unpinned base image ({df.name})",
                            "status": "FAIL",
                            "evidence": f"Line {line_num}: {stripped} — use pinned tag or digest",
                            "file_path": str(df.relative_to(repo_path)),
                            "line": line_num,
                            "existing_tool": "",
                        })

    # B4: Pre-commit hooks configured
    has_precommit = (repo_path / ".pre-commit-config.yaml").exists()
    results.append({
        "id": "B4", "category": "sbom",
        "title": "Pre-commit hooks configured",
        "status": "PASS" if has_precommit else "WARN",
        "evidence": ".pre-commit-config.yaml found" if has_precommit
                    else "No pre-commit config — consider adding for local checks",
        "existing_tool": "",
    })

    return results


def _check_kubernetes(repo_path: Path, repo_name: str) -> list[dict]:
    """Kubernetes / IaC readiness checks (K1-K10)."""
    results = []

    # Kyverno policy checks run for ANY repo (policies can be in non-K8s repos)
    for yml in _safe_rglob(repo_path, "*.yaml"):
        content = _safe_read_text(yml)
        if content is None:
            continue
        rel_path = str(yml.relative_to(repo_path))

        # K2: Kyverno enforcement mode
        if "kind: ClusterPolicy" in content or "kind: Policy" in content:
            if "validationFailureAction: Audit" in content:
                results.append({
                    "id": "K2", "category": "kubernetes",
                    "title": f"Kyverno policy in Audit mode ({yml.name})",
                    "status": "WARN",
                    "evidence": "validationFailureAction: Audit — violations are logged but not blocked. "
                               "Consider promoting to Enforce.",
                    "file_path": rel_path,
                    "existing_tool": "",
                })

    if not _is_k8s_repo(repo_path):
        return results

    for yml in _safe_rglob(repo_path, "*.yaml"):
        content = _safe_read_text(yml)
        if content is None:
            continue

        rel_path = str(yml.relative_to(repo_path))

        if "kind: Deployment" in content or "kind: StatefulSet" in content:
            # K3: Resource limits
            has_resources = "resources:" in content and ("limits:" in content or "requests:" in content)
            results.append({
                "id": "K3", "category": "kubernetes",
                "title": f"Resource limits defined ({yml.name})",
                "status": "PASS" if has_resources else "FAIL",
                "evidence": "resources block found" if has_resources
                            else "No resources.limits/requests — OOM risk",
                "file_path": rel_path,
                "existing_tool": "",
            })

            # K4: Health probes
            has_liveness = "livenessProbe:" in content
            has_readiness = "readinessProbe:" in content
            if not has_liveness or not has_readiness:
                results.append({
                    "id": "K4", "category": "kubernetes",
                    "title": f"Health probes missing ({yml.name})",
                    "status": "FAIL",
                    "evidence": f"liveness={'yes' if has_liveness else 'NO'}, "
                               f"readiness={'yes' if has_readiness else 'NO'}",
                    "file_path": rel_path,
                    "existing_tool": "",
                })

            # K9: Image pull policy and registry
            if "imagePullPolicy:" not in content:
                results.append({
                    "id": "K9", "category": "kubernetes",
                    "title": f"imagePullPolicy not set ({yml.name})",
                    "status": "WARN",
                    "evidence": "No explicit imagePullPolicy — defaults vary by tag",
                    "file_path": rel_path,
                    "existing_tool": "",
                })

        # K8: Ingress TLS
        if "kind: Ingress" in content:
            has_tls = "tls:" in content
            results.append({
                "id": "K8", "category": "kubernetes",
                "title": f"Ingress TLS configured ({yml.name})",
                "status": "PASS" if has_tls else "FAIL",
                "evidence": "TLS block found" if has_tls else "No TLS — traffic in cleartext",
                "file_path": rel_path,
                "existing_tool": "",
            })

    return results


def _check_quality(repo_path: Path, repo_name: str) -> list[dict]:
    """Code quality checks (Q1-Q6)."""
    results = []

    # Q4: Pre-commit consistency (checked in _check_sbom as B4)
    # Q1: SonarQube config present
    sonar_props = _safe_rglob(repo_path, "sonar-project.properties")
    if sonar_props:
        results.append({
            "id": "Q1", "category": "quality",
            "title": "SonarQube project properties configured",
            "status": "PASS",
            "evidence": f"Found: {sonar_props[0].relative_to(repo_path)}",
            "existing_tool": "sonarqube",
        })

    return results


def _find_jenkinsfiles(repo_path: Path) -> list[Path]:
    """Find all Jenkinsfile variants in a repo."""
    files = []
    for pattern in ["Jenkinsfile", "Jenkinsfile-*", "Jenkinsfile.*"]:
        files.extend(_safe_rglob(repo_path, pattern))
    return sorted(set(files))


def _is_k8s_repo(repo_path: Path) -> bool:
    """Heuristic: does this repo contain Kubernetes manifests?"""
    indicators = ["kustomization.yaml", "Chart.yaml", "helmfile.yaml"]
    for indicator in indicators:
        if _safe_rglob(repo_path, indicator):
            return True
    # Check for any YAML with 'kind: Deployment'
    for yml in _safe_rglob(repo_path, "*.yaml"):
        content = _safe_read_text(yml)
        if content and ("kind: Deployment" in content or "kind: Service" in content):
            return True
    return False


def evaluate_rubric_node(state: dict) -> dict:
    """LangGraph node: Run deterministic rubric checks on all repos.

    Reads state['repos_dir'] and state['repo_files'].
    Writes state['rubric_results'] with {repo_name: [result_dicts]}.
    """
    repos_dir = Path(state["repos_dir"])
    rubric_results: dict[str, list[dict]] = {}

    for repo_name in state.get("repo_files", {}):
        repo_path = repos_dir / repo_name
        if repo_path.exists():
            results = evaluate_repo(repo_path, repo_name)
            rubric_results[repo_name] = results
            passed = sum(1 for r in results if r["status"] == "PASS")
            failed = sum(1 for r in results if r["status"] == "FAIL")
            warned = sum(1 for r in results if r["status"] == "WARN")
            print(f"[evaluate_rubric] {repo_name}: {passed} PASS, {failed} FAIL, {warned} WARN")

    state["rubric_results"] = rubric_results
    return state
