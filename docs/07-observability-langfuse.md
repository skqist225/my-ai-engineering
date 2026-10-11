# 07 - Observability and Tracing with Langfuse

In traditional backend services, observability consists of logs, HTTP status codes, and APM traces (Datadog, Dynatrace). A `200 OK` status means the request succeeded.

In AI Engineering, an HTTP `200 OK` from an LLM API tells you almost nothing:
- Did the model return a brilliant security recommendation or a hallucinated fabrication?
- How many tokens did the request consume ($0.0001 or $0.25)?
- Did the prompt template render correctly?
- Which step in the agent loop took 80% of the latency (the vector search, the reranker, or model generation)?

To answer these questions, production AI systems require **LLM-Specific Tracing**. The leading open-source, self-hostable platform is **Langfuse**.

---

## 1. What Langfuse Traces

Langfuse models AI applications as a hierarchy of **Traces** and **Spans**:

```
Trace: "Audit Repository: infra-kubernetes" (Duration: 3.2s, Cost: $0.0042)
  ├── Span: "Ingest Repos" (Duration: 120ms)
  ├── Span: "Hybrid RAG Retrieval" (Duration: 450ms)
  │     ├── Span: "ChromaDB Dense Search" (Duration: 150ms)
  │     ├── Span: "BM25 Sparse Search" (Duration: 40ms)
  │     └── Span: "Cross-Encoder Rerank" (Duration: 260ms)
  ├── Generation: "Security Evaluation (Gemini 2.0 Flash)" (Duration: 1.8s)
  │     ├── Prompt: "system_eval_v2.j2"
  │     ├── Tokens: Prompt=2,450, Completion=380, Total=2,830
  │     └── Cost: $0.0014
  └── Span: "Pydantic Schema Validation" (Duration: 5ms)
```

### Key Metrics Captured:
1. **Token Economics:** Exact prompt and completion token counts tracked across providers, broken down by model version.
2. **Cost Calculation:** Automated cost assignment per generation based on current provider pricing.
3. **Prompt Versioning:** Tracks which exact prompt template version generated each response, enabling A/B testing.
4. **Latency Profiling:** Identifies whether bottlenecks stem from retrieval or model token generation.

---

## 2. Integrating Langfuse in Python

Langfuse provides native integrations with LangChain, LangGraph, and raw Python functions via decorators:

```python
from langfuse import Langfuse
from langfuse.decorators import observe, langfuse_context

# Initialize Langfuse client (reads LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST)
langfuse = Langfuse()

@observe(name="hybrid_rag_search")
def retrieve_security_context(query: str) -> list[str]:
    # Update current span metadata
    langfuse_context.update_current_observation(
        metadata={"query": query, "strategy": "dense_bm25_rrf"}
    )
    results = perform_hybrid_search(query)
    return results

@observe(as_type="generation", name="llm_security_eval")
def call_llm_reasoning(prompt: str, model_name: str) -> str:
    response = model_client.generate(prompt)
    
    # Log token usage and model metadata to Langfuse
    langfuse_context.update_current_observation(
        model=model_name,
        usage={
            "input": response.usage.prompt_tokens,
            "output": response.usage.completion_tokens,
        }
    )
    return response.text
```

---

## 3. Prometheus Telemetry for DevOps Operations

In addition to deep debugging in Langfuse, the DevOps platform needs real-time cluster metrics for alerting and autoscaling.

We export Prometheus metrics on `/metrics`:

```python
from prometheus_client import Counter, Histogram

AI_REQUESTS_TOTAL = Counter(
    "ai_agent_requests_total",
    "Total AI agent pipeline executions",
    ["agent_name", "status"]
)

AI_TOKENS_TOTAL = Counter(
    "ai_agent_tokens_total",
    "Total tokens consumed by model provider",
    ["provider", "model", "token_type"]  # token_type: prompt | completion
)

AI_LATENCY_SECONDS = Histogram(
    "ai_agent_latency_seconds",
    "Latency breakdown of AI agent stages",
    ["stage"],  # stage: ingestion | rag | inference | validation
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0]
)
```

This bridges the gap between deep application-level AI tracing and enterprise infrastructure monitoring.
