# 01 - AI Engineering vs MLOps: The Mental Model

If you come from a DevOps or software engineering background, the terms **Data Scientist**, **ML Engineer**, **MLOps Engineer**, and **AI Engineer** can easily blur together. However, in modern technology organizations (2025+), they represent distinct specializations with different daily deliverables, tools, and objectives.

---

## 1. Role Comparison at a Glance

| Dimension | ML Researcher | MLOps / Platform Engineer | AI Engineer |
|---|---|---|---|
| **Primary Goal** | Invent new model weights & architectures | Build resilient compute infrastructure & delivery pipelines | Build software applications powered by foundation models |
| **Deliverable** | Model weights (`.pt`, `.safetensors`), papers | Kubernetes clusters, Triton/vLLM engines, CI/CD, registries | Compound AI systems: Agents, RAG, APIs, structured pipelines |
| **Key Mindset** | Mathematics, linear algebra, loss functions | Reliability, latency, GPU scheduling, cost, GitOps | Application architecture, context management, prompt evals, UX |
| **Typical Tools** | PyTorch, JAX, CUDA, Deepspeed, Weights & Biases | Kubernetes, Kueue, Ray, Triton, KServe, Argo CD, Terraform | LangGraph, Instructor, Pydantic, Qdrant/ChromaDB, Langfuse, MCP |
| **Core Problem Solved** | "Can a neural network learn this complex pattern?" | "Can we serve 10,000 req/s reliably at low cost?" | "How do we make an LLM solve a business workflow accurately?" |

---

## 2. The Production Evolution: From Raw Weights to Compound Systems

### The Classical ML & MLOps World (Track 1 & Track 2 in `my-mlops`)
In classic ML and MLOps:
1. You gather historical data (Kafka, Spark, Data Lake).
2. You engineer features and store them in a feature store (Feast).
3. You train model weights (PyTorch, XGBoost, or LoRA fine-tuning with Ray).
4. You package and serve those weights behind an inference server (Triton, vLLM).
5. You monitor data drift (Evidently) and retrain when accuracy drops.

The primary unit of delivery is **the model artifact** (`model.onnx`, `adapter_model.safetensors`).

### The AI Engineering World (`ai-engineering`)
An AI Engineer starts from a foundation model that **already possesses broad reasoning capabilities** (e.g., Claude 3.7, GPT-4o, Gemini 2.0 Flash, DeepSeek R1). 

However, a raw foundation model alone cannot solve business problems because:
- It lacks your private company data (requires **RAG**).
- It cannot execute actions or query databases (requires **Tool Calling & MCP**).
- It produces free-form text that breaks backend APIs (requires **Structured Extraction / Pydantic**).
- It can hallucinate or be tricked by adversarial users (requires **Guardrails**).
- Multi-step tasks fail when executed in a single prompt (requires **Agentic State Machines / LangGraph**).
- You cannot tell if a prompt edit broke existing behaviors (requires **Evals**).

The primary unit of delivery in AI Engineering is **the Compound AI System**: an orchestrated loop of retrieval, reasoning, tools, and validation.

```
Classic MLOps Pipeline:
Data -> Features -> Training -> Model Registry -> Serving Engine (Triton/vLLM) -> Monitoring

AI Engineering System:
User Goal -> Guardrails -> Context/RAG -> LLM Reasoning -> Structured Output -> Tools/Actions -> Verification -> Response
                               ^                                  |
                               +----------- Feedback Loop --------+
```

---

## 3. Why Your DevOps Background Gives You an Unfair Advantage

Many software developers entering AI Engineering struggle because they treat LLMs as deterministic black boxes or build fragile prototypes that crash in production. 

As a DevOps engineer, you already possess the critical disciplines:

1. **Failure is Inevitable:** In DevOps, networks partition, pods crash, and disks fill up. In AI Engineering, models hallucinate, providers rate-limit with HTTP 429, and user prompts attempt injections. You are already conditioned to design **fallbacks, retries, and circuit breakers**.
2. **Infrastructure as Code -> Prompt as Code:** Prompts are configuration files with massive operational impact. You understand versioning, branch strategies, and pull requests.
3. **Automated Testing & CI/CD:** You know that untested code does not ship. In AI Engineering, you apply the same rigor to **Evals**: running automated regression suites (Promptfoo / DeepEval) in GitHub Actions before any prompt or model version changes.
4. **Observability & Cost Control:** LLM APIs charge per token. A runaway while-loop in an agent can cost thousands of dollars overnight. Your background in Prometheus, metrics, tracing, and rate-limiting is essential for deploying **LiteLLM proxies** and **Langfuse tracing**.

---

## 4. The 7-Layer Mastery Path in this Repository

To build a production-grade AI Engineering system, you will master 7 layers:
1. **Layer 1: Foundation Models & Dynamic Gateway** (Gemini 2.0, Groq, Ollama, Claude, task routing).
2. **Layer 2: Production Hybrid RAG** (Dense Vector + BM25 keyword search via Reciprocal Rank Fusion + Cross-Encoder reranking).
3. **Layer 3: Structured Outputs** (Instructor + Pydantic v2 validation loops).
4. **Layer 4: Agentic Orchestration & Protocols** (LangGraph state machines + Model Context Protocol).
5. **Layer 5: Defense-in-Depth Guardrails** (Prompt injection detection, PII scrubbing, grounding checks).
6. **Layer 6: Observability & Telemetry** (Langfuse distributed tracing + Prometheus metrics).
7. **Layer 7: Automated Evals in CI/CD** (Ragas RAG triad + Promptfoo regression testing).
