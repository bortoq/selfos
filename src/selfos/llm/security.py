from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class RedactedText:
    text: str
    replacements: dict[str, str] = field(default_factory=dict)


class PIIRedactor:
    EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
    PHONE_RE = re.compile(r"\+?\d[\d\-\s]{7,}\d")
    URL_RE = re.compile(r"https?://\S+")

    def __init__(self) -> None:
        self._last_replacements: dict[str, str] = {}

    def redact_text(self, text: str) -> RedactedText:
        replacements: dict[str, str] = {}
        redacted = text
        patterns = [
            ("EMAIL", self.EMAIL_RE),
            ("PHONE", self.PHONE_RE),
            ("URL", self.URL_RE),
        ]
        for label, pattern in patterns:
            for index, match in enumerate(pattern.findall(redacted), start=1):
                token = f"[{label}_{index}]"
                replacements[token] = match
                redacted = redacted.replace(match, token)
        self._last_replacements = replacements.copy()
        return RedactedText(text=redacted, replacements=replacements)

    def restore_text(self, text: str, replacements: dict[str, str] | None = None) -> str:
        restored = text
        active_replacements = replacements if replacements is not None else self._last_replacements
        for token, value in active_replacements.items():
            restored = restored.replace(token, value)
        return restored


class PromptSanitizer:
    SUSPICIOUS_PATTERNS = [
        "ignore previous instructions",
        "system prompt",
        "developer message",
        "disregard all prior",
    ]

    def has_suspicious_patterns(self, text: str) -> bool:
        lowered = text.lower()
        return any(pattern in lowered for pattern in self.SUSPICIOUS_PATTERNS)

    def clamp_confidence(self, value: float) -> float:
        return max(0.0, min(0.95, value))
