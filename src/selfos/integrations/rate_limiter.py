"""
Persistent rate limiter for external integrations.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from selfos.config import rate_limits_file


class RateLimiter:
    """Simple persistent token bucket with Retry-After support."""

    def __init__(
        self,
        path: Path | None = None,
        time_fn: Any | None = None,
    ) -> None:
        self._path = path or rate_limits_file()
        self._time_fn = time_fn or time.time

    def acquire(
        self,
        key: str,
        *,
        capacity: float = 10.0,
        refill_rate: float = 1.0,
        cost: float = 1.0,
    ) -> float:
        """Consumes tokens if available and returns required wait time."""
        now = float(self._time_fn())
        state = self._load_state()
        bucket = self._refill_bucket(
            state.get(key, self._new_bucket(capacity, now)),
            capacity=capacity,
            refill_rate=refill_rate,
            now=now,
        )

        blocked_until = float(bucket.get("blocked_until", 0.0))
        if blocked_until > now:
            state[key] = bucket
            self._save_state(state)
            return blocked_until - now

        tokens = float(bucket["tokens"])
        if tokens >= cost:
            bucket["tokens"] = tokens - cost
            bucket["updated_at"] = now
            state[key] = bucket
            self._save_state(state)
            return 0.0

        if refill_rate <= 0:
            return float("inf")

        wait_time = (cost - tokens) / refill_rate
        bucket["updated_at"] = now
        state[key] = bucket
        self._save_state(state)
        return wait_time

    def apply_retry_after(self, key: str, retry_after: str | int | float) -> None:
        """Applies Retry-After from API responses."""
        now = float(self._time_fn())
        state = self._load_state()
        bucket = state.get(key, self._new_bucket(10.0, now))
        bucket["blocked_until"] = now + float(retry_after)
        bucket["updated_at"] = now
        state[key] = bucket
        self._save_state(state)

    def _new_bucket(self, capacity: float, now: float) -> dict[str, float]:
        return {
            "tokens": capacity,
            "updated_at": now,
            "blocked_until": 0.0,
        }

    def _refill_bucket(
        self,
        bucket: dict[str, float],
        *,
        capacity: float,
        refill_rate: float,
        now: float,
    ) -> dict[str, float]:
        updated_at = float(bucket.get("updated_at", now))
        elapsed = max(0.0, now - updated_at)
        tokens = min(capacity, float(bucket.get("tokens", capacity)) + elapsed * refill_rate)
        bucket["tokens"] = tokens
        bucket["updated_at"] = now
        bucket.setdefault("blocked_until", 0.0)
        return bucket

    def _load_state(self) -> dict[str, dict[str, float]]:
        if not self._path.exists():
            return {}
        raw = json.loads(self._path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return {}
        return {
            str(key): {
                "tokens": float(value.get("tokens", 0.0)),
                "updated_at": float(value.get("updated_at", 0.0)),
                "blocked_until": float(value.get("blocked_until", 0.0)),
            }
            for key, value in raw.items()
            if isinstance(value, dict)
        }

    def _save_state(self, state: dict[str, dict[str, float]]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(state, indent=2), encoding="utf-8")
