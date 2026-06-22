"""
Delegation Rules — система пользовательских правил делегирования (Phase 4, Stage 2).

Позволяет пользователю описывать кастомные правила доверия в YAML:

    rules:
      - name: weekend-notes
        action_type: quick_note
        effect: allow
        condition_type: time_range
        condition_params:
          days: ["sat", "sun"]
        description: "Auto-execute notes on weekends"
        priority: 60

      - name: strict-photo
        action_type: photo_classification
        effect: deny
        condition_type: trust_threshold
        condition_params:
          min_trust: 10
        description: "Require high trust for photo classification"
        priority: 70
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import yaml

from selfos.config import rules_file as get_rules_file

# ─── Supported condition types ─────────────────────────────────────────

CONDITION_ALWAYS = "always"
CONDITION_NEVER = "never"
CONDITION_TRUST_THRESHOLD = "trust_threshold"
CONDITION_TIME_RANGE = "time_range"
CONDITION_EXPRESSION = "expression"

VALID_CONDITIONS: frozenset[str] = frozenset({
    CONDITION_ALWAYS,
    CONDITION_NEVER,
    CONDITION_TRUST_THRESHOLD,
    CONDITION_TIME_RANGE,
    CONDITION_EXPRESSION,
})

VALID_EFFECTS = frozenset({"allow", "deny"})


# ─── Data model ────────────────────────────────────────────────────────

@dataclass
class DelegationRule:
    """
    Одно правило делегирования.

    Правило содержит условие (condition_type + condition_params)
    и эффект (allow/deny). Если условие истинно — применяется эффект.
    """

    name: str
    action_type: str
    effect: Literal["allow", "deny"]
    condition_type: str = CONDITION_ALWAYS
    condition_params: dict[str, Any] = field(default_factory=dict)
    description: str = ""
    priority: int = 50
    enabled: bool = True

    def matches(self, action_type: str, trust_value: int = 0, **context: Any) -> bool:
        """
        Проверяет, применимо ли правило к данному action_type.

        Возвращает True, если правило активно и условие выполнено.
        """
        if not self.enabled:
            return False
        if self.action_type != action_type:
            return False

        return self._evaluate_condition(trust_value=trust_value, **context)

    def _evaluate_condition(self, trust_value: int = 0, **context: Any) -> bool:
        """Evaluate the rule's condition."""
        ct = self.condition_type

        if ct == CONDITION_ALWAYS:
            return True

        if ct == CONDITION_NEVER:
            return False

        if ct == CONDITION_TRUST_THRESHOLD:
            min_trust = self.condition_params.get("min_trust", 0)
            return trust_value >= int(min_trust)

        if ct == CONDITION_TIME_RANGE:
            return self._check_time_range(**context)

        if ct == CONDITION_EXPRESSION:
            # Reserved for future expression evaluation
            return False

        return False

    def _check_time_range(self, **context: Any) -> bool:
        """Check time-based conditions."""
        import datetime

        now = datetime.datetime.now()
        days = self.condition_params.get("days", [])
        if days:
            today_str = now.strftime("%a").lower()[:3]
            if today_str not in [d.lower()[:3] for d in days]:
                return False

        start_time = self.condition_params.get("start_time")
        end_time = self.condition_params.get("end_time")

        if start_time:
            start_h, start_m = map(int, start_time.split(":"))
            if (now.hour, now.minute) < (start_h, start_m):
                return False

        if end_time:
            end_h, end_m = map(int, end_time.split(":"))
            if (now.hour, now.minute) > (end_h, end_m):
                return False

        return True

    def validate(self) -> list[str]:
        """Validate rule fields. Returns list of errors (empty = valid)."""
        errors: list[str] = []

        if not self.name:
            errors.append("Rule name is required")
        if not self.action_type:
            errors.append("action_type is required")
        if self.effect not in VALID_EFFECTS:
            errors.append(f"effect must be 'allow' or 'deny', got '{self.effect}'")
        if self.condition_type not in VALID_CONDITIONS:
            errors.append(f"Unknown condition_type '{self.condition_type}'")

        # Validate condition-specific params
        if self.condition_type == CONDITION_TRUST_THRESHOLD:
            min_trust = self.condition_params.get("min_trust", None)
            if min_trust is None or not isinstance(min_trust, (int, float)):
                errors.append("trust_threshold condition requires numeric 'min_trust' param")

        if self.condition_type == CONDITION_TIME_RANGE:
            days = self.condition_params.get("days", [])
            if not isinstance(days, list):
                errors.append("time_range condition requires 'days' list")

        if not isinstance(self.priority, int):
            errors.append("priority must be an integer")

        return errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "action_type": self.action_type,
            "effect": self.effect,
            "condition_type": self.condition_type,
            "condition_params": self.condition_params,
            "description": self.description,
            "priority": self.priority,
            "enabled": self.enabled,
        }


