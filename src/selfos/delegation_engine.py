"""
DelegationEngine — центральный компонент глубокого делегирования (Phase 3, Этап 4).

Phase 4, Stage 2: добавлена поддержка пользовательских правил делегирования
через DelegationRuleSet (YAML-файл rules.yaml).

Порядок принятия решения (should_auto_execute):
  1. Ручные переопределения (overrides) — высший приоритет
  2. Пользовательские правила (custom rules) — по приоритету
  3. Критические действия (CRITICAL_ACTIONS) — всегда deny
  4. Стандартная система доверия (trust.py) — fallback
"""

from typing import Any

from selfos.delegation_rules import DelegationRuleSet, load_rules, save_rules
from selfos.plugin_registry import PluginRegistry
from selfos.trust import can_auto, increase_trust


class DelegationEngine:
    """
    Движок глубокого делегирования с поддержкой кастомных правил.
    """

    # Критически важные действия, которые никогда не должны выполняться автоматически
    CRITICAL_ACTIONS = {
        "email_send",      # Отправка писем
        "delete_data",     # Удаление данных
        "financial_transaction"
    }
    LLM_TO_DELEGATION_MAP: dict[str, str | None] = {
        "email_reply": "email_send",
        "task_create": "quick_note",
        "note": "quick_note",
        "review_context": None,
        "review_schedule": None,
    }

    def __init__(self, rules_file: str | None = None) -> None:
        self.overrides: dict[str, bool] = {}  # Ручные переопределения
        self._rules: DelegationRuleSet | None = None  # Ленивая загрузка
        self._rules_file: str | None = rules_file  # Для тестовой изоляции

    @property
    def rules(self) -> DelegationRuleSet:
        """Ленивая загрузка правил."""
        if self._rules is None:
            if self._rules_file is not None:
                self._rules = DelegationRuleSet.from_file(self._rules_file)
            else:
                self._rules = load_rules()
        return self._rules

    def reload_rules(self) -> None:
        """Перезагрузить правила из файла."""
        if self._rules_file is not None:
            self._rules = DelegationRuleSet.from_file(self._rules_file)
        else:
            self._rules = load_rules()

    def should_auto_execute(self, action_type: str, force: bool = False) -> bool:
        """
        Определяет, можно ли выполнить действие автоматически.

        Порядок проверки:
          1. Ручное переопределение (overrides)
          2. Пользовательские правила (custom rules)
          3. Критические действия (CRITICAL_ACTIONS)
          4. Система доверия (can_auto)
        """
        # 1. Ручное переопределение имеет высший приоритет
        if action_type in self.overrides:
            return self.overrides[action_type]

        # 2. Пользовательские правила
        matching = self.rules.find_matching(action_type)
        if matching:
            # Берём правило с высшим приоритетом
            rule = matching[0]
            if rule.effect == "allow":
                return True
            # rule.effect == "deny"
            return False

        # 3. Критические действия не выполняются автоматически
        if action_type in self.CRITICAL_ACTIONS and not force:
            return False

        # 4. Стандартная система доверия
        return can_auto(action_type)

    def execute(self, action_type: str, plugin_name: str, **kwargs: Any) -> dict[str, Any]:
        """
        Выполняет действие через плагин, если делегирование разрешено.
        """
        if not self.should_auto_execute(action_type):
            return {
                "executed": False,
                "reason": "Auto execution not allowed",
                "action": action_type
            }

        try:
            plugin = PluginRegistry.get_plugin(plugin_name)
            result = plugin.execute(**kwargs)
            increase_trust(action_type)

            return {
                "executed": True,
                "action": action_type,
                "result": result
            }
        except Exception as e:
            return {
                "executed": False,
                "reason": str(e),
                "action": action_type
            }

    def evaluate_suggestion(self, suggestion: dict[str, Any]) -> str:
        """Решение по suggestion на основе action и confidence."""
        action = str(suggestion.get("action", ""))
        delegation_type = self.LLM_TO_DELEGATION_MAP.get(action)
        if delegation_type is None:
            return "display_only"

        confidence = float(suggestion.get("confidence", 0.0))
        if confidence < 0.75:
            return "display_only"
        if self.should_auto_execute(delegation_type):
            return "auto_execute"
        return "queue_for_approval"

    # ─── Управление переопределениями ──────────────────────────────────

    def set_override(self, action_type: str, enabled: bool) -> None:
        """Ручное переопределение делегирования"""
        self.overrides[action_type] = enabled

    def clear_override(self, action_type: str) -> None:
        if action_type in self.overrides:
            del self.overrides[action_type]

    # ─── Управление правилами делегирования ────────────────────────────

    def add_rule(self, rule: Any) -> None:
        """
        Добавить правило делегирования.

        Правило валидируется перед добавлением. Сохраняет rules.yaml на диск.
        """
        from selfos.delegation_rules import DelegationRule

        if not isinstance(rule, DelegationRule):
            raise TypeError("rule must be a DelegationRule instance")

        self.rules.add(rule)
        assert self._rules is not None
        if self._rules_file is not None:
            self._rules.save(self._rules_file)
        else:
            save_rules(self._rules)

    def remove_rule(self, name: str) -> bool:
        """Удалить правило по имени. Возвращает True если удалено."""
        removed = self.rules.remove(name)
        if removed:
            assert self._rules is not None
            if self._rules_file is not None:
                self._rules.save(self._rules_file)
            else:
                save_rules(self._rules)
        return removed

    def list_rules(self) -> list[dict[str, Any]]:
        """Вернуть список правил как словарей (для CLI)."""
        return [r.to_dict() for r in self.rules.get_all()]

    def get_rule(self, name: str) -> dict[str, Any] | None:
        """Вернуть правило по имени как словарь."""
        rule = self.rules.get(name)
        return rule.to_dict() if rule else None
