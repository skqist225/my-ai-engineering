"""DevSecOps AI Advisor Agent - Production 7-Layer AI Engineering Platform Entrypoint."""

import argparse
import os
import sys
import uuid
from pathlib import Path
from dotenv import load_dotenv


def main():
    parser = argparse.ArgumentParser(
        description="DevSecOps AI Advisor - 7-Layer Production AI Engineering Platform"
    )
    parser.add_argument(
        "--repos-dir", default="D:\\repos\\devops",
        help="Directory containing target DevOps repositories (default: D:\\repos\\devops)"
    )
    parser.add_argument(
        "--scope", default="all",
        help="'all' to scan all repos, or a specific repo name (e.g. 'jenkins-shared-lib')"
    )
    parser.add_argument(
        "--provider", default=os.environ.get("LLM_PROVIDER", "gemini"),
        choices=["gemini", "groq", "ollama", "claude", "openai"],
        help="Target LLM provider (default: gemini)"
    )
    parser.add_argument(
        "--output-dir", default="./reports",
        help="Directory for generated Markdown and step summary reports (default: ./reports)"
    )
    parser.add_argument(
        "--serve-mcp", action="store_true",
        help="Launch the Model Context Protocol (MCP) server over stdio"
    )
    parser.add_argument(
        "--run-evals", action="store_true",
        help="Execute the automated RAG Triad benchmark suite"
    )
    args = parser.parse_args()

    # Load environment variables
    env_path = Path(__file__).resolve().parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)

    # 1. Option: Model Context Protocol Server
    if args.serve_mcp:
        print("[INFO] Launching DevSecOps AI FastMCP Server...")
        from src.mcp.server import run_server
        run_server()
        return

    # 2. Option: Run Evals
    if args.run_evals:
        print("[INFO] Executing automated RAG Triad benchmarks...")
        from evals.ragas_eval import evaluate_rag_triad
        evaluate_rag_triad()
        return

    # 3. Standard Pipeline Run
    repos_dir = Path(args.repos_dir)
    if not repos_dir.exists():
        print(f"[ERROR] Repositories directory not found: {repos_dir}", file=sys.stderr)
        sys.exit(1)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 65)
    print("  DevSecOps AI Advisor - AI Engineering Multi-Layer Pipeline")
    print(f"  [CONFIG] Provider:   {args.provider}")
    print(f"  [CONFIG] Target Dir: {args.repos_dir}")
    print(f"  [CONFIG] Scope:      {args.scope}")
    print(f"  [CONFIG] Output:     {args.output_dir}")
    print("=" * 65)

    from src.agent.graph import build_devsecops_graph
    from src.observability.tracing import langfuse_trace

    agent = build_devsecops_graph(enable_checkpointing=True)
    session_id = f"audit-{uuid.uuid4().hex[:8]}"

    initial_state = {
        "repos_dir": str(repos_dir),
        "scope": args.scope,
        "output_dir": str(output_dir),
        "provider": args.provider,
        "repo_files": {},
        "file_contents": {},
        "retrieved_context": [],
        "tool_findings": {},
        "rubric_results": {},
        "findings": [],
        "remediation_summary": "",
        "requires_human_approval": False,
        "human_approved": False,
        "report_path": None,
        "execution_metrics": {},
    }

    config = {"configurable": {"thread_id": session_id}}

    with langfuse_trace(session_id=session_id) as callbacks:
        if callbacks:
            config["callbacks"] = callbacks
        result = agent.invoke(initial_state, config=config)

    print("\n" + "=" * 65)
    report_path = result.get("report_path", "unknown")
    print(f"  [SUCCESS] Audit completed successfully.")
    print(f"  [OUTPUT]  Report: {report_path}")
    print("=" * 65)


if __name__ == "__main__":
    main()
