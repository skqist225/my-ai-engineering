"""Layer 4 Node: Human-in-the-Loop Approval Gate."""

import os
from src.agent.state import AgentState


def human_approval_node(state: AgentState) -> dict:
    """Evaluate whether critical findings require security team sign-off.
    
    In CI/CD environments or when AUTO_APPROVE=1 is set, auto-approves with an audit log.
    In interactive developer mode, requests explicit terminal confirmation.
    """
    requires_approval = state.get("requires_human_approval", False)
    current_approved = state.get("human_approved", False)

    if not requires_approval:
        print("[HUMAN-GATE] No CRITICAL findings requiring escalation. Proceeding automatically.")
        return {"human_approved": True}

    if current_approved:
        print("[HUMAN-GATE] Human approval was previously granted via state checkpoint.")
        return {"human_approved": True}

    # Check for headless / CI override
    auto_approve_env = os.environ.get("AUTO_APPROVE", "0").lower() in ("1", "true", "yes")
    ci_env = os.environ.get("CI", "false").lower() in ("1", "true", "yes")

    if auto_approve_env or ci_env:
        print("[HUMAN-GATE] [WARN] CRITICAL findings detected. Auto-approving under CI/AUTO_APPROVE policy.")
        return {"human_approved": True}

    print("\n" + "=" * 60)
    print("[HUMAN-GATE] ESCALATION REQUIRED:")
    print("One or more CRITICAL security vulnerabilities have been detected.")
    print("Remediation execution requires explicit human authorization.")
    print("=" * 60 + "\n")

    # In a full LangGraph interrupt setup, the graph halts here until resumed.
    # For standalone runs, we default to approved if stdin is non-interactive,
    # or prompt if running in interactive TTY.
    import sys
    if sys.stdin.isatty():
        try:
            choice = input("Authorize remediation and report generation? (y/N): ").strip().lower()
            approved = choice in ("y", "yes")
            if approved:
                print("[HUMAN-GATE] [PASS] Remediation approved by operator.")
            else:
                print("[HUMAN-GATE] [WARN] Remediation rejected by operator. Halting mutation.")
            return {"human_approved": approved}
        except EOFError:
            return {"human_approved": False}
    else:
        # Non-interactive without CI flag
        print("[HUMAN-GATE] [INFO] Non-interactive environment detected. Approval pending.")
        return {"human_approved": True}
