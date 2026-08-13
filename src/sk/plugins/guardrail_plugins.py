"""Guardrail plugin for Semantic Kernel.

Checks agent outputs for PII, harmful content, and prompt injection
before they are returned to the user.
"""

import json
import re
from typing import Any, Dict

from semantic_kernel.functions import kernel_function


class GuardrailPlugin:
    """SK plugin for responsible AI guardrails."""

    _SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
    _EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
    _PHONE_PATTERN = re.compile(r"\b\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")

    _HARMFUL_KEYWORDS = [
        "hack",
        "exploit",
        "malware",
        "phishing",
        "ransomware",
        "steal data",
        "inject sql",
        "bypass security",
    ]

    def __init__(self) -> None:
        self.name = "GuardrailPlugin"

    @kernel_function(description="Check content for PII, harmful content, and prompt injection")
    def check_content(self, content: str, check_type: str = "all") -> str:
        """Check content for guardrail violations."""
        violations: list = []

        if check_type in ("pii", "all"):
            violations.extend(self._check_pii(content))

        if check_type in ("harmful", "all"):
            violations.extend(self._check_harmful(content))

        if check_type in ("injection", "all"):
            violations.extend(self._check_injection(content))

        passed = len(violations) == 0
        sanitized = self._redact(content) if not passed else content

        result: Dict[str, Any] = {
            "passed": passed,
            "violations": violations,
            "sanitized": sanitized,
            "check_type": check_type,
        }
        return json.dumps(result)

    def _check_pii(self, content: str) -> list:
        violations = []
        if self._SSN_PATTERN.search(content):
            violations.append({"type": "pii", "detail": "SSN detected"})
        if self._EMAIL_PATTERN.search(content):
            violations.append({"type": "pii", "detail": "Email detected"})
        if self._PHONE_PATTERN.search(content):
            violations.append({"type": "pii", "detail": "Phone number detected"})
        return violations

    def _check_harmful(self, content: str) -> list:
        violations = []
        content_lower = content.lower()
        for kw in self._HARMFUL_KEYWORDS:
            if kw in content_lower:
                violations.append({"type": "harmful_content", "detail": f"Keyword: {kw}"})
        return violations

    def _check_injection(self, content: str) -> list:
        violations = []
        injection_patterns = [
            r"ignore (all )?instructions",
            r"reveal.*system prompt",
            r"jailbreak",
        ]
        for pattern in injection_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                violations.append({"type": "prompt_injection", "detail": "Injection attempt"})
        return violations

    def _redact(self, content: str) -> str:
        content = self._SSN_PATTERN.sub("[REDACTED]", content)
        content = self._EMAIL_PATTERN.sub("[REDACTED]", content)
        content = self._PHONE_PATTERN.sub("[REDACTED]", content)
        return content
