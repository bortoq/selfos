from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from selfos.config import llm_dir
from selfos.llm.models import Suggestion


class SuggestionStateStore:
    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = base_dir or llm_dir()
        self.suggestions_file = self.base_dir / "suggestions.json"
        self.ratings_file = self.base_dir / "ratings.json"
        self.stats_file = self.base_dir / "stats.json"
        self.cache_file = self.base_dir / "cache.json"

    def save_suggestions(self, suggestions: list[Suggestion]) -> None:
        stored = self.list_suggestions()
        by_id = {item["id"]: item for item in stored}
        for suggestion in suggestions:
            by_id[suggestion.id] = suggestion.to_dict()
        self._write_json(self.suggestions_file, list(by_id.values()))

    def list_suggestions(self) -> list[dict[str, Any]]:
        raw = self._read_json(self.suggestions_file, [])
        return raw if isinstance(raw, list) else []

    def approve(self, suggestion_id: str) -> dict[str, Any]:
        suggestions = self.list_suggestions()
        for suggestion in suggestions:
            if suggestion.get("id") == suggestion_id:
                suggestion["status"] = "approved"
                self._write_json(self.suggestions_file, suggestions)
                return suggestion
        raise ValueError(f"Unknown suggestion id: {suggestion_id}")

    def rate(self, suggestion_id: str, rating: int) -> None:
        ratings = self.load_ratings()
        ratings[suggestion_id] = rating
        self._write_json(self.ratings_file, ratings)

    def load_ratings(self) -> dict[str, int]:
        raw = self._read_json(self.ratings_file, {})
        return raw if isinstance(raw, dict) else {}

    def record_stats(self, **updates: int | float) -> dict[str, Any]:
        stats = self.get_stats()
        for key, value in updates.items():
            current = stats.get(key, 0)
            if isinstance(current, (int, float)):
                stats[key] = current + value
            else:
                stats[key] = value
        self._write_json(self.stats_file, stats)
        return stats

    def get_stats(self) -> dict[str, Any]:
        raw = self._read_json(self.stats_file, {})
        return raw if isinstance(raw, dict) else {}

    def load_cache(self) -> dict[str, Any]:
        raw = self._read_json(self.cache_file, {})
        return raw if isinstance(raw, dict) else {}

    def save_cache_entry(self, key: str, value: dict[str, Any]) -> None:
        cache = self.load_cache()
        cache[key] = value
        self._write_json(self.cache_file, cache)

    def clear_cache(self) -> None:
        self._write_json(self.cache_file, {})

    def _read_json(self, path: Path, default: Any) -> Any:
        if not path.exists():
            return default
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return default

    def _write_json(self, path: Path, payload: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
