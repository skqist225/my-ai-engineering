"""LLM reasoning node — uses Gemini (or any configured provider) for gap analysis."""

import json
import time
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage

from src.llm_factory import get_chat_model
from src.observability import langfuse_trace
from src.prompts.system import SYSTEM_PROMPT
from src.vectorstore import CodeVectorStore
from src.nodes.ingest_repos import chunk_file

# Gemini free tier: 15 RPM, 1M tokens/day — pace accordingly
_RATE_LIMIT_SLEEP = 5  # seconds between repos


# File extensions prioritized for embedding (DevSecOps-relevant code)
_PRIORITY_EXTENSIONS = {
    ".groovy", ".Jenkinsfile", ".yaml", ".yml", ".toml", ".json",
    ".py", ".sh", ".ps1", ".psm1", ".tf", ".hcl",
    ".go", ".rs", ".ts", ".js", ".java",
    ".dockerfile", ".properties", ".cfg", ".ini", ".conf",
}
_MAX_FILES_PER_REPO = 200  # CPU embedding budget


def _prioritize_files(file_list: list[str]) -> list[str]:
    """Sort files by DevSecOps relevance and cap at _MAX_FILES_PER_REPO."""
    priority = []
    rest = []
    for f in file_list:
        lower = f.lower()
        # Top priority: Jenkinsfiles, Dockerfiles, security configs
        if any(k in lower for k in ("jenkinsfile", "dockerfile", ".gitleaks", "kyverno", "helm")):
            priority.append(f)
        elif any(f.lower().endswith(ext) for ext in _PRIORITY_EXTENSIONS):
            priority.append(f)
        else:
            rest.append(f)
    return (priority + rest)[:_MAX_FILES_PER_REPO]


def _embed_repo_if_needed(
    repo_name: str,
    repos_dir: Path,
    vector_store: CodeVectorStore,
    file_list: list[str],
    force: bool = False,
) -> None:
    """Embed repo code chunks into ChromaDB if not already present."""
    if not force and vector_store.count() > 0:
        print(f"[embed] {repo_name}: ChromaDB has {vector_store.count()} chunks, skipping re-embed", flush=True)
        return

    repo_path = repos_dir / repo_name
    selected_files = _prioritize_files(file_list)
    print(f"[embed] {repo_name}: embedding {len(selected_files)}/{len(file_list)} files (capped at {_MAX_FILES_PER_REPO})...", flush=True)

    total_chunks = 0
    batch_docs: list[str] = []
    batch_meta: list[dict] = []
    BATCH_SIZE = 100  # Flush to ChromaDB every N chunks

    for i, rel_path in enumerate(selected_files):
        file_path = repo_path / rel_path
        if not file_path.exists() or file_path.stat().st_size > 500_000:
            continue
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        chunks = chunk_file(content, language=file_path.suffix)
        if chunks:
            for c in chunks:
                batch_docs.append(c)
                batch_meta.append({"repo": repo_name, "file": rel_path, "language": file_path.suffix})

            # Flush batch to ChromaDB when large enough
            if len(batch_docs) >= BATCH_SIZE:
                vector_store.add_chunks(batch_docs, batch_meta)
                total_chunks += len(batch_docs)
                batch_docs.clear()
                batch_meta.clear()

        # Progress every 50 files
        if (i + 1) % 50 == 0:
            print(f"[embed] {repo_name}: {i + 1}/{len(selected_files)} files processed ({total_chunks} chunks)...", flush=True)

    # Flush remaining
    if batch_docs:
        vector_store.add_chunks(batch_docs, batch_meta)
        total_chunks += len(batch_docs)

    print(f"[embed] {repo_name}: done — {total_chunks} chunks embedded", flush=True)


