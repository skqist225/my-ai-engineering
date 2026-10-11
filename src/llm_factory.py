"""
Swappable LLM factory — change provider via LLM_PROVIDER env var.

Supports:
  - gemini   (default, free): Google Gemini 2.0 Flash via AI Studio
  - groq     (free):          Llama 3.3 70B / Qwen 2.5 Coder 32B
  - ollama   (free, local):   Any Ollama-served model on CPU
  - anthropic (paid):         Claude 3.5 Sonnet (upgrade path)
"""

import os
from langchain_core.language_models.chat_models import BaseChatModel


def get_chat_model(provider: str | None = None) -> BaseChatModel:
    """Return an initialized LLM based on provider selection.

    Args:
        provider: Override LLM_PROVIDER env var. If None, reads from env.

    Returns:
        A LangChain chat model ready for .invoke() calls.
    """
    provider = (provider or os.getenv("LLM_PROVIDER", "gemini")).lower()

    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=os.getenv("GEMINI_MODEL", "gemini-3.6-flash"),
            temperature=0,
            google_api_key=os.getenv("GOOGLE_API_KEY"),
        )

    elif provider == "groq":
        from langchain_groq import ChatGroq

        return ChatGroq(
            model_name=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            temperature=0,
            groq_api_key=os.getenv("GROQ_API_KEY"),
        )

    elif provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b"),
            temperature=0,
            base_url=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        )

    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest"),
            temperature=0,
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        )

    else:
        raise ValueError(
            f"Unsupported LLM_PROVIDER: '{provider}'. "
            f"Valid options: gemini, groq, ollama, anthropic"
        )
