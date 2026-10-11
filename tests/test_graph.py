"""Unit tests for Layer 4: LangGraph StateGraph & Conditional Routing."""

import pytest
from langgraph.graph import END
from src.agent.graph import (
    build_devsecops_graph,
    route_after_reason,
    route_after_approval,
)


def test_build_devsecops_graph_compiles():
    graph = build_devsecops_graph(enable_checkpointing=False)
    assert graph is not None
    # Verify graph node presence
    node_names = list(graph.nodes.keys())
    assert "ingest_repos" in node_names
    assert "reason" in node_names
    assert "human_approval" in node_names
    assert "generate_report" in node_names


def test_route_after_reason_routes_to_human_approval():
    state_requiring_approval = {
        "requires_human_approval": True,
        "human_approved": False,
    }
    next_node = route_after_reason(state_requiring_approval)
    assert next_node == "human_approval"


def test_route_after_reason_routes_directly_to_report():
    state_safe = {
        "requires_human_approval": False,
        "human_approved": False,
    }
    next_node = route_after_reason(state_safe)
    assert next_node == "generate_report"


def test_route_after_approval_routes_to_report_or_end():
    approved_state = {"human_approved": True}
    assert route_after_approval(approved_state) == "generate_report"

    rejected_state = {"human_approved": False}
    assert route_after_approval(rejected_state) == END
