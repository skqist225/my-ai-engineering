"""Layer 1: Cost-Aware Dynamic Routing Gateway."""

import time
import logging
from enum import Enum
from typing import Any
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage

from src.gateway.factory import get_llm_client, ModelProvider

logger = logging.getLogger(__name__)


class TaskComplexity(str, Enum):
    """Task complexity tier for intelligent model routing."""
    FAST = "fast"          # Syntax check, categorization, summarization
    BALANCED = "balanced"  # Standard security analysis, RAG synthesis
    COMPLEX = "complex"    # Deep vulnerability root-cause reasoning, architectural redesign


class GatewayRouter:
    """Intelligent Model Router with task-aware selection and fallback resilience."""

    def __init__(
        self,
        primary_provider: ModelProvider | str = ModelProvider.GEMINI,
        fallback_provider: ModelProvider | str = ModelProvider.GROQ,
    ) -> None:
        self.primary_provider = ModelProvider(primary_provider) if isinstance(primary_provider, str) else primary_provider
        self.fallback_provider = ModelProvider(fallback_provider) if isinstance(fallback_provider, str) else fallback_provider

    def get_model_for_task(self, complexity: TaskComplexity) -> BaseChatModel:
        """Route to appropriate model based on task complexity tier."""
        if complexity == TaskComplexity.FAST:
            # Fast, low-cost extraction
            return get_llm_client(self.primary_provider, temperature=0.0)

        if complexity == TaskComplexity.COMPLEX:
            # High-capability reasoning model
            return get_llm_client(self.primary_provider, temperature=0.2)

        # Default balanced tier
        return get_llm_client(self.primary_provider, temperature=0.1)

    def execute_with_fallback(
        self,
        messages: list[BaseMessage] | list[dict[str, str]],
        complexity: TaskComplexity = TaskComplexity.BALANCED,
    ) -> tuple[Any, dict[str, Any]]:
        """Execute chat completion with automatic fallback chaining on failure.

        Returns:
            Tuple of (response, execution_metadata)
        """
        start_time = time.perf_counter()
        metadata: dict[str, Any] = {
            "complexity": complexity.value,
            "provider_used": self.primary_provider.value,
            "fallback_triggered": False,
        }

        try:
            model = self.get_model_for_task(complexity)
            response = model.invoke(messages)
            metadata["latency_seconds"] = round(time.perf_counter() - start_time, 3)
            return response, metadata

        except Exception as exc:
            logger.warning("[WARN] Primary provider %s failed (%s). Triggering fallback to %s",
                           self.primary_provider.value, str(exc), self.fallback_provider.value)
            metadata["fallback_triggered"] = True
            metadata["provider_used"] = self.fallback_provider.value
            metadata["primary_error"] = str(exc)

            fallback_model = get_llm_client(self.fallback_provider, temperature=0.1)
            response = fallback_model.invoke(messages)
            metadata["latency_seconds"] = round(time.perf_counter() - start_time, 3)
            return response, metadata
