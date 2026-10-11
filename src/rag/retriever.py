"""Layer 2: Hybrid Retriever combining Dense Vector and BM25 Sparse Search via RRF."""

import re
from typing import Any
from rank_bm25 import BM25Okapi

from src.rag.store import VectorStore


def tokenize(text: str) -> list[str]:
    """Simple alphanumeric tokenizer for BM25 keyword matching."""
    return re.findall(r"\w+", text.lower())


def reciprocal_rank_fusion(
    ranked_lists: list[list[dict[str, Any]]],
    k: int = 60,
) -> list[dict[str, Any]]:
    """Combine multiple ranked candidate lists using Reciprocal Rank Fusion (RRF).

    Formula:
        RRF_score(doc) = sum_{list in ranked_lists} 1 / (k + rank_in_list)

    Args:
        ranked_lists: List of ranked lists, where each list contains doc dicts with an 'id' key.
        k: Smoothing constant (default 60 from information retrieval literature).

    Returns:
        Consolidated list of documents sorted in descending order of RRF score.
    """
    scores: dict[str, float] = {}
    doc_lookup: dict[str, dict[str, Any]] = {}

    for ranked_list in ranked_lists:
        for rank, doc in enumerate(ranked_list, start=1):
            doc_id = doc["id"]
            doc_lookup[doc_id] = doc
            scores[doc_id] = scores.get(doc_id, 0.0) + (1.0 / (k + rank))

    # Sort descending by RRF score
    sorted_items = sorted(scores.items(), key=lambda item: item[1], reverse=True)

    results = []
    for doc_id, rrf_score in sorted_items:
        doc = dict(doc_lookup[doc_id])
        doc["rrf_score"] = round(rrf_score, 5)
        results.append(doc)

    return results


class HybridRetriever:
    """Production Hybrid Retriever combining Dense Vector embeddings and BM25 keyword search."""

    def __init__(self, vector_store: VectorStore | None = None) -> None:
        self.vector_store = vector_store or VectorStore()
        self.documents: list[dict[str, Any]] = []
        self.corpus_tokens: list[list[str]] = []
        self.bm25: BM25Okapi | None = None

    def index_documents(self, documents: list[dict[str, Any]]) -> None:
        """Index chunks into both ChromaDB (dense) and BM25 (sparse).

        Each document dict must have: 'id', 'content', and optional 'metadata'.
        """
        self.documents = documents
        texts = [doc["content"] for doc in documents]
        metas = [doc.get("metadata", {}) for doc in documents]
        ids = [doc["id"] for doc in documents]

        # 1. Index into ChromaDB
        self.vector_store.add_documents(documents=texts, metadatas=metas, ids=ids)

        # 2. Index into BM25
        self.corpus_tokens = [tokenize(t) for t in texts]
        self.bm25 = BM25Okapi(self.corpus_tokens)

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        dense_candidates: int = 15,
        sparse_candidates: int = 15,
    ) -> list[dict[str, Any]]:
        """Execute hybrid search using Reciprocal Rank Fusion."""
        if not self.documents or self.bm25 is None:
            return []

        # 1. Dense Semantic Search
        dense_results = self.vector_store.dense_query(query, top_k=dense_candidates)

        # 2. Sparse BM25 Search
        query_tokens = tokenize(query)
        bm25_scores = self.bm25.get_scores(query_tokens)

        # Sort BM25 results descending
        sparse_ranked = []
        indexed_scores = sorted(enumerate(bm25_scores), key=lambda x: x[1], reverse=True)
        for idx, score in indexed_scores[:sparse_candidates]:
            if score > 0.0:  # Only include chunks with at least one matching term
                doc = dict(self.documents[idx])
                doc["bm25_score"] = float(score)
                sparse_ranked.append(doc)

        # 3. Reciprocal Rank Fusion
        fused = reciprocal_rank_fusion([dense_results, sparse_ranked])
        return fused[:top_k]
