# DevSecOps AI Advisor - Production 7-Layer AI Engineering Platform

A production-grade, stateful AI Engineering system for DevSecOps governance, automated architecture compliance auditing, and continuous security intelligence. Built with cyclic LangGraph orchestration, Hybrid RAG (Dense + BM25 via Reciprocal Rank Fusion), self-healing Pydantic v2 structured outputs, defense-in-depth guardrails, FastMCP server support, distributed Langfuse tracing, and automated RAG Triad evaluation.

---

## 7-Layer Architecture Overview

```
========================================================================================
[LAYER 7] Automated Evals & Prompt CI/CD (Ragas RAG Triad, Promptfoo Regression Suite)
----------------------------------------------------------------------------------------
[LAYER 6] Observability & Telemetry (Langfuse Distributed Tracing, Prometheus Exporter)
----------------------------------------------------------------------------------------
[LAYER 5] Defense-in-Depth Guardrails (Injection Detection, Secret Scrubbing, Grounding)
----------------------------------------------------------------------------------------
[LAYER 4] Agentic Orchestration & MCP (Cyclic LangGraph, Checkpointing, FastMCP Server)
----------------------------------------------------------------------------------------
[LAYER 3] Structured Outputs & Extraction (Pydantic v2, Self-Healing Schema Validation)
----------------------------------------------------------------------------------------
[LAYER 2] Advanced Hybrid Retrieval (Dense Vector + BM25 Sparse via RRF + Cross-Encoder)
----------------------------------------------------------------------------------------
[LAYER 1] Foundation Models & Gateway (Dynamic Cost-Aware Router: Gemini, Groq, Ollama)
========================================================================================
```

| Layer | Component | Implementation Highlights |
|-------|-----------|---------------------------|
| **1. Gateway** | `src/gateway/` | Dynamic complexity routing (`FAST`, `BALANCED`, `COMPLEX`) with automated fallback chaining (Gemini -> Groq -> Ollama). |
| **2. Retrieval** | `src/rag/` | Dense ChromaDB semantic search + BM25 lexical keyword matching fused with Reciprocal Rank Fusion (RRF) and Cross-Encoder reranking. |
| **3. Structured Output** | `src/extraction/` | Pydantic v2 strict schemas (`SecurityAuditReport`, `SecurityFinding`, `Severity`) with self-healing retry validation loops. |
| **4. Orchestration** | `src/agent/` & `src/mcp/` | Stateful LangGraph pipeline with MemorySaver checkpointing, Human-in-the-Loop approval gate, and Model Context Protocol (FastMCP) server. |
| **5. Guardrails** | `src/guardrails/` | Inbound adversarial prompt injection detector, reversible regex credential scrubber (AWS/GitHub/JWT), and outbound grounding verification. |
| **6. Observability** | `src/observability/` | Distributed session tracing with Langfuse, latency tracking, token economics, and Prometheus metrics exposition. |
| **7. Evals & CI/CD** | `evals/` & `.github/` | Automated RAG Triad benchmarks (Context Precision, Faithfulness, Relevance) and GitHub Actions CI pipelines. |

---

## Comprehensive Documentation Suite (`docs/`)

Read the complete 10-chapter developer and architecture manual in `docs/`:

1. [01. AI Engineering vs MLOps: Paradigm Shift](docs/01-ai-engineering-vs-mlops.md)
2. [02. Platform Architecture & The 7 Production Layers](docs/02-architecture-and-the-7-layers.md)
3. [03. Stateful Agentic Orchestration with LangGraph](docs/03-agentic-orchestration-langgraph.md)
4. [04. Production Hybrid RAG & Cross-Encoder Reranking](docs/04-production-rag-hybrid-and-rerank.md)
5. [05. Structured Outputs & Self-Healing Extraction](docs/05-structured-outputs-instructor.md)
6. [06. Defense-in-Depth Guardrails & AI Safety](docs/06-guardrails-and-ai-security.md)
7. [07. Distributed Observability & Token Economics](docs/07-observability-langfuse.md)
8. [08. Automated Evaluation & Prompt CI/CD](docs/08-evals-and-prompt-ci.md)
9. [09. Model Context Protocol (MCP) Integration](docs/09-model-context-protocol-mcp.md)
10. [10. Developer Walkthrough & Operational Runbook](docs/10-getting-started-and-walkthrough.md)

---

## Quick Start

### 1. Environment Setup

```powershell
# Navigate to the repository
cd D:\tools\ai-engineering

# Activate Python virtual environment
.\.venv\Scripts\Activate.ps1

# Install project dependencies
pip install -r requirements.txt

# Configure your environment keys in .env
Copy-Item .env.example .env
```

