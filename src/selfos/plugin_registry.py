"""
PluginRegistry — реестр плагинов Self OS.

Поддерживает:
- Глобальный экземпляр для production (PluginRegistry.get_plugin())
- Изолированные экземпляры для тестов (PluginRegistry() + .register()/.get())
"""

from typing import Any


class PluginRegistry:
    """Реестр плагинов Self OS (instance-based, с глобальным singleton'ом)."""

    _global_registry: 'PluginRegistry | None' = None

    def __init__(self) -> None:
        self._plugins: dict[str, type] = {}
        self._instances: dict[str, Any] = {}

    # --- Instance API (для изолированных экземпляров, имена ≠ classmethod) ---

    def register(self, name: str, plugin_class: type) -> None:
        """Зарегистрировать класс плагина."""
        if not name:
            raise ValueError("Plugin name cannot be empty")
        if name in self._plugins:
            raise ValueError(f"Plugin '{name}' is already registered")
        self._plugins[name] = plugin_class

    def get(self, name: str, config: dict[str, Any] | None = None) -> Any:
        """Получить экземпляр плагина (без коллизии с classmethod)."""
        if name not in self._plugins:
            raise ValueError(f"Plugin '{name}' is not registered")
        if name not in self._instances:
            plugin_class = self._plugins[name]
            self._instances[name] = plugin_class(config or {})
        return self._instances[name]

    def list_registered(self) -> list[str]:
        """Список зарегистрированных имён плагинов."""
        return list(self._plugins.keys())

    def clear(self) -> None:
        """Очистить реестр и экземпляры."""
        self._plugins.clear()
        self._instances.clear()

    # --- Глобальный singleton ---

    @classmethod
    def _get_global(cls) -> 'PluginRegistry':
        if cls._global_registry is None:
            reg = PluginRegistry()
            _auto_register(reg)
            cls._global_registry = reg
        return cls._global_registry

    # --- Classmethod API (backward compatible, делегируют глобальному экземпляру) ---

    @classmethod
    def get_plugin(cls, name: str, config: dict[str, Any] | None = None) -> Any:
        """Получить плагин из глобального реестра (backward compatible)."""
        return cls._get_global().get(name, config)

    @classmethod
    def list_plugins(cls) -> list[str]:
        """Список плагинов из глобального реестра (backward compatible)."""
        return cls._get_global().list_registered()

    @classmethod
    def clear_global(cls) -> None:
        """Очистить глобальный реестр."""
        cls._get_global().clear()


# === Регистрация плагинов (встроенные) ===

from plugins.auto_categorize_plugin import AutoCategorizePlugin
from plugins.calendar_plugin import CalendarPlugin
from plugins.categorize_plugin import CategorizePlugin
from plugins.daily_summary_plugin import DailySummaryPlugin
from plugins.enable_auto_plugin import EnableAutoPlugin
from plugins.quick_note_plugin import QuickNotePlugin
from plugins.show_auto_status_plugin import ShowAutoStatusPlugin
from plugins.smart_suggestions_plugin import SmartSuggestionsPlugin
from plugins.tag_suggestion_plugin import TagSuggestionPlugin
from plugins.todoist_plugin import TodoistPlugin
from plugins.update_dashboard_plugin import UpdateDashboardPlugin
from plugins.weekly_report_plugin import WeeklyReportPlugin


def _auto_register(registry: PluginRegistry) -> None:
    """Регистрирует все встроенные плагины."""
    registry.register("calendar", CalendarPlugin)
    registry.register("todoist", TodoistPlugin)
    registry.register("quick_note", QuickNotePlugin)
    registry.register("categorize", CategorizePlugin)
    registry.register("daily_summary", DailySummaryPlugin)
    registry.register("tag_suggestion", TagSuggestionPlugin)
    registry.register("smart_suggestions", SmartSuggestionsPlugin)
    registry.register("weekly_report", WeeklyReportPlugin)
    registry.register("enable_auto", EnableAutoPlugin)
    registry.register("auto_categorize", AutoCategorizePlugin)
    registry.register("show_auto_status", ShowAutoStatusPlugin)
    registry.register("update_dashboard", UpdateDashboardPlugin)
