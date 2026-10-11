"""Agent state definition for LangGraph."""

from typing import TypedDict


class AgentState(TypedDict):
    """State that flows through the LangGraph agent pipeline.

    Each node reads from and writes to this shared state.
    """

    # Input configuration
    repos_dir: str
    scope: str  # "all" or specific repo name
    chromadb_path: str
    output_dir: str
    force_reindex: bool

    # Populated by ingest_repos node
    repo_files: dict[str, list[str]]  # repo_name -> [relative_file_paths]

    # Populated by evaluate_rubric node
    rubric_results: dict[str, list[dict]]  # repo_name -> [RubricResult dicts]

    # Populated by ingest_tools node
    tool_findings: dict[str, list[dict]]  # repo_name -> [Finding dicts]

    # Populated by reason node
    recommendations: dict[str, list[dict]]  # repo_name -> [Recommendation dicts]

    # Populated by report node
    report_path: str | None
