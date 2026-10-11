"""ChromaDB vector store wrapper for code chunk embedding and retrieval."""

import hashlib

import chromadb
from sentence_transformers import SentenceTransformer


class CodeVectorStore:
    """Wraps ChromaDB with sentence-transformer embeddings for code search.

    Uses all-MiniLM-L6-v2 (80MB, CPU-feasible) for embeddings.
    Persists to disk via ChromaDB's PersistentClient.
    """

    def __init__(
        self,
        persist_dir: str,
        collection_name: str = "devops_code",
        embedding_model: str = "all-MiniLM-L6-v2",
    ):
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        self._embedder = SentenceTransformer(embedding_model)

    def add_chunks(
        self,
        chunks: list[str],
        metadatas: list[dict],
    ) -> None:
        """Embed and store code chunks with metadata.

        Args:
            chunks: List of text content to embed.
            metadatas: Parallel list of metadata dicts (must include 'repo', 'file').
        """
        if not chunks:
            return

        embeddings = self._embedder.encode(chunks).tolist()
        # Use content hash + index as stable ID for upsert idempotency
        ids = [
            hashlib.md5(
                f"{m.get('repo', '')}:{m.get('file', '')}:{i}:{c[:100]}".encode()
            ).hexdigest()
            for i, (c, m) in enumerate(zip(chunks, metadatas))
        ]
        self.collection.upsert(
            ids=ids,
            documents=chunks,
            embeddings=embeddings,
            metadatas=metadatas,
        )

    def search(
        self,
        query: str,
        k: int = 5,
        where: dict | None = None,
    ) -> list[dict]:
        """Semantic search for code chunks similar to query.

        Args:
            query: Natural language or code search query.
            k: Number of results to return.
            where: Optional ChromaDB filter (e.g. {"repo": "jenkins-shared-lib"}).

        Returns:
            List of dicts with 'content', 'metadata', 'distance' keys.
        """
        query_embedding = self._embedder.encode([query]).tolist()

        kwargs = {"query_embeddings": query_embedding, "n_results": k}
        if where:
            kwargs["where"] = where

        results = self.collection.query(**kwargs)

        if not results["documents"] or not results["documents"][0]:
            return []

        return [
            {"content": doc, "metadata": meta, "distance": dist}
            for doc, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            )
        ]

    def count(self) -> int:
        """Return total number of chunks in the collection."""
        return self.collection.count()

    def clear(self) -> None:
        """Delete and recreate the collection."""
        name = self.collection.name
        metadata = self.collection.metadata
        self.client.delete_collection(name)
        self.collection = self.client.get_or_create_collection(
            name=name, metadata=metadata
        )