# ─── Rule set (collection) ────────────────────────────────────────────

class DelegationRuleSet:
    """
    Набор правил делегирования с загрузкой/сохранением в YAML.

    Правила упорядочены по приоритету (высший → низший).
    """

    def __init__(self, rules: list[DelegationRule] | None = None) -> None:
        self._rules: list[DelegationRule] = rules or []
        self._sort()

    def _sort(self) -> None:
        """Sort rules by priority descending."""
        self._rules.sort(key=lambda r: r.priority, reverse=True)

    def add(self, rule: DelegationRule) -> None:
        """Add a validated rule."""
        errs = rule.validate()
        if errs:
            raise ValueError(f"Invalid rule: {'; '.join(errs)}")
        # Remove existing rule with same name
        self._rules = [r for r in self._rules if r.name != rule.name]
        self._rules.append(rule)
        self._sort()

    def remove(self, name: str) -> bool:
        """Remove rule by name. Returns True if removed."""
        before = len(self._rules)
        self._rules = [r for r in self._rules if r.name != name]
        return len(self._rules) < before

    def get(self, name: str) -> DelegationRule | None:
        """Get rule by name."""
        for r in self._rules:
            if r.name == name:
                return r
        return None

    def get_all(self) -> list[DelegationRule]:
        """Return all rules sorted by priority."""
        return list(self._rules)

    def find_matching(
        self,
        action_type: str,
        trust_value: int = 0,
        **context: Any,
    ) -> list[DelegationRule]:
        """Find all matching rules for action_type, sorted by priority."""
        return [
            r
            for r in self._rules
            if r.matches(action_type, trust_value=trust_value, **context)
        ]

    def to_yaml(self) -> str:
        """Serialize to YAML string."""
        data = {"rules": [r.to_dict() for r in self._rules]}
        return str(yaml.dump(data, default_flow_style=False, allow_unicode=True))

    @classmethod
    def from_yaml(cls, content: str) -> DelegationRuleSet:
        """Load from YAML string."""
        try:
            data = yaml.safe_load(content)
        except yaml.YAMLError:
            return cls()
        if not data or not isinstance(data, dict):
            return cls()
        raw_rules = data.get("rules", [])
        if not isinstance(raw_rules, list):
            return cls()
        rules = []
        for raw in raw_rules:
            if not isinstance(raw, dict):
                continue
            try:
                rule = DelegationRule(
                    name=str(raw.get("name", "")),
                    action_type=str(raw.get("action_type", "")),
                    effect=str(raw.get("effect", "deny")),  # type: ignore[arg-type]
                    condition_type=str(raw.get("condition_type", CONDITION_ALWAYS)),
                    condition_params=raw.get("condition_params", {}),
                    description=str(raw.get("description", "")),
                    priority=int(raw.get("priority", 50)),
                    enabled=bool(raw.get("enabled", True)),
                )
                # Validate silently, skip invalid rules
                if not rule.validate():
                    rules.append(rule)
            except (ValueError, TypeError):
                continue
        return cls(rules)

    @classmethod
    def from_file(cls, path: Path | str) -> DelegationRuleSet:
        """Load rules from a YAML file."""
        path = Path(path)
        if not path.exists():
            return cls()
        return cls.from_yaml(path.read_text(encoding="utf-8"))

    def save(self, path: Path | str) -> None:
        """Save rules to YAML file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_yaml(), encoding="utf-8")

    def __len__(self) -> int:
        return len(self._rules)


# ─── Convenience: load/save default rules file ─────────────────────────

def load_rules() -> DelegationRuleSet:
    """Load rules from the default ~/.selfos/rules.yaml."""
    return DelegationRuleSet.from_file(get_rules_file())


def save_rules(rules: DelegationRuleSet) -> None:
    """Save rules to the default ~/.selfos/rules.yaml."""
    rules.save(get_rules_file())


def validate_rule_dict(data: dict[str, Any]) -> list[str]:
    """Validate a raw dict as a delegation rule. Returns error list."""
    try:
        rule = DelegationRule(
            name=str(data.get("name", "")),
            action_type=str(data.get("action_type", "")),
            effect=str(data.get("effect", "deny")),  # type: ignore[arg-type]
            condition_type=str(data.get("condition_type", CONDITION_ALWAYS)),
            condition_params=data.get("condition_params", {}),
            description=str(data.get("description", "")),
            priority=int(data.get("priority", 50)),
            enabled=bool(data.get("enabled", True)),
        )
        return rule.validate()
    except (ValueError, TypeError) as e:
        return [str(e)]
