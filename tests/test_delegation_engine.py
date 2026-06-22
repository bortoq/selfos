from pathlib import Path

from selfos.delegation_engine import DelegationEngine
from selfos.delegation_rules import DelegationRule

# ─── Helper ───────────────────────────────────────────────────────────

def make_engine(tmp_path: Path) -> DelegationEngine:
    """Create an engine with isolated rules file for test isolation."""
    rules_file = tmp_path / "rules.yaml"
    return DelegationEngine(rules_file=str(rules_file))


# ─── Core engine tests (unchanged) ────────────────────────────────────

def test_critical_actions_never_auto(tmp_path: Path):
    engine = make_engine(tmp_path)
    assert engine.should_auto_execute("email_send") is False
    assert engine.should_auto_execute("delete_data") is False


def test_override_works(tmp_path: Path):
    engine = make_engine(tmp_path)
    engine.set_override("email_send", True)
    assert engine.should_auto_execute("email_send") is True
    engine.clear_override("email_send")
    assert engine.should_auto_execute("email_send") is False


def test_execute_blocked(tmp_path: Path):
    engine = make_engine(tmp_path)
    result = engine.execute("email_send", "quick_note", text="test")
    assert result["executed"] is False
    assert "not allowed" in result["reason"]


# ─── Custom rules integration ─────────────────────────────────────────

def test_allow_rule_overrides_trust_default(tmp_path: Path):
    """
    Если правило allow срабатывает, should_auto_execute возвращает True,
    даже если стандартная система доверия сказала бы False.
    """
    engine = make_engine(tmp_path)
    engine.add_rule(DelegationRule(
        name="allow-all-notes",
        action_type="quick_note",
        effect="allow",
    ))
    assert engine.should_auto_execute("quick_note") is True


def test_deny_rule_overrides_trust_default(tmp_path: Path):
    """
    Если правило deny срабатывает, should_auto_execute возвращает False,
    даже если система доверия разрешила бы авто-выполнение.
    """
    engine = make_engine(tmp_path)
    import json

    from selfos.config import trust_file
    tf = trust_file()
    tf.parent.mkdir(parents=True, exist_ok=True)
    with open(tf, "w") as f:
        json.dump({"quick_note": 100}, f)

    try:
        engine.add_rule(DelegationRule(
            name="deny-notes",
            action_type="quick_note",
            effect="deny",
            priority=90,
        ))
        assert engine.should_auto_execute("quick_note") is False
    finally:
        if tf.exists():
            tf.unlink()


def test_highest_priority_rule_wins(tmp_path: Path):
    engine = make_engine(tmp_path)
    engine.add_rule(DelegationRule(
        name="low-priority-allow",
        action_type="quick_note",
        effect="allow",
        priority=10,
    ))
    engine.add_rule(DelegationRule(
        name="high-priority-deny",
        action_type="quick_note",
        effect="deny",
        priority=90,
    ))
    assert engine.should_auto_execute("quick_note") is False


def test_override_still_highest_priority(tmp_path: Path):
    engine = make_engine(tmp_path)
    engine.add_rule(DelegationRule(
        name="deny-all",
        action_type="email_send",
        effect="deny",
        priority=100,
    ))
    assert engine.should_auto_execute("email_send") is False
    engine.set_override("email_send", True)
    assert engine.should_auto_execute("email_send") is True


def test_rule_only_matches_its_action_type(tmp_path: Path):
    engine = make_engine(tmp_path)
    engine.add_rule(DelegationRule(
        name="notes-only",
        action_type="quick_note",
        effect="allow",
    ))
    assert engine.should_auto_execute("email_send") is False
    assert engine.should_auto_execute("quick_note") is True


def test_list_rules(tmp_path: Path):
    engine = make_engine(tmp_path)
    engine.add_rule(DelegationRule(name="r1", action_type="a", effect="allow"))
    engine.add_rule(DelegationRule(name="r2", action_type="b", effect="deny"))
    rules = engine.list_rules()
    assert len(rules) == 2
    names = [r["name"] for r in rules]
    assert "r1" in names
    assert "r2" in names


def test_get_rule(tmp_path: Path):
    engine = make_engine(tmp_path)
    engine.add_rule(DelegationRule(
        name="my-rule",
        action_type="photo_classification",
        effect="allow",
        priority=75,
    ))
    rule = engine.get_rule("my-rule")
    assert rule is not None
    assert rule["name"] == "my-rule"
    assert rule["priority"] == 75
    assert engine.get_rule("nonexistent") is None


def test_remove_rule(tmp_path: Path):
    engine = make_engine(tmp_path)
    engine.add_rule(DelegationRule(name="r", action_type="x", effect="allow"))
    assert len(engine.list_rules()) == 1
    assert engine.remove_rule("r") is True
    assert len(engine.list_rules()) == 0
    assert engine.remove_rule("nonexistent") is False


def test_reload_rules(tmp_path: Path):
    """reload_rules should re-read from disk."""
    engine = make_engine(tmp_path)
    engine.add_rule(DelegationRule(name="r", action_type="x", effect="allow"))
    assert len(engine.list_rules()) == 1
    # Simulate external change: delete file, then reload
    rules_file = tmp_path / "rules.yaml"
    if rules_file.exists():
        rules_file.unlink()
    engine.reload_rules()
    assert len(engine.list_rules()) == 0


def test_time_range_rule(tmp_path: Path):
    import datetime
    today_short = datetime.datetime.now().strftime("%a").lower()[:3]
    engine = make_engine(tmp_path)
    engine.add_rule(DelegationRule(
        name="weekend-only",
        action_type="quick_note",
        effect="allow",
        condition_type="time_range",
        condition_params={"days": [today_short]},
    ))
    assert engine.should_auto_execute("quick_note") is True
