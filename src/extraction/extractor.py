"""Layer 3: Instructor-based Structured Output Extractor with Self-Healing Retries."""

import os
import json
import logging
from typing import Type, TypeVar
from pydantic import BaseModel, ValidationError

from src.gateway.factory import ModelProvider, get_llm_client

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


class StructuredExtractor:
    """Extracts strictly-typed Pydantic domain models from LLM outputs with validation retries."""

    def __init__(
        self,
        provider: ModelProvider | str = ModelProvider.GEMINI,
        max_retries: int = 3,
    ) -> None:
        self.provider = ModelProvider(provider) if isinstance(provider, str) else provider
        self.max_retries = max_retries

    def extract(
        self,
        schema: Type[T],
        system_prompt: str,
        user_content: str,
    ) -> T:
        """Extract structured object of type `schema` using instructor or structured output.

        Implements self-correcting validation loop: if output fails validation, the error
        is sent back to the model for automated correction.
        """
        model = get_llm_client(self.provider, temperature=0.0)

        # Attempt extraction using LangChain's native with_structured_output
        structured_model = model.with_structured_output(schema)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                result = structured_model.invoke(messages)
                if isinstance(result, schema):
                    return result
                if isinstance(result, dict):
                    return schema.model_validate(result)
                raise ValueError(f"[ERROR] Output did not match expected schema {schema.__name__}: {result}")

            except (ValidationError, ValueError) as exc:
                last_error = exc
                logger.warning(
                    "[WARN] Structured extraction attempt %d/%d failed validation: %s",
                    attempt, self.max_retries, str(exc)
                )
                if attempt < self.max_retries:
                    # Append error feedback turn for self-healing
                    messages.append({
                        "role": "assistant",
                        "content": "I produced output that failed schema validation."
                    })
                    messages.append({
                        "role": "user",
                        "content": (
                            f"Your previous response failed validation with error:\n{str(exc)}\n"
                            f"Please correct the output to strictly conform to schema {schema.__name__}."
                        )
                    })

        raise RuntimeError(
            f"[FAILED] Structured extraction failed after {self.max_retries} retries. "
            f"Last error: {last_error}"
        )
