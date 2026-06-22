"""
DelegationEngine — центральный компонент глубокого делегирования (Phase 3, Этап 4).

Отвечает за:
- Zero-input delegation
- Приоритеты и исключения
- Автоматическое выполнение действий при высоком уровне доверия
"""

from typing import Dict, Any, Callable, Optional
from src.selfos.plugin_registry import PluginRegistry
from scripts.trust_manager_v2 import can_auto, get_threshold, increase_trust


class DelegationEngine:
    """
    Движок глубокого делегирования.
    """

    # Критически важные действия, которые никогда не должны выполняться автоматически
    CRITICAL_ACTIONS = {
        "email_send",      # Отправка писем
        "delete_data",     # Удаление данных
        "financial_transaction"
    }

    def __init__(self):
        self.overrides: Dict[str, bool] = {}  # Ручные переопределения

    def should_auto_execute(self, action_type: str, force: bool = False) -> bool:
        """
        Определяет, можно ли выполнить действие автоматически.
        """
        # Ручное переопределение имеет высший приоритет
        if action_type in self.overrides:
            return self.overrides[action_type]

        # Критические действия не выполняются автоматически
        if action_type in self.CRITICAL_ACTIONS and not force:
            return False

        return can_auto(action_type)

    def execute(self, action_type: str, plugin_name: str, **kwargs) -> Dict[str, Any]:
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

    def set_override(self, action_type: str, allow_auto: bool):
        """Ручное переопределение делегирования"""
        self.overrides[action_type] = allow_auto

    def clear_override(self, action_type: str):
        if action_type in self.overrides:
            del self.overrides[action_type]