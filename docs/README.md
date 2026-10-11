# Production AI Engineering Documentation Suite

Welcome to the **AI Engineering Platform** documentation suite. This manual provides a complete curriculum and production architecture guide for software and DevOps engineers transitioning into modern AI Engineering.

---

## Documentation Index

| Guide | Description |
|---|---|
| [**01 - AI Engineering vs MLOps**](01-ai-engineering-vs-mlops.md) | The mental model and distinct responsibilities of AI Engineers vs MLOps Engineers. |
| [**02 - Architecture & The 7 Production Layers**](02-architecture-and-the-7-layers.md) | High-level system blueprint, component interaction, and layer contracts. |
| [**03 - Agentic Orchestration with LangGraph**](03-agentic-orchestration-langgraph.md) | Stateful cyclic graphs, reducers, checkpointing, and Human-in-the-Loop gates. |
| [**04 - Production RAG: Hybrid & Reranking**](04-production-rag-hybrid-and-rerank.md) | Dense Vector + BM25 Sparse search, Reciprocal Rank Fusion (RRF), and Cross-Encoder reranking. |
| [**05 - Structured Outputs & Instructor**](05-structured-outputs-instructor.md) | Enforcing Pydantic v2 schemas and self-healing LLM validation retry loops. |
| [**06 - Guardrails & AI Application Security**](06-guardrails-and-ai-security.md) | Defense-in-depth: prompt injection detection, PII/secret scrubbing, and citation grounding. |
| [**07 - Observability & Tracing with Langfuse**](07-observability-langfuse.md) | Nested spans, token economics, latency profiling, and Prometheus telemetry. |
| [**08 - Evals & Prompt CI/CD**](08-evals-and-prompt-ci.md) | Evaluation-Driven Development (EDD), the RAG Triad (Ragas), and Promptfoo in CI/CD. |
| [**09 - Model Context Protocol (MCP)**](09-model-context-protocol-mcp.md) | The universal standard for exposing tools, resources, and prompts to AI systems. |
| [**10 - Getting Started & Walkthrough**](10-getting-started-and-walkthrough.md) | Step-by-step local setup running 100% free with Gemini Flash and local ChromaDB. |

---

## The 7-Layer Production Stack

```
Layer 7: Automated Evals (Ragas Triad, Promptfoo in CI/CD)
Layer 6: Observability & Telemetry (Langfuse Distributed Tracing, Prometheus)
Layer 5: Defense-in-Depth Guardrails (Prompt Injections, Secret Scrubbing, Grounding)
Layer 4: Agentic Orchestration & Protocols (LangGraph StateGraph, FastMCP Server)
Layer 3: Structured Outputs & Validation (Instructor, Pydantic v2 Self-Correction)
Layer 2: Production Hybrid RAG (Dense Embeddings + BM25 via RRF, Cross-Encoder Rerank)
Layer 1: Foundation Models & Dynamic Gateway (Gemini 2.0 Flash, Groq, Ollama, Claude)
```
