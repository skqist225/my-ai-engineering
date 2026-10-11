"""Layer 2: Cross-Encoder Precision Reranker."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class CrossEncoderReranker:
    """Re-scores candidate chunks using a cross-encoder for high-precision semantic matching."""

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2") -> None:
        self.model_name = model_name
        self._model = None

    def _load_model(self) -> Any:
        if self._model is None:
            try:
                from sentence_transformers import CrossEncoder
                self._model = CrossEncoder(self.model_name)
            except Exception as exc:
                logger.warning("[WARN] Could not load cross-encoder model %s (%s). Using fallback ranker.",
                               self.model_name, str(exc))
                self._model = False
        return self._model

    def rerank(
        self,
        query: str,
        documents: list[dict[str, Any]],
        top_k: int = 3,
    ) -> list[dict[str, Any]]:
        """Rerank candidate chunks according to cross-encoder score.

        Args:
            query: User search query or vulnerability signature.
            documents: Candidate document dicts (must contain 'content' key).
            top_k: Number of highest-relevance chunks to return.

        Returns:
            Re-ordered top_k document list with added 'rerank_score' key.
        """
        if not documents:
            return []

        model = self._load_model()
        if model:
            pairs = [[query, doc["content"]] for doc in documents]
            scores = model.predict(pairs)

            ranked = []
            for doc, score in zip(documents, scores):
                doc_copy = dict(doc)
                doc_copy["rerank_score"] = float(score)
                ranked.append(doc_copy)

            ranked.sort(key=lambda x: x["rerank_score"], reverse=True)
            return ranked[:top_k]

        # Graceful fallback: maintain RRF score order if cross-encoder model is unavailable
        for doc in documents:
            doc["rerank_score"] = doc.get("rrf_score", 0.0)
        return documents[:top_k]
