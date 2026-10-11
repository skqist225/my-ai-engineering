"""Layer 6: Prometheus Metrics & Token Economics Telemetry."""

import time
from typing import Any
from collections import defaultdict


class MetricsCollector:
    """Singleton telemetry collector tracking tokens, latencies, and security events."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MetricsCollector, cls).__new__(cls)
            cls._instance._counters = defaultdict(int)
            cls._instance._latencies = defaultdict(list)
        return cls._instance

    def record_llm_call(self, provider: str, model: str, status: str, latency_seconds: float, input_tokens: int = 0, output_tokens: int = 0):
        """Record an LLM API invocation."""
        key = f"llm_calls_total{{provider=\"{provider}\",model=\"{model}\",status=\"{status}\"}}"
        self._counters[key] += 1

        # Record tokens
        self._counters[f"llm_tokens_input_total{{provider=\"{provider}\"}}"] += input_tokens
        self._counters[f"llm_tokens_output_total{{provider=\"{provider}\"}}"] += output_tokens
        self._counters[f"llm_tokens_total{{provider=\"{provider}\"}}"] += (input_tokens + output_tokens)

        # Record latency
        self._latencies[f"llm_latency_seconds{{provider=\"{provider}\"}}"].append(latency_seconds)

    def record_guardrail_event(self, event_type: str, action: str):
        """Record a safety or security guardrail interception."""
        key = f"guardrail_events_total{{type=\"{event_type}\",action=\"{action}\"}}"
        self._counters[key] += 1

    def record_rag_query(self, strategy: str, chunks_retrieved: int):
        """Record a retrieval operation."""
        self._counters[f"rag_queries_total{{strategy=\"{strategy}\"}}"] += 1
        self._counters[f"rag_chunks_retrieved_total{{strategy=\"{strategy}\"}}"] += chunks_retrieved

    def get_summary(self) -> dict[str, Any]:
        """Export in-memory telemetry snapshot."""
        return {
            "counters": dict(self._counters),
            "latencies_count": {k: len(v) for k, v in self._latencies.items()},
            "average_latency_seconds": {
                k: round(sum(v) / len(v), 3) if v else 0.0 for k, v in self._latencies.items()
            },
        }

    def export_prometheus_text(self) -> str:
        """Render metrics in standard Prometheus exposition format."""
        lines = []
        lines.append("# HELP devsecops_counters Total metric counts across agents and LLM gateways")
        lines.append("# TYPE devsecops_counters counter")
        for key, val in sorted(self._counters.items()):
            lines.append(f"{key} {val}")

        for key, vals in sorted(self._latencies.items()):
            count = len(vals)
            total = sum(vals)
            lines.append(f"{key}_count {count}")
            lines.append(f"{key}_sum {round(total, 4)}")

        return "\n".join(lines) + "\n"


_global_metrics = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    """Return the global singleton metrics collector."""
    return _global_metrics