def reason_about_repo(
    repo_name: str,
    rubric_results: list[dict],
    tool_findings: list[dict],
    vector_store: CodeVectorStore,
) -> list[dict]:
    """Use LLM to analyze rubric results + tool findings and produce recommendations.

    Args:
        repo_name: Name of the repo being analyzed.
        rubric_results: Deterministic rubric check results.
        tool_findings: Findings from DefectDojo/SonarQube.
        vector_store: ChromaDB store with embedded code chunks.

    Returns:
        List of recommendation dicts.
    """
    llm = get_chat_model()

    # Retrieve relevant code context for failed/warned rubric items
    failed_items = [r for r in rubric_results if r["status"] in ("FAIL", "WARN")]

    context_chunks = []
    for item in failed_items[:10]:  # Limit queries to avoid rate limits
        query = f"{item['title']} {item.get('evidence', '')}"
        try:
            results = vector_store.search(query, k=3, where={"repo": repo_name})
            context_chunks.extend(results)
        except Exception:
            # ChromaDB may fail if collection is empty
            pass

    # Deduplicate context by content prefix
    seen: set[str] = set()
    unique_context = []
    for c in context_chunks:
        key = c["content"][:100]
        if key not in seen:
            seen.add(key)
            unique_context.append(c)

    # Build context text
    context_text = "\n\n".join([
        f"--- {c['metadata'].get('file', 'unknown')} ---\n{c['content']}"
        for c in unique_context[:15]
    ])

    # Truncate rubric results to keep within free-tier token budget
    # Only send FAIL/WARN items (PASS items are noise for the LLM)
    rubric_for_llm = [r for r in rubric_results if r["status"] in ("FAIL", "WARN")][:30]
    rubric_text = json.dumps(rubric_for_llm, indent=2, default=str)

    # Truncate tool findings for token budget
    findings_summary = json.dumps(tool_findings[:20], indent=2, default=str)

    user_prompt = f"""## Repo: {repo_name}

## RUBRIC RESULTS — Failed/Warning checks only ({len(rubric_for_llm)} of {len(rubric_results)} total)
{rubric_text}

## EXISTING TOOL FINDINGS (DefectDojo + SonarQube, first 20)
{findings_summary if tool_findings else "No tool findings available (tools not configured or no findings)."}

## RELEVANT CODE CONTEXT (from semantic search)
{context_text if context_text else "No code context available."}

Produce your recommendations as a JSON array. Focus on GAPS — things the existing tools missed.
If rubric results show all PASS and no tool findings, you may return an empty array [].
Limit to your top 10 most impactful recommendations.
"""

    print(f"[reason] Calling LLM for {repo_name} ({len(rubric_for_llm)} failed/warn items)...", flush=True)

    with langfuse_trace(session_id=f"advisor-{repo_name}") as callbacks:
        response = llm.invoke(
            [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=user_prompt),
            ],
            config={"callbacks": callbacks} if callbacks else {},
        )

    # Parse JSON from response
    # Gemini 3.6 may return content as a list of parts — normalize to string
    content = response.content
    if isinstance(content, list):
        content = "\n".join(
            part if isinstance(part, str) else part.get("text", str(part))
            for part in content
        )
    content = str(content)

    # Strip markdown code fences if present
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0]
    elif "```" in content:
        content = content.split("```")[1].split("```")[0]

    try:
        recommendations = json.loads(content.strip())
        if not isinstance(recommendations, list):
            recommendations = [recommendations]
    except json.JSONDecodeError:
        print(f"[reason] WARNING: Failed to parse LLM JSON response for {repo_name}", flush=True)
        recommendations = [{
            "id": "PARSE-ERROR",
            "title": "LLM response parsing failed",
            "category": "quality",
            "risk": "Low",
            "effort": "XS",
            "recommendation": f"Raw LLM response (first 500 chars): {content[:500]}",
            "existing_tool_covers": False,
            "confidence": 0.0,
        }]

    print(f"[reason] {repo_name}: {len(recommendations)} recommendations generated", flush=True)
    return recommendations


def reason_node(state: dict) -> dict:
    """LangGraph node: Run LLM reasoning on all repos.

    Reads state['rubric_results'], state['tool_findings'], state['repo_files'].
    Writes state['recommendations'] with {repo_name: [recommendation_dicts]}.
    """
    repos_dir = Path(state["repos_dir"])
    chromadb_path = state.get("chromadb_path", "D:\\data\\ai-agent\\chromadb")
    force_reindex = state.get("force_reindex", False)

    vector_store = CodeVectorStore(persist_dir=chromadb_path)

    if force_reindex:
        print("[reason] Force reindex requested — clearing ChromaDB", flush=True)
        vector_store.clear()

    recommendations: dict[str, list[dict]] = {}

    for repo_name in state.get("repo_files", {}):
        # Embed code chunks
        _embed_repo_if_needed(
            repo_name, repos_dir, vector_store,
            state["repo_files"][repo_name], force=force_reindex,
        )

        # Run LLM reasoning
        rubric = state.get("rubric_results", {}).get(repo_name, [])
        findings = state.get("tool_findings", {}).get(repo_name, [])

        recs = reason_about_repo(repo_name, rubric, findings, vector_store)
        recommendations[repo_name] = recs

        # Rate-limit between repos to stay within Gemini free tier (15 RPM)
        time.sleep(_RATE_LIMIT_SLEEP)

    state["recommendations"] = recommendations
    return state
