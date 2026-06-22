from __future__ import annotations

import json
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any
from uuid import uuid4

from selfos.config import llm_config
from selfos.context_engine import ContextEngine
from selfos.llm.cost_guard import CostGuard
from selfos.llm.models import Suggestion
from selfos.llm.prompts import PromptManager
from selfos.llm.providers import (
    AnthropicProvider,
    BaseLLMProvider,
    OllamaProvider,
    OpenAIProvider,
)
from selfos.llm.security import PIIRedactor, PromptSanitizer
from selfos.llm.state import SuggestionStateStore

ProviderFactory = Callable[[str], BaseLLMProvider]


class SuggestionEngine:
    def __init__(
        self,
        *,
        state_dir: Path | None = None,
        provider_factory: ProviderFactory | None = None,
        context_engine: ContextEngine | None = None,
    ) -> None:
        self._store = SuggestionStateStore(base_dir=state_dir)
        self._context_engine = context_engine or ContextEngine()
        self._prompts = PromptManager()
        self._sanitizer = PromptSanitizer()
        self._redactor = PIIRedactor()
        self._cost_guard = CostGuard(path=self._store.stats_file)
        self._provider_factory = provider_factory or self._build_provider

    def get_suggestions(
        self,
        mode: str = "rules",
        provider: str | None = None,
    ) -> dict[str, Any]:
        if mode != "llm":
            return self._rules_response(mode="rules")

        requested_provider = provider or str(llm_config().get("provider", "ollama"))
        llm_provider = self._provider_factory(requested_provider)
        if not llm_provider.is_available():
            self._store.record_stats(requests=1, fallbacks=1)
            return self._rules_response(
                mode="rules_fallback",
                fallback_reason="provider_unavailable",
            )

        start = time.time()
        context = self._build_context()
        prompt = self._prompts.render("suggest_general", context)
        redacted = self._redactor.redact_text(prompt)
        input_tokens = llm_provider.count_tokens(redacted.text)
        if not self._cost_guard.can_spend(
            model=llm_provider.model,
            input_tokens=input_tokens,
            output_tokens=400,
        ):
            self._store.record_stats(requests=1, fallbacks=1)
            return self._rules_response(
                mode="rules_fallback",
                fallback_reason="budget_exceeded",
            )

        cache_key = self._cost_guard.semantic_key(
            context=context,
            template="suggest_general",
            provider=llm_provider.name,
            model=llm_provider.model,
        )
        cache = self._store.load_cache()
        if cache_key in cache:
            payload = cache[cache_key]
            suggestions = [self._suggestion_from_dict(item) for item in payload["suggestions"]]
            self._store.save_suggestions(suggestions)
            return {
                "backend_requested": "llm",
                "backend_used": "llm",
                "provider": llm_provider.name,
                "suggestions": [item.to_dict() for item in suggestions],
                "fallback_reason": None,
                "cached": True,
                "usage": payload.get("usage", {}),
            }

        try:
            llm_response = llm_provider.complete(redacted.text)
            suggestions = self._parse_llm_suggestions(llm_response.content, backend_used="llm")
        except (ValueError, KeyError, json.JSONDecodeError):
            self._store.record_stats(requests=1, fallbacks=1)
            return self._rules_response(
                mode="rules_fallback",
                fallback_reason="invalid_llm_output",
            )

        self._cost_guard.record_usage(
            model=llm_provider.model,
            input_tokens=llm_response.input_tokens,
            output_tokens=llm_response.output_tokens,
        )
        self._store.save_suggestions(suggestions)
        latency_ms = int((time.time() - start) * 1000)
        self._store.record_stats(requests=1, llm_requests=1, latency_ms=latency_ms)
        usage = {
            "input_tokens": llm_response.input_tokens,
            "output_tokens": llm_response.output_tokens,
        }
        self._store.save_cache_entry(
            cache_key,
            {"suggestions": [item.to_dict() for item in suggestions], "usage": usage},
        )
        return {
            "backend_requested": "llm",
            "backend_used": "llm",
            "provider": llm_provider.name,
            "suggestions": [item.to_dict() for item in suggestions],
            "fallback_reason": None,
            "cached": False,
            "usage": usage,
        }

    def approve_suggestion(self, suggestion_id: str) -> dict[str, Any]:
        suggestion = self._store.approve(suggestion_id)
        self._store.record_stats(approvals=1)
        return {"status": "approved", "suggestion_id": suggestion_id, "suggestion": suggestion}

    def rate_suggestion(self, suggestion_id: str, rating: int) -> None:
        self._store.rate(suggestion_id, rating)
        self._store.record_stats(ratings=1)

    def get_stats(self) -> dict[str, Any]:
        return self._store.get_stats()

    def clear_cache(self) -> None:
        self._store.clear_cache()

    def _rules_response(self, *, mode: str, fallback_reason: str | None = None) -> dict[str, Any]:
        suggestions = self._rules_suggestions(backend_used=mode)
        self._store.save_suggestions(suggestions)
        self._store.record_stats(requests=1 if mode == "rules" else 0)
        return {
            "backend_requested": "llm" if mode == "rules_fallback" else "rules",
            "backend_used": mode,
            "provider": None,
            "suggestions": [item.to_dict() for item in suggestions],
            "fallback_reason": fallback_reason,
            "cached": False,
            "usage": {},
        }

    def _rules_suggestions(self, *, backend_used: str) -> list[Suggestion]:
        texts = self._context_engine.get_proactive_suggestions()
        suggestions = [
            Suggestion(
                id=f"rules-{uuid4().hex[:8]}",
                title=text[:60],
                summary=text,
                action="review_context",
                confidence=0.7,
                backend_used=backend_used,
                source_context={"activity": True},
            )
            for text in texts
        ]
        return suggestions

    def _build_context(self) -> dict[str, Any]:
        patterns = self._context_engine.get_patterns()
        suggestions = self._context_engine.get_proactive_suggestions()
        return {
            "summary": self._context_engine.get_context_summary(),
            "patterns": patterns,
            "rules_suggestions": suggestions,
            "unread_emails": [],
            "active_tasks": [],
            "upcoming_events": [],
        }

    def _parse_llm_suggestions(
        self,
        raw: str,
        *,
        backend_used: str,
    ) -> list[Suggestion]:
        payload = json.loads(raw)
        items = payload.get("suggestions", [])
        if not isinstance(items, list):
            raise ValueError("suggestions must be a list")
        suggestions: list[Suggestion] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            confidence = self._sanitizer.clamp_confidence(
                float(item.get("confidence", 0.5))
            )
            title = str(item["title"])
            summary = str(item["summary"])
            restored_summary = self._redactor.restore_text(summary)
            suggestions.append(
                Suggestion(
                    id=f"llm-{uuid4().hex[:8]}",
                    title=title,
                    summary=restored_summary,
                    action=str(item.get("action", "review_context")),
                    confidence=confidence,
                    backend_used=backend_used,
                    source_context={"activity": True, "llm": True},
                )
            )
        if not suggestions:
            raise ValueError("No suggestions parsed")
        return suggestions

    def _suggestion_from_dict(self, data: dict[str, Any]) -> Suggestion:
        return Suggestion(
            id=str(data["id"]),
            title=str(data["title"]),
            summary=str(data["summary"]),
            action=str(data.get("action", "review_context")),
            confidence=float(data.get("confidence", 0.5)),
            backend_used=str(data.get("backend_used", "llm")),
            source_context=dict(data.get("source_context", {})),
            status=str(data.get("status", "new")),
        )

    def _build_provider(self, name: str) -> BaseLLMProvider:
        config = llm_config()
        provider_name = name
        model = str(config.get("model", "llama3.2"))
        if provider_name == "openai":
            return OpenAIProvider(
                model=model or "gpt-4o-mini",
                api_key=str(config.get("api_key", "")),
            )
        if provider_name == "anthropic":
            return AnthropicProvider(
                model=model or "claude-3-5-sonnet-latest",
                api_key=str(config.get("api_key", "")),
            )
        return OllamaProvider(model=model or "llama3.2")