### 2. Execution Modes

#### Standard Security Audit Pipeline
Scan repositories, evaluate rubrics, enrich with CIS standards, synthesize grounded findings, and generate Markdown reports:
```powershell
python main.py --repos-dir D:\repos\devops --scope all --provider gemini --output-dir ./reports
```

#### Launch FastMCP Server (Model Context Protocol)
Expose DevSecOps security auditing, CIS querying, and CVE policy tools to AI IDEs (Claude Desktop, Cursor):
```powershell
python main.py --serve-mcp
```

#### Run Automated RAG Triad Evaluation
Run regression testing on golden security benchmark cases to measure Context Precision, Faithfulness, and Relevance:
```powershell
python main.py --run-evals
```

---

## Repository Structure

```
ai-engineering/
|-- .github/workflows/         # CI/CD and automated prompt evaluation workflows
|   |-- ci.yaml                # Pytest unit tests, linting, and knowledge base check
|   `-- evals.yaml             # Scheduled RAG Triad benchmark execution
|-- data/knowledge/            # Authoritative CIS Benchmarks and OWASP guidelines
|   |-- cis_kubernetes_docker.md
|   |-- owasp_top10_devsecops.md
|   `-- pipeline_security_rubrics.json
|-- docs/                      # Complete 10-chapter technical guide
|-- evals/                     # Layer 7 Evaluation suite
|   |-- datasets/              # Golden benchmark security evaluation datasets
|   |-- promptfoo.yaml         # Prompt regression configuration
|   `-- ragas_eval.py          # RAG Triad scorer (Precision, Faithfulness, Relevance)
|-- reports/                   # Generated audit reports and executive summaries
|-- src/
|   |-- agent/                 # Layer 4 LangGraph orchestration
|   |   |-- graph.py           # StateGraph assembly, conditional routing, checkpointer
|   |   |-- state.py           # TypedDict AgentState schema
|   |   `-- nodes/             # Ingestion, RAG, Rubric, Reason, Gate, Report nodes
|   |-- clients/               # Integrations for DefectDojo and SonarQube
|   |-- extraction/            # Layer 3 Structured outputs & Pydantic v2 schemas
|   |   |-- extractor.py       # Self-healing retry extraction engine
|   |   `-- schemas.py         # SecurityAuditReport, SecurityFinding, Severity
|   |-- gateway/               # Layer 1 Foundation models & dynamic router
|   |   |-- factory.py         # Multi-provider LLM factory (Gemini, Groq, Ollama, etc.)
|   |   `-- router.py          # TaskComplexity classifier and fallback chaining
|   |-- guardrails/            # Layer 5 AI Safety and Defense-in-depth
|   |   |-- grounding.py       # Outbound citation & hallucination filter
|   |   |-- injection.py       # Inbound prompt injection detector
|   |   `-- privacy.py         # Credential scrubber (AWS, GitHub, JWT) & restorer
|   |-- mcp/                   # Layer 4 Model Context Protocol
|   |   |-- server.py          # FastMCP server registration
|   |   `-- tools.py           # Repository scan, CIS query, CVE policy tools
|   |-- observability/         # Layer 6 Telemetry & Tracing
|   |   |-- metrics.py         # Prometheus counters, latency histograms, token tracking
|   |   `-- tracing.py         # Distributed Langfuse tracing integration
|   |-- prompts/               # System prompts and extraction templates
|   |   `-- system.py
|   |-- rag/                   # Layer 2 Hybrid RAG
|   |   |-- reranker.py        # Cross-Encoder candidate reranker
|   |   |-- retriever.py       # Dense + BM25 Reciprocal Rank Fusion (RRF)
|   |   `-- store.py           # Local ChromaDB vector store wrapper
|   `-- templates/             # Jinja2 audit report templates
|-- tests/                     # Comprehensive Pytest test suite
|   |-- test_clients.py
|   |-- test_evaluate_rubric.py
|   |-- test_extraction.py
|   |-- test_gateway.py
|   |-- test_graph.py
|   |-- test_guardrails.py
|   |-- test_ingest_repos.py
|   `-- test_rag_hybrid.py
|-- main.py                    # Unified CLI entrypoint
|-- requirements.txt           # Pinned production dependencies
`-- pyproject.toml             # Modern packaging metadata
```

---

## Verification & Testing

Execute the test suite across all 7 layers:
```powershell
python -m pytest tests/ -v
```

All modules follow clean code principles (SRP, KISS, YAGNI, fail-fast direct property access) and strict ASCII console output discipline.
