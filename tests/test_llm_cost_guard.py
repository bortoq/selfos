from __future__ import annotations

from selfos.llm.cost_guard import CostGuard


def test_cost_guard_blocks_when_daily_budget_exceeded(tmp_path) -> None:
    guard = CostGuard(path=tmp_path / "stats.json", max_cost_usd_per_day=1.0)
    guard.record_usage(model="gpt-4o-mini", input_tokens=7_000_000, output_tokens=0)
    assert guard.can_spend(model="gpt-4o-mini", input_tokens=1, output_tokens=1) is False


def test_cost_guard_generates_stable_semantic_key(tmp_path) -> None:
    guard = CostGuard(path=tmp_path / "stats.json", time_fn=lambda: 7200.0)
    one = guard.semantic_key(
        context={"unread_emails": [1, 2], "active_tasks": [1], "upcoming_events": []},
        template="suggest_general",
        provider="ollama",
        model="llama3.2",
    )
    two = guard.semantic_key(
        context={"active_tasks": [1], "upcoming_events": [], "unread_emails": [3, 4]},
        template="suggest_general",
        provider="ollama",
        model="llama3.2",
    )
    assert one == two
