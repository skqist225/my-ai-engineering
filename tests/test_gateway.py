"""Unit tests for Layer 1: Foundation Models & Gateway Router."""

import pytest
from unittest.mock import MagicMock, patch
from src.gateway.factory import LLMFactory
from src.gateway.router import GatewayRouter, TaskComplexity


def test_router_classifies_complexity():
    router = GatewayRouter(primary_provider="gemini")

    fast_task = router.classify_task("Scrub secrets from this file")
    assert fast_task == TaskComplexity.FAST

    balanced_task = router.classify_task("Extract structured findings from rubric results")
    assert balanced_task == TaskComplexity.BALANCED

    complex_task = router.classify_task("Synthesize architectural remediation for distributed Kubernetes deployment")
    assert complex_task == TaskComplexity.COMPLEX


def test_factory_creates_ollama_model():
    with patch("langchain_community.chat_models.ChatOllama") as mock_ollama:
        mock_instance = MagicMock()
        mock_ollama.return_value = mock_instance

        llm = LLMFactory.create_llm(provider="ollama", model_name="qwen2.5-coder:7b", temperature=0.0)
        assert llm == mock_instance
        mock_ollama.assert_called_once()


def test_router_fallback_on_failure():
    router = GatewayRouter(primary_provider="gemini", fallback_providers=["groq", "ollama"])

    mock_llm_fail = MagicMock()
    mock_llm_fail.invoke.side_effect = RuntimeError("Rate limit exceeded on Gemini")

    mock_llm_success = MagicMock()
    mock_llm_success.invoke.return_value = "Recovered response from Groq"

    with patch.object(LLMFactory, "create_llm", side_effect=[mock_llm_fail, mock_llm_success]):
        response = router.invoke_with_fallback("Analyze pipeline security")
        assert response == "Recovered response from Groq"
