from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any, cast

MODEL_PRICES: dict[str, dict[str, float]] = {
    "gpt-4o": {"input": 5.0, "output": 15.0},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "claude-sonnet": {"input": 3.0, "output": 15.0},
    "claude-3-5-sonnet-latest": {"input": 3.0, "output": 15.0},
    "claude-haiku": {"input": 0.25, "output": 1.25},
    "llama3.2": {"input": 0.0, "output": 0.0},
}


class CostGuard:
    def __init__(
        self,
        path: Path,
        *,
        max_cost_usd_per_day: float = 1.0,
        time_fn: Any | None = None,
    ) -> None:
        self._path = path
        self.max_cost_usd_per_day = max_cost_usd_per_day
        self._time_fn = time_fn or time.time

    def semantic_key(
        self,
        *,
        context: dict[str, Any],
        template: str,
        provider: str,
        model: str,
    ) -> str:
        significant = {
            "emails_count": len(context.get("unread_emails", [])),
            "tasks_count": len(context.get("active_tasks", [])),
            "events_count": len(context.get("upcoming_events", [])),
            "template": template,
            "provider": provider,
            "model": model,
            "hour_bucket": int(self._time_fn()) // 3600,
        }
        data = json.dumps(significant, sort_keys=True).encode("utf-8")
        return hashlib.sha256(data).hexdigest()[:16]

    def estimate_cost(self, *, model: str, input_tokens: int, output_tokens: int) -> float:
        prices = MODEL_PRICES.get(model, {"input": 0.0, "output": 0.0})
        return (
            (input_tokens / 1_000_000) * prices["input"]
            + (output_tokens / 1_000_000) * prices["output"]
        )

    def can_spend(self, *, model: str, input_tokens: int, output_tokens: int) -> bool:
        estimated_cost = self.estimate_cost(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
        return self._spent_today() + estimated_cost <= self.max_cost_usd_per_day

    def record_usage(self, *, model: str, input_tokens: int, output_tokens: int) -> None:
        state = self._load()
        today = self._today_key()
        entry = state.get(today, {"spent_usd": 0.0, "requests": 0})
        entry["spent_usd"] = float(entry["spent_usd"]) + self.estimate_cost(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
        entry["requests"] = int(entry["requests"]) + 1
        state[today] = entry
        self._save(state)

    def _spent_today(self) -> float:
        return float(self._load().get(self._today_key(), {}).get("spent_usd", 0.0))

    def _today_key(self) -> str:
        return time.strftime("%Y-%m-%d", time.gmtime(self._time_fn()))

    def _load(self) -> dict[str, dict[str, float | int]]:
        if not self._path.exists():
            return {}
        return cast(
            dict[str, dict[str, float | int]],
            json.loads(self._path.read_text(encoding="utf-8")),
        )

    def _save(self, state: dict[str, dict[str, float | int]]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(state, indent=2), encoding="utf-8")
