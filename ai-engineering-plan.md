# AI Engineering Platform - Dual-Track DevSecOps Autonomous Agent

## Executive Summary
This project transforms `D:\tools\ai-engineering` from a basic linear scanner into a production-grade **Compound AI System** and learning blueprint. It demonstrates all 7 critical layers of modern AI Engineering applied to enterprise DevSecOps:
1. **Foundation Models & Routing Gateway:** Multi-provider LLM Factory (Gemini 2.0, Groq, Ollama, Claude, OpenAI) with dynamic fallback and cost-aware routing.
2. **Advanced Retrieval-Augmented Generation (RAG):** Hybrid search (Dense Vector + BM25 Sparse Keyword via Reciprocal Rank Fusion) and Cross-Encoder Reranking over CIS/OWASP security standards.
3. **Structured Outputs & Schema Validation:** Pydantic v2 and Instructor with self-healing retry validation loops.
4. **Agentic Orchestration & Protocols:** Stateful cyclic LangGraph with checkpointing, conditional branching, Human-in-the-Loop interrupts, and Model Context Protocol (MCP) server.
5. **Defense-in-Depth Guardrails:** Prompt injection detection, PII/Secret scrubbing, and hallucination grounding checks.
6. **Observability & Telemetry:** Langfuse distributed tracing, token economics, latency profiling, and Prometheus metrics export.
7. **Automated Evals (CI/CD):** Ragas-style RAG triad evaluation (Faithfulness, Relevancy, Precision), Promptfoo prompt regression suite, and GitHub Actions CI integration.

---

## 7-Layer Production Architecture Blueprint

```
+---------------------------------------------------------------------------------------------------+
|                                     LAYER 7: EVALUATION & CI/CD                                   |
|   - Ragas RAG Triad (Faithfulness, Answer Relevancy, Context Precision)                           |
|   - DeepEval / Pytest Assertion Suite for Deterministic & Non-Deterministic Logic                 |
|   - Promptfoo Prompt Regression Suite (.github/workflows/evals.yaml)                             |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|                                LAYER 6: OBSERVABILITY & TELEMETRY                                 |
|   - Langfuse Tracing (Nested spans, inputs/outputs, model parameters, user feedback scores)       |
|   - Token Economics (Input/Output token counters, cost tracking per LLM provider)                |
|   - Prometheus Metrics Exporter (ai_requests_total, ai_latency_seconds, ai_tokens_total)          |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|                                LAYER 5: GUARDRAILS & AI SECURITY                                  |
|   - Inbound Guardrail: Prompt Injection & Jailbreak Detector                                      |
|   - Data Privacy Guardrail: PII & Secret Redactor (AWS Keys, GitHub PATs, JWTs masked before LLM)|
|   - Outbound Guardrail: Grounding & Hallucination Verifier (remediations must cite real evidence) |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|                             LAYER 4: AGENTIC ORCHESTRATION & PROTOCOLS                            |
|   - Stateful Cyclic LangGraph (StateGraph with MemorySaver checkpointing & state transitions)     |
|   - Dynamic Branching: Critical findings -> Human-in-the-Loop approval gate -> Remediation PR    |
|   - Model Context Protocol (MCP): MCP Server exposing security tools, analyzers, and resources   |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|                                LAYER 3: STRUCTURED OUTPUTS & EXTRACTION                           |
|   - Pydantic v2 Core Domain Models (SecurityFinding, RubricEvaluation, RemediationAction)         |
|   - Instructor Schema Enforcement: Auto-retry with reflection on validation failure               |
|   - Guaranteed 100% JSON syntactic and semantic validity                                          |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|                                  LAYER 2: RETRIEVAL & CONTEXT (RAG)                               |
|   - Knowledge Base: CIS Kubernetes/Docker Benchmarks, OWASP Top 10, DevSecOps Rubrics            |
|   - Hybrid Search: Dense embeddings (ChromaDB/MiniLM) + BM25 Sparse Search combined via RRF       |
|   - Cross-Encoder Reranker: MS-MARCO MiniLM re-scoring to eliminate irrelevant chunks             |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|                              LAYER 1: FOUNDATION MODELS & ROUTING GATEWAY                         |
|   - Multi-Provider LLM Factory: Google Gemini 2.0 Flash (Free), Groq (Free), Ollama, Claude, OpenAI|
|   - Dynamic Task-Aware Router: Cheap/fast models for extraction; reasoning models for remediation |
|   - Resilient Fallback Chaining: Automated failover on HTTP 429 rate-limiting                     |
+---------------------------------------------------------------------------------------------------+
```

---

## Directory Structure Plan

