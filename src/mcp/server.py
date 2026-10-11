"""Layer 4: FastMCP Server Exposing DevSecOps Tools to IDEs and Agents."""

import sys
from typing import Any
from src.mcp.tools import scan_repository, query_cis_standards, evaluate_cve_policy

try:
    from mcp.server.fastmcp import FastMCP
    _MCP_AVAILABLE = True
except ImportError:
    FastMCP = None
    _MCP_AVAILABLE = False


def create_mcp_server():
    """Instantiate and register tools with FastMCP."""
    if not _MCP_AVAILABLE:
        return None

    mcp = FastMCP("DevSecOps AI Advisor")

    @mcp.tool()
    def mcp_scan_repository(repo_path: str) -> dict[str, Any]:
        """Scan a repository for hardcoded secrets and Kubernetes/Docker misconfigurations."""
        return scan_repository(repo_path)

    @mcp.tool()
    def mcp_query_cis_standards(query: str, top_k: int = 3) -> list[dict[str, Any]]:
        """Retrieve authoritative CIS Kubernetes/Docker and OWASP DevSecOps benchmarks."""
        return query_cis_standards(query=query, top_k=top_k)

    @mcp.tool()
    def mcp_evaluate_cve_policy(finding_type: str) -> dict[str, str]:
        """Fetch remediation SLAs and mandated architectural fixes for security violations."""
        return evaluate_cve_policy(finding_type)

    return mcp


def run_server():
    """Entrypoint to launch the FastMCP server over standard I/O."""
    if not _MCP_AVAILABLE:
        print("[ERROR] 'mcp' package is not installed.")
        print("[INFO] Run: pip install mcp to enable Model Context Protocol serving.")
        sys.exit(1)

    server = create_mcp_server()
    if server:
        print("[INFO] Starting DevSecOps FastMCP server on stdio transport...")
        server.run(transport="stdio")


if __name__ == "__main__":
    run_server()
