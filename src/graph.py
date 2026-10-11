"""Top-level LangGraph agent assembly - exposes build_devsecops_graph."""

from src.agent.graph import build_devsecops_graph

# Backward compatibility alias
build_agent_graph = build_devsecops_graph

__all__ = ["build_devsecops_graph", "build_agent_graph"]
