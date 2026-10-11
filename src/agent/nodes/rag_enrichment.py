"""Node 3: Layer 2 Hybrid RAG Context Enrichment."""

from pathlib import Path
from src.agent.state import AgentState
from src.rag.retriever import HybridRetriever
from src.rag.reranker import CrossEncoderReranker


def load_knowledge_base_chunks() -> list[dict[str, str]]:
    """Load standard markdown and json knowledge chunks from data/knowledge/."""
    knowledge_dir = Path(__file__).resolve().parent.parent.parent.parent / "data" / "knowledge"
    chunks = []

    if not knowledge_dir.exists():
        return chunks

    for file_path in knowledge_dir.glob("*.md"):
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        # Split by section headers
        sections = content.split("### ")
        for idx, sec in enumerate(sections):
            if sec.strip():
                title_line = sec.splitlines()[0]
                chunks.append({
                    "id": f"{file_path.stem}_{idx}",
                    "content": f"### {sec.strip()}",
                    "metadata": {"source": file_path.name, "title": title_line}
                })

    return chunks


def rag_enrichment_node(state: AgentState) -> dict:
    """Enrich agent state with authoritative CIS & OWASP standards via Hybrid RAG."""
    file_contents = state.get("file_contents", {})
    if not file_contents:
        return {"retrieved_context": []}

    # Initialize retriever & index knowledge base
    retriever = HybridRetriever()
    knowledge_chunks = load_knowledge_base_chunks()
    if knowledge_chunks:
        retriever.index_documents(knowledge_chunks)

    reranker = CrossEncoderReranker()

    # Formulate queries based on observed configurations
    queries = []
    has_docker = any("dockerfile" in k.lower() for k in file_contents)
    has_k8s = any(".yaml" in k.lower() or ".yml" in k.lower() for k in file_contents)

    if has_docker:
        queries.append("CIS Docker non-root user and base image tagging guidelines")
    if has_k8s:
        queries.append("CIS Kubernetes privileged container security context and memory limits")

    if not queries:
        queries.append("DevSecOps CI/CD secret scrubbing and branch protection guidelines")

    all_retrieved = []
    for q in queries:
        candidates = retriever.retrieve(q, top_k=6)
        reranked = reranker.rerank(q, candidates, top_k=2)
        all_retrieved.extend(reranked)

    return {"retrieved_context": all_retrieved}
