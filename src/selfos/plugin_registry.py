"""
PluginRegistry — реестр плагинов Self OS.
"""



class PluginRegistry:
    _plugins: dict[str, type] = {}
    _instances: dict[str, object] = {}

    @classmethod
    def register(cls, name: str, plugin_class: type):
        if not name:
            raise ValueError("Plugin name cannot be empty")
        if name in cls._plugins:
            raise ValueError(f"Plugin '{name}' is already registered")
        cls._plugins[name] = plugin_class

    @classmethod
    def get_plugin(cls, name: str, config: dict | None = None) -> object:
        if name not in cls._plugins:
            raise ValueError(f"Plugin '{name}' is not registered")
        if name not in cls._instances:
            plugin_class = cls._plugins[name]
            cls._instances[name] = plugin_class(config or {})
        return cls._instances[name]

    @classmethod
    def list_plugins(cls) -> list[str]:
        return list(cls._plugins.keys())

    @classmethod
    def clear(cls):
        cls._plugins.clear()
        cls._instances.clear()


# === Регистрация плагинов ===

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

PluginRegistry.register("calendar", CalendarPlugin)
PluginRegistry.register("todoist", TodoistPlugin)
PluginRegistry.register("quick_note", QuickNotePlugin)
PluginRegistry.register("categorize", CategorizePlugin)
PluginRegistry.register("daily_summary", DailySummaryPlugin)
PluginRegistry.register("tag_suggestion", TagSuggestionPlugin)
PluginRegistry.register("smart_suggestions", SmartSuggestionsPlugin)
PluginRegistry.register("weekly_report", WeeklyReportPlugin)
PluginRegistry.register("enable_auto", EnableAutoPlugin)
PluginRegistry.register("auto_categorize", AutoCategorizePlugin)
PluginRegistry.register("show_auto_status", ShowAutoStatusPlugin)
PluginRegistry.register("update_dashboard", UpdateDashboardPlugin)