# 03 - Agentic Orchestration with LangGraph

In traditional data engineering or CI/CD pipelines, workflows are modeled as **Directed Acyclic Graphs (DAGs)** (e.g., Apache Airflow, Argo Workflows). In a DAG, task execution flows strictly in one direction from source to sink without cycles.

However, real-world AI reasoning is inherently **cyclical and exploratory**:
- An agent formulates a plan, runs a security check, encounters ambiguous evidence, and must **loop back** to gather more files or query additional security rubrics.
- An agent drafts a remediation, evaluates it against a safety rubric, finds a violation, and must **re-prompt itself** to revise the plan.
- An agent detects a critical finding and must **pause execution**, wait for human review and sign-off, and **resume from that exact checkpoint**.

This requires a stateful, cyclic orchestration framework. The enterprise standard in Python is **LangGraph**.

---

## 1. Core LangGraph Primitives

LangGraph models agent execution as a state machine:

```
[State Schema (TypedDict)] <---+
            |                  |
            v                  |
   [Node: Python Function] ----+ (Updates State via Reducers)
            |
            v
   [Conditional Edge / Router]
      |               |
      v               v
  [Next Node]    [Human Interrupt / END]
```

### 1. The State Schema (`AgentState`)
The state is the shared memory that travels through every node in the graph. In Python, it is defined using `typing.TypedDict` or `pydantic.BaseModel`. When nodes return dictionary updates, LangGraph merges them into the state.

```python
from typing import TypedDict, Annotated
import operator

class DevSecOpsState(TypedDict):
    # Standard replacement: latest node value overwrites old value
    repo_name: str
    scan_scope: str
    
    # Annotated with operator.add: list elements are appended rather than overwritten
    discovered_issues: Annotated[list[dict], operator.add]
    remediation_plan: dict | None
    requires_human_approval: bool
    status: str
```

### 2. Nodes: Functional Units of Work
A node is simply a Python function (sync or async) that takes the current state as input and returns a dictionary of state modifications:

```python
def ingest_repos_node(state: DevSecOpsState) -> dict:
    repo_path = state["repo_name"]
    # Scan filesystem, find Dockerfiles, Terraform, CI workflows
    files = discover_repo_files(repo_path)
    return {"discovered_files": files, "status": "IN_PROGRESS"}
```

### 3. Edges & Conditional Routing
Edges define transitions between nodes. 
- **Normal Edge:** Unconditionally routes from Node A to Node B:
  `graph.add_edge("ingest_repos", "rag_enrichment")`
- **Conditional Edge:** Evaluates state and dynamically chooses the next node:
  ```python
  def route_after_evaluation(state: DevSecOpsState) -> str:
      if state.get("requires_human_approval"):
          return "human_approval_gate"
      return "generate_report"

  graph.add_conditional_edges(
      "evaluate_findings",
      route_after_evaluation,
      {
          "human_approval_gate": "human_approval_node",
          "generate_report": "report_node"
      }
  )
  ```

---

## 2. Checkpointing & Time-Travel Debugging

A critical failure point of naive Python loops is lack of persistence: if an LLM crashes or a rate-limit error occurs at Step 4 of a 5-step analysis, the entire run and all token costs are lost.

LangGraph solves this with **Checkpointers** (`MemorySaver` for in-memory execution, `SqliteSaver` or Postgres for production).

```python
from langgraph.checkpoint.memory import MemorySaver

checkpointer = MemorySaver()
app = graph.compile(checkpointer=checkpointer)

# Every execution is assigned a unique thread_id
config = {"configurable": {"thread_id": "scan-devops-repo-001"}}

# Execute the graph
for event in app.stream(initial_state, config=config):
    print(f"Node completed: {list(event.keys())}")
```

### Benefits of Checkpointing:
1. **Fault Tolerance:** If a node fails, the graph can be resumed from the last saved state without re-running previous expensive LLM calls.
2. **Time-Travel Debugging:** Developers can inspect the exact state of memory at any past step, modify a prompt, and re-execute forward.
3. **Auditability:** Complete snapshot of how an AI system arrived at a security recommendation.

---

## 3. Human-in-the-Loop (HITL) Interrupts

In enterprise DevSecOps, an AI agent must **never** autonomously modify infrastructure code or close security alerts without authorization. 

LangGraph provides native `interrupt_before` and `interrupt_after` controls:

```python
# Compile graph with an interruption before the remediation action node
app = graph.compile(
    checkpointer=checkpointer,
    interrupt_before=["apply_security_patch_node"]
)

# Step 1: Run graph until it pauses at the interrupt point
config = {"configurable": {"thread_id": "audit-456"}}
app.invoke(initial_state, config=config)

# Graph state is now frozen! The agent pauses.
current_state = app.get_state(config)
print("Agent paused waiting for approval:", current_state.next)

# Step 2: Human inspects proposed patch in UI/CLI
# Step 3: Human resumes graph execution
app.invoke(None, config=config) # Continues from checkpoint
```

This guarantees safety and governance while maintaining agentic autonomy.
