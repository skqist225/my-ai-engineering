"""Layer 1: Multi-Provider LLM Factory."""

import os
from enum import Enum
from typing import Any
from langchain_core.language_models.chat_models import BaseChatModel


class ModelProvider(str, Enum):
    """Supported LLM Providers."""
    GEMINI = "gemini"
    GROQ = "groq"
    OLLAMA = "ollama"
    CLAUDE = "claude"
    OPENAI = "openai"


def get_llm_client(
    provider: str | ModelProvider | None = None,
    model_name: str | None = None,
    temperature: float = 0.1,
) -> BaseChatModel:
    """Instantiate and return a LangChain ChatModel based on provider selection.

    Args:
        provider: Name of provider (gemini, groq, ollama, claude, openai).
                  Defaults to LLM_PROVIDER env variable or 'gemini'.
        model_name: Specific model identifier. If None, uses provider default.
        temperature: Sampling temperature (default 0.1 for deterministic security analysis).

    Returns:
        Configured BaseChatModel instance.
    """
    if provider is None:
        provider = os.environ.get("LLM_PROVIDER", ModelProvider.GEMINI.value).lower()
    elif isinstance(provider, ModelProvider):
        provider = provider.value.lower()

    if provider == ModelProvider.GEMINI.value:
        from langchain_google_genai import ChatGoogleGenerativeAI

        api_key = os.environ["GEMINI_API_KEY"]
        model = model_name or "gemini-2.0-flash"
        return ChatGoogleGenerativeAI(
            model=model,
            google_api_key=api_key,
            temperature=temperature,
        )

    if provider == ModelProvider.GROQ.value:
        from langchain_community.chat_models import ChatGroq

        api_key = os.environ["GROQ_API_KEY"]
        model = model_name or "llama-3.3-70b-versatile"
        return ChatGroq(
            model_name=model,
            groq_api_key=api_key,
            temperature=temperature,
        )

    if provider == ModelProvider.OLLAMA.value:
        from langchain_community.chat_models import ChatOllama

        base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        model = model_name or os.environ.get("OLLAMA_MODEL", "llama3.2:3b")
        return ChatOllama(
            base_url=base_url,
            model=model,
            temperature=temperature,
        )

    if provider == ModelProvider.CLAUDE.value:
        from langchain_anthropic import ChatAnthropic

        api_key = os.environ["ANTHROPIC_API_KEY"]
        model = model_name or "claude-3-7-sonnet-20250219"
        return ChatAnthropic(
            model=model,
            anthropic_api_key=api_key,
            temperature=temperature,
        )

    if provider == ModelProvider.OPENAI.value:
        from langchain_openai import ChatOpenAI

        api_key = os.environ["OPENAI_API_KEY"]
        model = model_name or "gpt-4o"
        return ChatOpenAI(
            model=model,
            openai_api_key=api_key,
            temperature=temperature,
        )

    raise ValueError(f"[ERROR] Unsupported LLM provider '{provider}'. Choose from: {[p.value for p in ModelProvider]}")
