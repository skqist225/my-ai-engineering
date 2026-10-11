"""Layer 2: Local ChromaDB Vector Store Integration."""

import os
from pathlib import Path
from typing import Any
import chromadb
from chromadb.utils import embedding_functions


class VectorStore:
    """ChromaDB wrapper providing dense vector storage and query capabilities."""

    def __init__(
        self,
        persist_dir: str = "./chromadb_data",
        collection_name: str = "security_standards",
    ) -> None:
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        self.client = chromadb.PersistentClient(path=self.persist_dir)

        # Lightweight, free, local sentence-transformer embedding function
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )

        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self.embedding_fn,
            metadata={"description": "CIS Benchmarks and OWASP DevSecOps rules"}
        )

    def add_documents(
        self,
        documents: list[str],
        metadatas: list[dict[str, str]],
        ids: list[str],
    ) -> None:
        """Add text chunks with metadata to the vector collection."""
        self.collection.upsert(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
        )

    def dense_query(self, query: str, top_k: int = 10) -> list[dict[str, Any]]:
        """Perform dense vector semantic search."""
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
        )

        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        ids = results.get("ids", [[]])[0]
        distances = results.get("distances", [[]])[0]

        output = []
        for doc, meta, doc_id, dist in zip(docs, metas, ids, distances):
            output.append({
                "id": doc_id,
                "content": doc,
                "metadata": meta,
                "dense_score": 1.0 - dist if dist is not None else 1.0,
            })
        return output

    def count(self) -> int:
        """Return total chunks stored."""
        return self.collection.count()


# Alias for backward and cross-layer compatibility
KnowledgeStore = VectorStore

__all__ = ["VectorStore", "KnowledgeStore"]

