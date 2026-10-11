# 10 - Getting Started and Local Walkthrough

This guide walks you through setting up and running the complete **7-Layer AI Engineering Platform** on Windows (PowerShell) **100% free**, using Google Gemini 2.0 Flash and Groq Cloud free tiers with local ChromaDB.

---

## 1. Prerequisites

1. **Python 3.12+** installed on your system.
2. **Free API Keys** (No credit card required):
   - **Google Gemini API Key:** Get free from [Google AI Studio](https://aistudio.google.com/).
   - **Groq API Key (Optional, for ultra-fast fallback):** Get free from [Groq Console](https://console.groq.com/).

---

## 2. Environment Setup

Open PowerShell in the project directory:

```powershell
cd D:\tools\ai-engineering

# 1. Activate or create virtual environment
if (-not (Test-Path .venv)) { python -m venv .venv }
.\.venv\Scripts\Activate.ps1

# 2. Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 3. Configure environment variables (.env)
if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
}
```

Open `.env` in your text editor and set your key:
```ini
LLM_PROVIDER=gemini
GEMINI_API_KEY="your-google-ai-studio-key-here"
GROQ_API_KEY="your-groq-key-optional"
LANGFUSE_PUBLIC_KEY="optional"
LANGFUSE_SECRET_KEY="optional"
LANGFUSE_HOST="https://cloud.langfuse.com"
```

---

## 3. Step-by-Step Hands-On Learning Flow

### Step 1: Run the Fast Offline Dry-Run (No LLM Required)
Test repository discovery and security rubric evaluation without making external API calls:

```powershell
python -m learning.dry_run
```
*What this teaches:* Demonstrates deterministic file parsing, detecting Dockerfiles, Kubernetes manifests, and Terraform files across `D:\repos\devops`.

---

### Step 2: Test Layer 2 (Hybrid RAG & Cross-Encoder Reranker)
Query the local security knowledge base (CIS Benchmarks & OWASP rules) using Dense + BM25 search with Reciprocal Rank Fusion:

```powershell
python -m src.rag.retriever --query "rules for running Docker containers as non-root user"
```
*What this teaches:* Inspect how Dense and BM25 candidate lists are merged by RRF and re-scored by the Cross-Encoder model.

---

### Step 3: Test Layer 3 & 5 (Guardrails & Structured Extraction)
Run an extraction that scrubs sensitive tokens, checks for prompt injection, and returns a verified Pydantic object:

```powershell
python -m src.extraction.extractor --input-sample "test_dockerfile"
```
*What this teaches:* See Instructor's self-healing validation loop in action if the model produces malformed fields.

---

### Step 4: Run the Complete LangGraph Agent
Execute the full stateful cyclic agent against a target repository:

```powershell
python main.py --repos-dir D:\repos\devops --scope infra-kubernetes --output-dir ./reports
```

*Execution Stages:*
1. **Ingest Repos:** Discovers infrastructure manifests.
2. **Ingest Tools:** Pulls findings from SonarQube / DefectDojo (or mock feeds).
3. **RAG Enrichment:** Pulls authoritative CIS guidelines for discovered files.
4. **Evaluate Rubric:** Assesses baseline compliance.
5. **Reason & Remediate:** Instructor-guided LLM generates prioritized recommendations.
6. **Guardrails:** Grounding check verifies evidence snippets.
7. **Report:** Synthesizes a structured Markdown security report in `./reports/`.

---

### Step 5: Run the Model Context Protocol (MCP) Server
Launch the MCP server to expose your DevSecOps tools to external AI agents:

```powershell
python -m src.mcp.server
```
*What this teaches:* Test your MCP server using the MCP Inspector or Claude Desktop.

---

### Step 6: Run Automated Evals & Unit Tests
Run the complete automated test suite across all 7 layers:

```powershell
pytest -v
```

Run Promptfoo prompt regression assertions:
```powershell
npx promptfoo@latest eval -c evals/promptfoo.yaml
```
