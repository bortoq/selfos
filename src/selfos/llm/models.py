from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class LLMResponse:
    content: str
    input_tokens: int
    output_tokens: int
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class Suggestion:
    id: str
    title: str
    summary: str
    action: str
    confidence: float
    backend_used: str
    source_context: dict[str, Any]
    status: str = "new"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
