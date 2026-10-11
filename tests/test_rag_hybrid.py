"""Unit tests for Layer 2: Hybrid RAG (Dense + BM25 via Reciprocal Rank Fusion) and Reranking."""

import pytest
from unittest.mock import MagicMock
from src.rag.retriever import tokenize, reciprocal_rank_fusion, HybridRetriever
from src.rag.reranker import CrossEncoderReranker


def test_tokenize_alphanumeric():
    text = "CIS-K8S-5.2: Ensure privileged containers are NOT allowed!"
    tokens = tokenize(text)
    assert "cis" in tokens
    assert "k8s" in tokens
    assert "privileged" in tokens
    assert "containers" in tokens


def test_reciprocal_rank_fusion():
    # Dense results
    list_dense = [
        {"id": "doc1", "content": "Docker security", "dense_score": 0.9},
        {"id": "doc2", "content": "Kubernetes RBAC", "dense_score": 0.8},
        {"id": "doc3", "content": "Secret detection", "dense_score": 0.7},
    ]

    # Sparse results
    list_sparse = [
        {"id": "doc2", "content": "Kubernetes RBAC", "bm25_score": 5.2},
        {"id": "doc1", "content": "Docker security", "bm25_score": 3.1},
        {"id": "doc4", "content": "Vault injection", "bm25_score": 2.0},
    ]

    fused = reciprocal_rank_fusion([list_dense, list_sparse], k=60)
    assert len(fused) == 4
    # doc1 and doc2 appear in both lists, so their RRF scores should be higher than doc3 and doc4
    top_ids = [d["id"] for d in fused[:2]]
    assert "doc1" in top_ids
    assert "doc2" in top_ids


def test_hybrid_retriever_sparse_fallback():
    mock_store = MagicMock()
    mock_store.dense_query.return_value = [
        {"id": "c1", "content": "CIS Docker Non-Root Guideline", "metadata": {}}
    ]

    retriever = HybridRetriever(vector_store=mock_store)
    docs = [
        {"id": "c1", "content": "CIS Docker Non-Root Guideline", "metadata": {}},
        {"id": "c2", "content": "OWASP Injection in CI Pipeline", "metadata": {}},
    ]
    retriever.index_documents(docs)

    results = retriever.retrieve(query="Docker non-root", top_k=2)
    assert len(results) > 0
    assert results[0]["id"] == "c1"


def test_reranker_fallback():
    reranker = CrossEncoderReranker()
    candidates = [
        {"id": "c1", "content": "Irrelevant info", "rrf_score": 0.03},
        {"id": "c2", "content": "Exact match for CIS Benchmark", "rrf_score": 0.02},
    ]

    # Without heavy cross-encoder model loaded, it preserves candidates or returns ordered slice
    reranked = reranker.rerank(query="CIS Benchmark", candidates=candidates, top_k=1)
    assert len(reranked) == 1
