"""Layer 4: MCP Tools for DevSecOps Intelligence."""

import os
import re
from pathlib import Path
from typing import Any
from src.guardrails.privacy import scrub_sensitive_tokens
from src.rag.store import KnowledgeStore
from src.rag.retriever import HybridRetriever


def scan_repository(repo_path: str) -> dict[str, Any]:
    """Scan a repository directory for immediate security misconfigurations and secrets.

    Args:
        repo_path: Absolute or relative path to the repository directory.

    Returns:
        Summary dict containing file count, identified issues, and risk levels.
    """
    path = Path(repo_path)
    if not path.exists() or not path.is_dir():
        return {"error": f"Path not found or is not a directory: {repo_path}"}

    issues: list[dict[str, str]] = []
    scanned_files = 0

    # Common security patterns to flag
    secret_pattern = re.compile(
        r"(?i)(password|secret|apikey|access_token|private_key)\s*[:=]\s*['\"][A-Za-z0-9_\-+=]{8,}['\"]"
    )

    for file_path in path.rglob("*"):
        if not file_path.is_file():
            continue
        # Skip git metadata and virtualenvs
        rel_str = str(file_path.relative_to(path))
        if any(part in rel_str for part in (".git", ".venv", "node_modules", "__pycache__")):
            continue

        scanned_files += 1
        if scanned_files > 200:
            break

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            # 1. Secret check
            matches = secret_pattern.findall(content)
            if matches:
                issues.append({
                    "file": rel_str,
                    "type": "EXPOSED_SECRET",
                    "severity": "CRITICAL",
                    "detail": f"Potential exposed credential detected ({len(matches)} match(es))."
                })

            # 2. Dockerfile checks
            if file_path.name.lower() == "dockerfile":
                if "FROM" in content and ":latest" in content:
                    issues.append({
                        "file": rel_str,
                        "type": "UNPINNED_IMAGE",
                        "severity": "HIGH",
                        "detail": "Base image uses unpinned ':latest' tag (violates CIS Docker 4.1)."
                    })
                if "USER " not in content:
                    issues.append({
                        "file": rel_str,
                        "type": "ROOT_USER_CONTAINER",
                        "severity": "HIGH",
                        "detail": "Container defaults to root execution (violates CIS Docker 4.1)."
                    })

            # 3. Kubernetes checks
            if file_path.suffix in (".yaml", ".yml") and "kind: Deployment" in content:
                if "privileged: true" in content:
                    issues.append({
                        "file": rel_str,
                        "type": "PRIVILEGED_POD",
                        "severity": "CRITICAL",
                        "detail": "Pod runs in privileged mode (violates CIS Kubernetes 5.2.5)."
                    })
                if "readOnlyRootFilesystem: true" not in content:
                    issues.append({
                        "file": rel_str,
                        "type": "WRITABLE_ROOT_FS",
                        "severity": "MEDIUM",
                        "detail": "Root filesystem is writable (violates CIS Kubernetes 5.2.6)."
                    })

        except Exception:
            continue

    return {
        "status": "[OK]",
        "scanned_files_count": scanned_files,
        "total_issues_found": len(issues),
        "issues": issues,
    }


def query_cis_standards(query: str, top_k: int = 3) -> list[dict[str, Any]]:
    """Query authoritative CIS Benchmarks and OWASP guidelines via Hybrid RAG.

    Args:
        query: Security topic or check description (e.g. 'root container user').
        top_k: Number of relevant guidelines to retrieve.

    Returns:
        List of matching guideline chunks with source metadata.
    """
    store = KnowledgeStore()
    retriever = HybridRetriever(store=store)
    return retriever.retrieve(query=query, top_k=top_k)


def evaluate_cve_policy(finding_type: str) -> dict[str, str]:
    """Retrieve policy severity and immediate remediation advice for standard vulnerability types."""
    finding_upper = finding_type.strip().upper()
    policy_db = {
        "EXPOSED_SECRET": {
            "severity": "CRITICAL",
            "sla": "4 hours",
            "action": "Revoke credential immediately, rotate secret in Vault, and purge commit history."
        },
        "PRIVILEGED_POD": {
            "severity": "CRITICAL",
            "sla": "24 hours",
            "action": "Set securityContext.privileged: false and drop CAP_SYS_ADMIN capabilities."
        },
        "UNPINNED_IMAGE": {
            "severity": "HIGH",
            "sla": "7 days",
            "action": "Pin base image to SHA256 digest or immutable semver release tag."
        },
        "ROOT_USER_CONTAINER": {
            "severity": "HIGH",
            "sla": "7 days",
            "action": "Add non-root user via 'USER 10001:10001' in Dockerfile and configure runAsNonRoot: true in K8s."
        },
        "WRITABLE_ROOT_FS": {
            "severity": "MEDIUM",
            "sla": "30 days",
            "action": "Configure securityContext.readOnlyRootFilesystem: true and mount emptyDir for /tmp."
        },
    }

    if finding_upper in policy_db:
        entry = policy_db[finding_upper]
        return {
            "policy_match": "[MATCHED]",
            "finding_type": finding_upper,
            "severity": entry["severity"],
            "resolution_sla": entry["sla"],
            "mandated_action": entry["action"],
        }

    return {
        "policy_match": "[UNMATCHED]",
        "finding_type": finding_upper,
        "severity": "INFORMATIONAL",
        "resolution_sla": "Standard sprint cycle",
        "mandated_action": "Review against organizational DevSecOps guidelines."
    }
