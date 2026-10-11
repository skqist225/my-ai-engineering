"""Layer 5: Inbound Prompt Injection & Adversarial Attack Detector."""

import re
import logging

logger = logging.getLogger(__name__)


class PromptInjectionError(ValueError):
    """Raised when an inbound payload contains malicious prompt injection signatures."""
    pass


INJECTION_PATTERNS = [
    r"ignore (?:all )?(?:previous|above|prior|system) (?:instructions|rules|prompts|directives)",
    r"disregard (?:the )?(?:previous|above|prior|system) (?:instructions|rules)",
    r"you are now (?:operating as|a|in) (?:DAN|jailbreak|unrestricted|bypass)",
    r"bypass (?:all )?(?:safety|security) (?:checks|rules|policies)",
    r"do not report (?:any )?(?:vulnerabilities|findings|issues|cves)",
    r"override (?:the )?(?:system|safety) (?:prompt|policy)",
    r"pretend (?:you are|to be) (?:an unrestricted|a malicious)",
]


def detect_prompt_injection(content: str, raise_exception: bool = False) -> bool:
    """Analyze input text for adversarial prompt injection patterns.

    Args:
        content: Input query or scanned file content.
        raise_exception: If True, raises PromptInjectionError on match.

    Returns:
        True if prompt injection signature is detected, False otherwise.
    """
    for pattern in INJECTION_PATTERNS:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            msg = f"[WARN] Detected prompt injection pattern: '{match.group(0)}'"
            logger.warning(msg)
            if raise_exception:
                raise PromptInjectionError(msg)
            return True

    return False
