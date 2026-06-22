from selfos.delegation_engine import DelegationEngine


def test_task_create_is_display_only_per_roadmap() -> None:
    engine = DelegationEngine()
    decision = engine.evaluate_suggestion(
        {
            "action": "task_create",
            "confidence": 0.95,
        }
    )
    assert decision == "display_only"
