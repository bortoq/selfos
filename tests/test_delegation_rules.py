"""
Тесты для delegation_rules.py — пользовательские правила делегирования.
"""

from pathlib import Path
from selfos.delegation_rules import (
    DelegationRule,
    DelegationRuleSet,
    validate_rule_dict,
    load_rules,
    save_rules,
)


# ─── DelegationRule: создание и валидация ─────────────────────────────

class TestDelegationRuleCreation:
    def test_minimal_rule(self) -> None:
        rule = DelegationRule(name="test", action_type="quick_note", effect="allow")
        assert rule.name == "test"
        assert rule.action_type == "quick_note"
        assert rule.effect == "allow"
        assert rule.condition_type == "always"
        assert rule.enabled is True
        assert rule.priority == 50

    def test_validation_valid(self) -> None:
        rule = DelegationRule(
            name="valid-rule",
            action_type="quick_note",
            effect="allow",
            condition_type="trust_threshold",
            condition_params={"min_trust": 5},
        )
        assert rule.validate() == []

    def test_validation_no_name(self) -> None:
        rule = DelegationRule(name="", action_type="quick_note", effect="allow")
        errs = rule.validate()
        assert "Rule name is required" in errs

    def test_validation_invalid_effect(self) -> None:
        rule = DelegationRule(
            name="r", action_type="x", effect="invalid"  # type: ignore[arg-type]
        )
        errs = rule.validate()
        assert any("effect must be 'allow' or 'deny'" in e for e in errs)

    def test_validation_unknown_condition(self) -> None:
        rule = DelegationRule(
            name="r", action_type="x", effect="allow",
            condition_type="magic",
        )
        errs = rule.validate()
        assert any("Unknown condition_type" in e for e in errs)

    def test_validation_trust_threshold_missing_param(self) -> None:
        rule = DelegationRule(
            name="r", action_type="x", effect="allow",
            condition_type="trust_threshold",
            condition_params={},
        )
        errs = rule.validate()
        assert any("min_trust" in e for e in errs)

    def test_validation_never_no_params(self) -> None:
        rule = DelegationRule(
            name="r", action_type="x", effect="deny",
            condition_type="never",
        )
        assert rule.validate() == []


# ─── DelegationRule.matches() ─────────────────────────────────────────

class TestDelegationRuleMatches:
    def test_always_matches(self) -> None:
        rule = DelegationRule(name="r", action_type="quick_note", effect="allow")
        assert rule.matches("quick_note") is True
        assert rule.matches("other") is False

    def test_never_matches(self) -> None:
        rule = DelegationRule(
            name="r", action_type="quick_note", effect="deny",
            condition_type="never",
        )
        assert rule.matches("quick_note") is False
        # never condition always returns False, so rule never matches
        assert rule.matches("quick_note", trust_value=100) is False

    def test_disabled_never_matches(self) -> None:
        rule = DelegationRule(
            name="r", action_type="quick_note", effect="allow",
            enabled=False,
        )
        assert rule.matches("quick_note") is False

    def test_trust_threshold_met(self) -> None:
        rule = DelegationRule(
            name="r", action_type="quick_note", effect="allow",
            condition_type="trust_threshold",
            condition_params={"min_trust": 5},
        )
        assert rule.matches("quick_note", trust_value=10) is True
        assert rule.matches("quick_note", trust_value=3) is False

    def test_time_range_matches(self) -> None:
        """Test time_range with current day included."""
        import datetime
        today_short = datetime.datetime.now().strftime("%a").lower()[:3]
        rule = DelegationRule(
            name="r", action_type="quick_note", effect="allow",
            condition_type="time_range",
            condition_params={"days": [today_short]},
        )
        assert rule.matches("quick_note") is True

    def test_time_range_wrong_day(self) -> None:
        """Test time_range with a day that's not today."""
        import datetime
        today_short = datetime.datetime.now().strftime("%a").lower()[:3]
        # Pick a different day
        all_days = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
        other_days = [d for d in all_days if d != today_short]
        rule = DelegationRule(
            name="r", action_type="quick_note", effect="allow",
            condition_type="time_range",
            condition_params={"days": other_days},
        )
        assert rule.matches("quick_note") is False


# ─── DelegationRuleSet ────────────────────────────────────────────────

