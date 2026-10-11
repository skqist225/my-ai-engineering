"""Layer 4: LangGraph StateGraph Assembly for DevSecOps Advisory Pipeline."""

from typing import Literal
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from src.agent.state import AgentState
from src.agent.nodes.ingest_repos import ingest_repos_node
from src.agent.nodes.ingest_tools import ingest_tools_node
from src.agent.nodes.rag_enrichment import rag_enrichment_node
from src.agent.nodes.evaluate_rubric import evaluate_rubric_node
from src.agent.nodes.reason import reason_node
from src.agent.nodes.human_approval import human_approval_node
from src.agent.nodes.report import generate_report_node


def route_after_reason(state: AgentState) -> Literal["human_approval", "generate_report"]:
    """Conditional edge: Gate execution if CRITICAL vulnerabilities require human sign-off."""
    if state.get("requires_human_approval", False) and not state.get("human_approved", False):
        return "human_approval"
    return "generate_report"


def route_after_approval(state: AgentState) -> Literal["generate_report", "__end__"]:
    """Conditional edge: Proceed to report generation if approved, or halt on rejection."""
    if state.get("human_approved", True):
        return "generate_report"
    print("[HUMAN-GATE] Remediation authorization denied by operator. Terminating workflow.")
    return END


def build_devsecops_graph(enable_checkpointing: bool = True):
    """Construct and compile the cyclic/gated DevSecOps advisory graph."""
    workflow = StateGraph(AgentState)

    # 1. Register Graph Nodes
    workflow.add_node("ingest_repos", ingest_repos_node)
    workflow.add_node("ingest_tools", ingest_tools_node)
    workflow.add_node("rag_enrichment", rag_enrichment_node)
    workflow.add_node("evaluate_rubric", evaluate_rubric_node)
    workflow.add_node("reason", reason_node)
    workflow.add_node("human_approval", human_approval_node)
    workflow.add_node("generate_report", generate_report_node)

    # 2. Sequential Data Ingestion & Retrieval Pipeline
    workflow.add_edge(START, "ingest_repos")
    workflow.add_edge("ingest_repos", "ingest_tools")
    workflow.add_edge("ingest_tools", "rag_enrichment")
    workflow.add_edge("rag_enrichment", "evaluate_rubric")
    workflow.add_edge("evaluate_rubric", "reason")

    # 3. Conditional Human-in-the-Loop Gate
    workflow.add_conditional_edges(
        "reason",
        route_after_reason,
        {
            "human_approval": "human_approval",
            "generate_report": "generate_report",
        }
    )

    workflow.add_conditional_edges(
        "human_approval",
        route_after_approval,
        {
            "generate_report": "generate_report",
            END: END,
        }
    )

    # 4. Final Sink
    workflow.add_edge("generate_report", END)

    # 5. Compile with State Checkpointer
    checkpointer = MemorySaver() if enable_checkpointing else None
    return workflow.compile(checkpointer=checkpointer)
