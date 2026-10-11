"""Repo ingestion node — walks repos and chunks code files for embedding."""

from pathlib import Path

from langchain_text_splitters import Language, RecursiveCharacterTextSplitter

# Directories to skip during file walk
IGNORE_DIRS = {
    ".git", "node_modules", "bin", "obj", ".gradle", "build",
    "__pycache__", ".venv", "dist", ".scannerwork", "packages",
    ".agent", ".antigravitycli", "logs", "output", "tmp",
}

# File extensions to ingest
SCAN_EXTENSIONS = {
    ".groovy", ".ps1", ".py", ".go", ".yaml", ".yml", ".json",
    ".tf", ".hcl", ".rs", ".cs", ".js", ".ts", ".toml", ".xml",
    ".sh", ".bash", ".properties", ".ini", ".cfg",
}

# Filename prefixes to ingest regardless of extension
SCAN_FILENAME_PREFIXES = ("Jenkinsfile", "Dockerfile", "Makefile", "Vagrantfile")

# Map file extensions to LangChain Language splitters
LANGUAGE_MAP = {
    ".groovy": Language.JAVA,   # Closest available for Groovy
    ".go": Language.GO,
    ".py": Language.PYTHON,
    ".js": Language.JS,
    ".ts": Language.TS,
    ".rs": Language.RUST,
    ".cs": Language.CSHARP,
    ".rb": Language.RUBY,
}


def walk_repo(repo_path: Path) -> list[Path]:
    """Walk a repo directory tree, returning all scannable files.

    Skips directories in IGNORE_DIRS and filters by extension/filename.
    Returns sorted list of absolute paths.
    """
    files = []
    for p in repo_path.rglob("*"):
        # Skip ignored directories
        if any(part in IGNORE_DIRS for part in p.parts):
            continue
        if not p.is_file():
            continue
        # Include by extension or filename prefix (Jenkinsfile-*, Dockerfile.*, etc.)
        if p.suffix.lower() in SCAN_EXTENSIONS or p.name.startswith(SCAN_FILENAME_PREFIXES):
            files.append(p)
    return sorted(files)


def chunk_file(
    content: str,
    language: str = "generic",
    chunk_size: int = 1500,
    chunk_overlap: int = 200,
) -> list[str]:
    """Split file content into chunks using language-aware splitter.

    Args:
        content: Raw file text content.
        language: File extension (e.g. ".groovy") or language name.
        chunk_size: Target chunk size in characters.
        chunk_overlap: Overlap between chunks.

    Returns:
        List of text chunks.
    """
    if not content.strip():
        return []

    ext = f".{language}" if not language.startswith(".") else language
    lang = LANGUAGE_MAP.get(ext)

    if lang:
        splitter = RecursiveCharacterTextSplitter.from_language(
            language=lang,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
    else:
        # Generic splitter for YAML, PowerShell, config files, etc.
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""],
        )

    return splitter.split_text(content)


def ingest_repos_node(state: dict) -> dict:
    """LangGraph node: Walk all repos and collect file inventory.

    Reads state['repos_dir'] and state['scope'].
    Writes state['repo_files'] with {repo_name: [relative_paths]}.
    """
    repos_dir = Path(state["repos_dir"])
    scope = state.get("scope", "all")

    repo_files: dict[str, list[str]] = {}

    # Determine which subdirectories are repos
    if scope == "all":
        candidates = [
            d for d in repos_dir.iterdir()
            if d.is_dir() and (d / ".git").exists()
        ]
    else:
        target = repos_dir / scope
        if target.exists() and target.is_dir():
            candidates = [target]
        else:
            print(f"[WARN] Repo '{scope}' not found at {target}")
            candidates = []

    for repo_dir in sorted(candidates):
        repo_name = repo_dir.name
        files = walk_repo(repo_dir)
        relative_paths = [str(f.relative_to(repo_dir)) for f in files]
        repo_files[repo_name] = relative_paths
        print(f"[ingest_repos] {repo_name}: {len(relative_paths)} files found")

    state["repo_files"] = repo_files
    return state