class TestDelegationRuleSet:
    def test_empty_set(self) -> None:
        rs = DelegationRuleSet()
        assert len(rs) == 0
        assert rs.get_all() == []

    def test_add_and_list(self) -> None:
        rs = DelegationRuleSet()
        rs.add(DelegationRule(name="a", action_type="x", effect="allow"))
        rs.add(DelegationRule(name="b", action_type="y", effect="deny"))
        assert len(rs) == 2
        names = [r.name for r in rs.get_all()]
        assert "a" in names
        assert "b" in names

    def test_add_invalid_raises(self) -> None:
        import pytest
        rs = DelegationRuleSet()
        with pytest.raises(ValueError, match="Invalid rule"):
            rs.add(DelegationRule(name="", action_type="x", effect="allow"))

    def test_add_replaces_existing(self) -> None:
        rs = DelegationRuleSet()
        rs.add(DelegationRule(name="r", action_type="x", effect="allow", priority=50))
        rs.add(DelegationRule(name="r", action_type="x", effect="deny", priority=60))
        assert len(rs) == 1
        assert rs.get("r") is not None
        # noinspection PyUnresolvedReferences
        assert rs.get("r").effect == "deny"  # type: ignore[union-attr]

    def test_remove(self) -> None:
        rs = DelegationRuleSet()
        rs.add(DelegationRule(name="r", action_type="x", effect="allow"))
        assert rs.remove("r") is True
        assert len(rs) == 0
        assert rs.remove("nonexistent") is False

    def test_get(self) -> None:
        rs = DelegationRuleSet()
        rs.add(DelegationRule(name="r", action_type="x", effect="allow"))
        assert rs.get("r") is not None
        assert rs.get("nonexistent") is None

    def test_sort_by_priority(self) -> None:
        rs = DelegationRuleSet()
        rs.add(DelegationRule(name="low", action_type="x", effect="allow", priority=10))
        rs.add(DelegationRule(name="high", action_type="x", effect="deny", priority=90))
        rs.add(DelegationRule(name="mid", action_type="x", effect="allow", priority=50))
        names = [r.name for r in rs.get_all()]
        assert names == ["high", "mid", "low"]

    def test_find_matching(self) -> None:
        rs = DelegationRuleSet()
        rs.add(DelegationRule(name="note-allow", action_type="quick_note", effect="allow"))
        rs.add(DelegationRule(name="photo-deny", action_type="photo_classification", effect="deny"))
        matching = rs.find_matching("quick_note")
        assert len(matching) == 1
        assert matching[0].name == "note-allow"

    def test_find_matching_respects_priority(self) -> None:
        """When multiple rules match, highest priority comes first."""
        rs = DelegationRuleSet()
        rs.add(DelegationRule(
            name="low-deny", action_type="quick_note", effect="deny", priority=10,
        ))
        rs.add(DelegationRule(
            name="high-allow", action_type="quick_note", effect="allow", priority=90,
        ))
        matching = rs.find_matching("quick_note")
        assert len(matching) == 2
        assert matching[0].name == "high-allow"
        assert matching[1].name == "low-deny"


# ─── YAML roundtrip ───────────────────────────────────────────────────

class TestDelegationRuleSetYAML:
    def test_to_yaml_and_back(self) -> None:
        rs = DelegationRuleSet()
        rs.add(DelegationRule(
            name="test-rule",
            action_type="quick_note",
            effect="allow",
            description="Test rule",
            priority=60,
        ))
        yaml_str = rs.to_yaml()
        loaded = DelegationRuleSet.from_yaml(yaml_str)
        assert len(loaded) == 1
        rule = loaded.get("test-rule")
        assert rule is not None
        assert rule.effect == "allow"
        assert rule.priority == 60
        assert rule.description == "Test rule"

    def test_empty_yaml(self) -> None:
        rs = DelegationRuleSet.from_yaml("")
        assert len(rs) == 0

    def test_invalid_yaml(self) -> None:
        rs = DelegationRuleSet.from_yaml("not: valid: yaml: [[[")
        assert len(rs) == 0

    def test_yaml_with_rule_of_wrong_type(self) -> None:
        rs = DelegationRuleSet.from_yaml("rules: [42]")
        assert len(rs) == 0

    def test_roundtrip_trust_threshold(self) -> None:
        rs = DelegationRuleSet()
        rs.add(DelegationRule(
            name="trust-rule",
            action_type="photo_classification",
            effect="deny",
            condition_type="trust_threshold",
            condition_params={"min_trust": 10},
        ))
        yaml_str = rs.to_yaml()
        loaded = DelegationRuleSet.from_yaml(yaml_str)
        rule = loaded.get("trust-rule")
        assert rule is not None
        assert rule.condition_params.get("min_trust") == 10


# ─── File I/O ─────────────────────────────────────────────────────────

class TestFileIO:
    def test_save_and_load(self, tmp_path: Path) -> None:
        rules_file = tmp_path / "rules.yaml"
        rs = DelegationRuleSet()
        rs.add(DelegationRule(name="file-rule", action_type="x", effect="allow"))
        rs.save(rules_file)
        assert rules_file.exists()
        loaded = DelegationRuleSet.from_file(rules_file)
        assert len(loaded) == 1
        assert loaded.get("file-rule") is not None

    def test_load_nonexistent(self) -> None:
        rs = DelegationRuleSet.from_file("/nonexistent/rules.yaml")
        assert len(rs) == 0


# ─── Convenience functions ────────────────────────────────────────────

class TestConvenience:
    def test_validate_rule_dict_valid(self) -> None:
        errs = validate_rule_dict({
            "name": "r",
            "action_type": "x",
            "effect": "allow",
        })
        assert errs == []

    def test_validate_rule_dict_invalid(self) -> None:
        errs = validate_rule_dict({
            "name": "",
            "action_type": "",
            "effect": "maybe",
        })
        assert len(errs) > 0


# ─── Engine integration (will be tested in test_delegation_engine.py) ─
