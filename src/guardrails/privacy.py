"""Layer 5: Inbound Secret Scrubbing and PII Redactor."""

import re
from typing import NamedTuple


class RedactionResult(NamedTuple):
    redacted_text: str
    redactions_count: int
    secret_map: dict[str, str]  # placeholder -> original_secret


SECRET_REGEXES: dict[str, str] = {
    "AWS_ACCESS_KEY": r"(?i)\b(AKIA[0-9A-Z]{16})\b",
    "AWS_SECRET_KEY": r"(?i)(?:aws_secret_access_key|secret_key)\s*[:=]\s*['\"]?([A-Za-z0-9/\+=]{40})['\"]?",
    "GITHUB_TOKEN": r"\b(ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{82})\b",
    "JWT_TOKEN": r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b",
    "GENERIC_PASSWORD": r"(?i)(?:password|passwd|pwd|secret)\s*[:=]\s*['\"]([^'\"]{6,})['\"]",
}


def redact_secrets(text: str) -> RedactionResult:
    """Scan text and replace sensitive credentials with deterministic placeholders.

    Returns:
        RedactionResult containing the sanitized text, count of redactions, and mapping.
    """
    sanitized = text
    secret_map: dict[str, str] = {}
    counter = 0

    for secret_type, pattern in SECRET_REGEXES.items():
        for match in re.finditer(pattern, text):
            # Capture either group 1 or whole match
            secret_value = match.group(1) if match.lastindex else match.group(0)
            if secret_value not in secret_map.values():
                counter += 1
                placeholder = f"[REDACTED_{secret_type}_{counter}]"
                secret_map[placeholder] = secret_value
                sanitized = sanitized.replace(secret_value, placeholder)

    return RedactionResult(
        redacted_text=sanitized,
        redactions_count=len(secret_map),
        secret_map=secret_map,
    )


def restore_secrets(redacted_text: str, secret_map: dict[str, str]) -> str:
    """Restore placeholders back to original secrets locally if needed."""
    restored = redacted_text
    for placeholder, original in secret_map.items():
        restored = restored.replace(placeholder, original)
    return restored


# Compatibility aliases
scrub_sensitive_tokens = redact_secrets
restore_sensitive_tokens = restore_secrets

__all__ = [
    "RedactionResult",
    "redact_secrets",
    "restore_secrets",
    "scrub_sensitive_tokens",
    "restore_sensitive_tokens",
]

