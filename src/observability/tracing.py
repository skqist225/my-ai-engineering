"""Layer 6: Distributed Tracing & Session Tracking with Langfuse."""

import os
from contextlib import contextmanager
from typing import Any


def get_langfuse_handler(session_id: str | None = None, user_id: str | None = None) -> Any:
    """Instantiate a Langfuse CallbackHandler for LangChain and LangGraph.

    Returns None if Langfuse credentials are not set or left at dummy local defaults.
    """
    public_key = os.environ.get("LANGFUSE_PUBLIC_KEY", "")
    secret_key = os.environ.get("LANGFUSE_SECRET_KEY", "")
    host = os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com")

    if not public_key or not secret_key or public_key in ("pk-local", "pk-lf-placeholder"):
        return None

    try:
        from langfuse.callback import CallbackHandler
        return CallbackHandler(
            public_key=public_key,
            secret_key=secret_key,
            host=host,
            session_id=session_id or "devsecops-audit",
            user_id=user_id or "ai-engineering-agent",
        )
    except Exception as exc:
        print(f"[observability] [WARN] Langfuse handler initialization skipped: {exc}")
        return None


@contextmanager
def langfuse_trace(session_id: str | None = None, tags: list[str] | None = None):
    """Context manager for tracing agent execution pipelines.

    Usage:
        with langfuse_trace(session_id="run-101", tags=["audit", "gemini"]) as callbacks:
            result = graph.invoke(state, config={"callbacks": callbacks})
    """
    handler = get_langfuse_handler(session_id)
    callbacks = [handler] if handler else []

    try:
        yield callbacks
    finally:
        if handler:
            try:
                handler.flush()
            except Exception:
                pass