```
D:\tools\ai-engineering\
|-- .github/
|   `-- workflows/
|       |-- ci.yaml                  # Lint, type check, unit tests, security audit
|       `-- evals.yaml               # Promptfoo & Ragas automated evaluation workflow
|-- docs/                            # Comprehensive 10-part documentation manual
|   |-- 01-ai-engineering-vs-mlops.md
|   |-- 02-architecture-and-the-7-layers.md
|   |-- 03-agentic-orchestration-langgraph.md
|   |-- 04-production-rag-hybrid-and-rerank.md
|   |-- 05-structured-outputs-instructor.md
|   |-- 06-guardrails-and-ai-security.md
|   |-- 07-observability-langfuse.md
|   |-- 08-evals-and-prompt-ci.md
|   |-- 09-model-context-protocol-mcp.md
|   `-- 10-getting-started-and-walkthrough.md
|-- data/
|   `-- knowledge/                   # Markdown & JSON security standards for RAG
|       |-- cis_benchmarks.md
|       |-- owasp_top10_devsecops.md
|       `-- pipeline_security_rubrics.json
|-- evals/                           # Evaluation-Driven Development suite
|   |-- datasets/                    # Golden test query & expected response pairs
|   |   `-- golden_security_evals.json
|   |-- promptfoo.yaml               # Promptfoo test suite definition
|   `-- ragas_eval.py                # Ragas metrics calculator (Faithfulness, Relevancy)
|-- src/
|   |-- __init__.py
|   |-- agent/                       # Layer 4: LangGraph state machine & nodes
|   |   |-- __init__.py
|   |   |-- state.py                 # Graph state schema (TypedDict + Reducers)
|   |   |-- graph.py                 # Cyclic StateGraph assembly & checkpointing
|   |   `-- nodes/
|   |       |-- ingest_repos.py      # Codebase scanning node
|   |       |-- ingest_tools.py      # SonarQube & DefectDojo ingest node
|   |       |-- rag_enrichment.py    # Hybrid RAG security context injection
|   |       |-- evaluate_rubric.py   # Security baseline evaluation node
|   |       |-- reason.py            # LLM reasoning & gap prioritization node
|   |       |-- human_approval.py    # Human-in-the-loop interrupt gate
|   |       `-- report.py            # Final report synthesizer node
|   |-- extraction/                  # Layer 3: Instructor & structured output
|   |   |-- __init__.py
|   |   |-- extractor.py             # Instructor client wrapper with auto-retry
|   |   `-- schemas.py               # Pydantic v2 domain models
|   |-- gateway/                     # Layer 1: Model routing & fallback gateway
|   |   |-- __init__.py
|   |   |-- factory.py               # Multi-provider LLM factory
|   |   `-- router.py                # Cost & task-aware routing with fallbacks
|   |-- guardrails/                  # Layer 5: AI security & input/output rails
|   |   |-- __init__.py
|   |   |-- injection.py             # Prompt injection & jailbreak detection
|   |   |-- privacy.py               # PII & Secret masking before LLM
|   |   `-- grounding.py             # Output citation & hallucination verification
|   |-- mcp/                         # Layer 4 (Protocols): Model Context Protocol
|   |   |-- __init__.py
|   |   |-- server.py                # Standard MCP server exposing security tools
|   |   `-- tools.py                 # Tool handlers (scan_repo, get_cve_details)
|   |-- observability/               # Layer 6: Langfuse & Prometheus telemetry
|   |   |-- __init__.py
|   |   |-- tracing.py               # Langfuse client & OTel tracer
|   |   `-- metrics.py               # Prometheus metrics exporter
|   |-- rag/                         # Layer 2: Production Hybrid RAG & Reranker
|   |   |-- __init__.py
|   |   |-- store.py                 # ChromaDB / Qdrant interface
|   |   |-- retriever.py             # Dense Vector + BM25 Hybrid Search (RRF)
|   |   `-- reranker.py              # Cross-Encoder precision reranker
|   `-- clients/                     # External API integrations
|       |-- defectdojo.py
|       `-- sonarqube.py
|-- tests/
|   |-- unit/                        # Layer-by-layer fast unit tests
|   |   |-- test_gateway.py
|   |   |-- test_rag_hybrid.py
|   |   |-- test_extraction.py
|   |   |-- test_guardrails.py
|   |   `-- test_graph.py
|   `-- integration/                 # End-to-end dry run tests
|       `-- test_agent_e2e.py
|-- main.py                          # CLI application entrypoint
|-- pyproject.toml                   # Project metadata & tool settings
|-- requirements.txt                 # Pinned dependencies
`-- README.md                        # Master project guide
```

---

## Phased Implementation Plan

- [ ] **Phase 1: Architecture & Educational Documentation (`docs/`)**
  - Author complete 10-part documentation manual explaining how every layer works, why it is needed, and code examples.
- [ ] **Phase 2: Layer 1 & 3 - Gateway, Multi-LLM Factory & Structured Extraction**
  - Implement `src/gateway/` (factory + cost-aware router with Gemini 2.0 Flash, Groq, Ollama, Claude, OpenAI).
  - Implement `src/extraction/` using Pydantic v2 schemas and Instructor with retry logic.
- [ ] **Phase 3: Layer 2 - Production Hybrid RAG & Cross-Encoder Reranking**
  - Create standard security knowledge base in `data/knowledge/` (CIS, OWASP).
  - Implement ChromaDB vector store + BM25 keyword search combined via Reciprocal Rank Fusion (RRF).
  - Implement cross-encoder reranker for chunk relevance scoring.
- [ ] **Phase 4: Layer 5 - Defense-in-Depth Guardrails**
  - Implement prompt injection detection, PII/secret scrubbing, and hallucination grounding checks.
- [ ] **Phase 5: Layer 4 - Cyclic LangGraph State Machine & MCP Protocol**
  - Upgrade `AgentState` with memory, rich findings, and RAG context.
  - Assemble cyclic StateGraph with conditional edges and Human-in-the-Loop approval gate.
  - Implement Model Context Protocol (MCP) server exposing tools and resources.
- [ ] **Phase 6: Layer 6 & 7 - Observability & Automated Evals**
  - Configure Langfuse nested tracing and Prometheus metrics exporter.
  - Build Ragas RAG evaluation script and Promptfoo CI regression configuration.
- [ ] **Phase 7: CLI Integration, Unit Tests & End-to-End Verification**
  - Update `main.py` CLI supporting all layers, update `pyproject.toml` and `requirements.txt`.
  - Author comprehensive pytest test suite across all 7 layers.
