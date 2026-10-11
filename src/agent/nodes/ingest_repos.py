"""Node 1: Ingest Repositories and File Structures."""

import os
from pathlib import Path
from src.agent.state import AgentState
from src.guardrails.privacy import redact_secrets

INTERESTING_EXTENSIONS = {".yaml", ".yml", ".tf", ".json", ".dockerfile"}
INTERESTING_NAMES = {"dockerfile", "jenkinsfile", "compose.yaml", "compose.yml"}


def is_security_relevant_file(file_path: Path) -> bool:
    """Determine if a file is relevant for DevSecOps analysis."""
    name_lower = file_path.name.lower()
    if name_lower in INTERESTING_NAMES:
        return True
    if file_path.suffix.lower() in INTERESTING_EXTENSIONS:
        return True
    return False


def ingest_repos_node(state: AgentState) -> dict:
    """Scan local repositories, record files, and load contents with secret scrubbing."""
    repos_dir = Path(state["repos_dir"])
    scope = state.get("scope", "all")

    repo_files: dict[str, list[str]] = {}
    file_contents: dict[str, str] = {}

    if not repos_dir.exists():
        return {
            "repo_files": {},
            "file_contents": {},
            "execution_metrics": {"ingested_repos_count": 0, "ingested_files_count": 0}
        }

    # Discover target repositories
    target_dirs = []
    if scope == "all":
        target_dirs = [d for d in repos_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]
    else:
        specific = repos_dir / scope
        if specific.is_dir():
            target_dirs = [specific]

    for repo_dir in target_dirs:
        repo_name = repo_dir.name
        repo_files[repo_name] = []

        for root, dirs, files in os.walk(repo_dir):
            # Skip hidden and dependency directories
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("node_modules", ".venv", "target", "vendor")]

            for fname in files:
                fpath = Path(root) / fname
                if is_security_relevant_file(fpath):
                    rel_to_repo = str(fpath.relative_to(repo_dir)).replace("\\", "/")
                    qualified_key = f"{repo_name}/{rel_to_repo}"
                    repo_files[repo_name].append(rel_to_repo)

                    try:
                        # Read and scrub secrets immediately (Layer 5 Guardrail)
                        raw_text = fpath.read_text(encoding="utf-8", errors="ignore")
                        redaction = redact_secrets(raw_text)
                        file_contents[qualified_key] = redaction.redacted_text
                    except Exception:
                        pass

    return {
        "repo_files": repo_files,
        "file_contents": file_contents,
        "execution_metrics": {
            "ingested_repos_count": len(repo_files),
            "ingested_files_count": len(file_contents),
        }
    }
