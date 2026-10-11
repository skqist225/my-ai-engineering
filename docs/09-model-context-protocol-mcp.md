# 09 - Model Context Protocol (MCP): The Universal Standard

Before late 2024, every AI framework and LLM provider implemented its own custom format for tool calling, external APIs, and document retrieval. 

If you wrote an integration for an internal PostgreSQL database or SonarQube server:
- You had to write one wrapper for LangChain.
- Another wrapper for LlamaIndex.
- Another wrapper for OpenAI function calling.
- Another wrapper for Claude Desktop or Cursor.

To solve this fragmentation, Anthropic introduced the **Model Context Protocol (MCP)**, an open-source standard for connecting AI systems to data sources and tools.

---

## 1. MCP Architecture: Client, Host, and Server

MCP follows a client-server architecture over standard JSON-RPC 2.0 (running via standard input/output `stdio` or HTTP with Server-Sent Events `SSE`):

```
+-------------------------------------------------------------------------+
|                                MCP HOST                                 |
|          (Cursor, Claude Desktop, Antigravity, Custom AI Agent)         |
|                                    |                                    |
|                             [MCP Client]                                |
+------------------------------------+------------------------------------+
                                     |
                         JSON-RPC (stdio / SSE)
                                     |
                                     v
+-------------------------------------------------------------------------+
|                               MCP SERVER                                |
|                        (D:\tools\ai-engineering)                         |
|                                                                         |
|   +-------------------+  +-------------------+  +-------------------+   |
|   |     RESOURCES     |  |       TOOLS       |  |      PROMPTS      |   |
|   |  - repo://files   |  |  - scan_repo      |  |  - security_audit |   |
|   |  - standards://cis|  |  - get_cve_info   |  |  - explain_fix    |   |
|   +-------------------+  +-------------------+  +-------------------+   |
+-------------------------------------------------------------------------+
```

### The Three MCP Primitives:
1. **Resources:** Read-only data endpoints provided to the model as context (e.g. `repo://infra-kubernetes/Dockerfile` or `standards://cis/k8s`).
2. **Tools:** Executable functions that the model can invoke to perform side effects or query dynamic systems (e.g. `scan_repository(path, scope)` or `lookup_cve(cve_id)`).
3. **Prompts:** Pre-packaged prompt templates exposed by the server to guide users through complex workflows.

---

## 2. Implementing an MCP Server in Python

Using the official `mcp` Python SDK (`pip install mcp`), creating an MCP server for our DevSecOps agent is concise and declarative:

```python
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

# Initialize FastMCP server
mcp = FastMCP("DevSecOps-Advisor-Server")

# Expose a Tool
@mcp.tool()
def scan_repository(repo_path: str, scope: str = "all") -> str:
    """Scan a local repository directory for DevSecOps coverage gaps and security flaws."""
    # Invokes the internal LangGraph pipeline
    from src.agent.graph import build_agent_graph
    app = build_agent_graph()
    result = app.invoke({"repos_dir": repo_path, "scope": scope})
    return f"Scan complete. Found {len(result['rubric_results'])} evaluated rubrics."

# Expose a Dynamic Resource
@mcp.resource("standards://cis/{topic}")
def get_cis_standard(topic: str) -> str:
    """Retrieve authoritative CIS benchmark rules for Kubernetes or Docker."""
    from src.rag.retriever import get_standard_content
    return get_standard_content(topic)

# Expose a Reusable Prompt
@mcp.prompt()
def security_audit_prompt(repo_name: str) -> str:
    """Generate a prompt to perform a full security audit on a repository."""
    return f"Please audit repository {repo_name} against CIS Kubernetes Benchmarks and OWASP Top 10."

if __name__ == "__main__":
    # Runs over stdio for local tools or SSE for remote deployments
    mcp.run()
```

---

## 3. How Other AI Systems Consume this Server

Because MCP is a recognized open standard, any MCP-compatible client can immediately discover and run your DevSecOps tools without code modification:

- **In Claude Desktop / Cursor:** Add to `mcpServers` configuration:
  ```json
  {
    "mcpServers": {
      "devsecops-advisor": {
        "command": "python",
        "args": ["-m", "src.mcp.server"],
        "cwd": "D:\\tools\\ai-engineering"
      }
    }
  }
  ```
- **In our custom LangGraph Agent:** The agent can dynamically connect to external MCP servers (e.g., GitHub MCP server, PostgreSQL MCP server) to fetch data without writing custom API clients.

MCP transforms internal scripts into **standardized, modular capabilities** for the entire AI ecosystem.
