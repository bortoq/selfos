from __future__ import annotations

from selfos.integrations.rate_limiter import RateLimiter


def test_rate_limiter_consumes_capacity_and_persists_state(tmp_path) -> None:
    limiter = RateLimiter(
        path=tmp_path / "rate_limits.json",
        time_fn=lambda: 100.0,
    )

    wait_time = limiter.acquire("gmail", capacity=2, refill_rate=1.0)
    second_wait = limiter.acquire("gmail", capacity=2, refill_rate=1.0)
    blocked_wait = limiter.acquire("gmail", capacity=2, refill_rate=1.0)

    assert wait_time == 0.0
    assert second_wait == 0.0
    assert blocked_wait == 1.0


def test_rate_limiter_applies_retry_after(tmp_path) -> None:
    now = {"value": 200.0}
    limiter = RateLimiter(
        path=tmp_path / "rate_limits.json",
        time_fn=lambda: now["value"],
    )

    limiter.apply_retry_after("gmail", "12")
    wait_time = limiter.acquire("gmail")

    assert wait_time == 12.0

    now["value"] = 213.0
    assert limiter.acquire("gmail") == 0.0
