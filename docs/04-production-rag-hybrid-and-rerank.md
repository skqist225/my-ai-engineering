# 04 - Production RAG: Hybrid Search and Cross-Encoder Reranking

Most online tutorials demonstrate **Naive RAG**: take raw text, split into 500-token chunks with 50-token overlap, compute cosine similarity over OpenAI embeddings, and pass the top 3 chunks to the model.

In real-world enterprise systems, **Naive RAG fails over 40% of the time**:
1. **The Exact-Keyword Blindspot:** Dense vector embeddings understand high-level semantics (e.g., mapping `"container security"` to `"Docker isolation"`), but they frequently fail on exact technical identifiers (e.g., searching for `CVE-2024-21626`, `AWS_SECRET_ACCESS_KEY`, or `runAsNonRoot: true`). Dense search often returns chunks about general container flaws while missing the exact CVE specification.
2. **Semantic Drift in Top-K:** A vector similarity score of `0.78` might be completely irrelevant if the query had a negative constraint (e.g., `"vulnerabilities that do NOT affect Linux x86"`).
3. **Context Window Pollution:** Passing irrelevant chunks dilutes the model's attention, increases token costs, and induces hallucinations.

Production RAG solves this using a **Two-Stage Hybrid Search & Reranking Architecture**.

---

## 1. The Two-Stage Retrieval Architecture

```
User Query: "CIS Benchmark rule for privileged containers"
                       |
        +--------------+--------------+
        |                             |
        v                             v
[Dense Vector Search]       [Sparse BM25 Search]
(Captures semantic intent)    (Captures exact keywords)
  Top 20 candidates             Top 20 candidates
        |                             |
        +--------------+--------------+
                       |
                       v
         [Reciprocal Rank Fusion (RRF)]
           (Merged Top 15 Candidates)
                       |
                       v
         [Cross-Encoder Reranker Model]
       (Evaluates full Query-Doc interaction)
                       |
                       v
           [Top 3 Reranked Chunks]
                       |
                       v
       [Passed to LLM Context Window]
```

---

## 2. Hybrid Search: Combining Dense Vectors and BM25 Sparse Search

### Dense Search (Bi-Encoder Embeddings)
- Transforms text into a continuous vector space (e.g., 384 or 1536 dimensions).
- Calculates cosine distance between query vector and chunk vectors.
- **Strength:** Paraphrasing, synonyms, conceptual understanding.
- **Weakness:** Exact acronyms, error codes, version numbers.

### Sparse Search (BM25 / TF-IDF)
- Analyzes term frequency and inverse document frequency across exact token matches.
- **Strength:** Pinpoint exact matching for terms like `CVE-2023-44487`, `SonarQube`, `DefectDojo`, or variable names.
- **Weakness:** Zero vocabulary flexibility; cannot match `"auth failure"` with `"login credential error"`.

### Merging with Reciprocal Rank Fusion (RRF)
You cannot simply average dense cosine similarities (range: 0.0 to 1.0) with BM25 scores (unbounded: e.g., 2.4 to 45.2). 

Instead, **Reciprocal Rank Fusion (RRF)** combines them based purely on their **ordinal rank positions**:

$$\text{RRF\_Score}(d) = \sum_{m \in \{\text{dense}, \text{sparse}\}} \frac{1}{k + \text{rank}_m(d)}$$

Where:
- $\text{rank}_m(d)$ is the 1-based rank position of document $d$ in system $m$.
- $k$ is a constant smoothing parameter (standard default is $k = 60$).

If a document appears in the top 3 of **both** dense and BM25 searches, its RRF score spikes dramatically, catapulting it to the top.

```python
def reciprocal_rank_fusion(
    dense_results: list[str],
    sparse_results: list[str],
    k: int = 60
) -> list[tuple[str, float]]:
    scores: dict[str, float] = {}

    for rank, doc_id in enumerate(dense_results, start=1):
        scores[doc_id] = scores.get(doc_id, 0.0) + (1.0 / (k + rank))

    for rank, doc_id in enumerate(sparse_results, start=1):
        scores[doc_id] = scores.get(doc_id, 0.0) + (1.0 / (k + rank))

    # Sort descending by combined score
    return sorted(scores.items(), key=lambda item: item[1], reverse=True)
```

---

## 3. Stage 2: Cross-Encoder Reranking

Bi-encoder models (standard embeddings) embed the query and document **independently**:
$$\text{Sim} = \cos(E(q), E(d))$$
Because query and document never cross-attend to each other during vector generation, fine-grained relationships and nuanced negations are missed.

A **Cross-Encoder model** takes the query and document concatenated together through transformer layers:
$$\text{Input} = [CLS] + \text{Query} + [SEP] + \text{Document}$$
Every token in the query attends to every token in the document simultaneously, yielding dramatically superior precision.

### Why not use Cross-Encoders for the entire database?
Cross-encoders are computationally intensive. Evaluating 100,000 documents with a cross-encoder would take minutes per query. 
Therefore, the production pattern is:
1. **Fast Retrieval:** Dense + BM25 narrows 100,000 documents down to **20 candidates** in milliseconds.
2. **Precision Rerank:** Cross-encoder re-scores only those 20 candidates, selecting the **top 3-5 pristine chunks** for the final LLM prompt.

```python
from sentence_transformers import CrossEncoder

# ms-marco-MiniLM-L-6-v2 runs fast on CPU (free, lightweight)
reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

query = "CIS rule for running as root in docker"
candidate_chunks = [chunk_text_1, chunk_text_2, chunk_text_3]

# Pair query with each candidate
pairs = [[query, doc] for doc in candidate_chunks]
scores = reranker.predict(pairs)

# Re-sort candidates by cross-encoder score
ranked_docs = [doc for _, doc in sorted(zip(scores, candidate_chunks), reverse=True)]
```

By coupling Hybrid Search (RRF) with Cross-Encoder Reranking, retrieval accuracy reaches production reliability.
