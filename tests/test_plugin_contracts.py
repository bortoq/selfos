"""Tests for plugin contracts and BaseSelfOSPlugin compliance."""


from selfos.plugin_contracts import (
    CategorizerPlugin,
    NotingPlugin,
    SmartSuggestPlugin,
    SummarizerPlugin,
)
from selfos.plugin_registry import PluginRegistry


def test_all_plugins_return_dict():
    """Каждый selfos-плагин должен возвращать dict при execute()."""
    for name in PluginRegistry.list_plugins():
        plugin = PluginRegistry.get_plugin(name)
        if not hasattr(plugin, 'execute'):
            continue  # external integration stubs (calendar, todoist)
        # Execute with minimal/default kwargs per plugin type
        kwargs = _default_kwargs(name)
        result = plugin.execute(**kwargs)
        assert isinstance(result, dict), (
            f"Plugin '{name}'.execute() вернул {type(result)}, ожидался dict"
        )


def test_all_plugins_have_name_and_description():
    """Каждый плагин должен иметь name и description."""
    for name in PluginRegistry.list_plugins():
        plugin = PluginRegistry.get_plugin(name)
        assert hasattr(plugin, 'name'), f"Plugin '{name}' не имеет атрибута name"
        assert isinstance(plugin.name, str), f"Plugin '{name}'.name не строка"
        assert hasattr(plugin, 'description'), (
            f"Plugin '{name}' не имеет атрибута description"
        )
        assert isinstance(plugin.description, str), (
            f"Plugin '{name}'.description не строка"
        )


def test_quick_note_implements_noting_protocol():
    """quick_note плагин должен соответствовать NotingPlugin."""
    plugin = PluginRegistry.get_plugin("quick_note")
    assert isinstance(plugin, NotingPlugin), (
        "quick_note не соответствует NotingPlugin protocol"
    )


def test_categorize_implements_categorizer_protocol():
    """categorize плагин должен соответствовать CategorizerPlugin."""
    plugin = PluginRegistry.get_plugin("categorize")
    assert isinstance(plugin, CategorizerPlugin), (
        "categorize не соответствует CategorizerPlugin protocol"
    )


def test_auto_categorize_implements_categorizer_protocol():
    """auto_categorize плагин должен соответствовать CategorizerPlugin."""
    plugin = PluginRegistry.get_plugin("auto_categorize")
    assert isinstance(plugin, CategorizerPlugin), (
        "auto_categorize не соответствует CategorizerPlugin protocol"
    )


def test_daily_summary_implements_summarizer_protocol():
    """daily_summary плагин должен соответствовать SummarizerPlugin."""
    plugin = PluginRegistry.get_plugin("daily_summary")
    assert isinstance(plugin, SummarizerPlugin), (
        "daily_summary не соответствует SummarizerPlugin protocol"
    )


def test_smart_suggestions_implements_smart_suggest_protocol():
    """smart_suggestions плагин должен соответствовать SmartSuggestPlugin."""
    plugin = PluginRegistry.get_plugin("smart_suggestions")
    assert isinstance(plugin, SmartSuggestPlugin), (
        "smart_suggestions не соответствует SmartSuggestPlugin protocol"
    )


def test_plugin_registry_isolated_instance():
    """PluginRegistry() даёт изолированный реестр для тестов."""
    registry = PluginRegistry()
    assert registry.list_registered() == []

    # Регистрируем тестовый плагин
    from plugins.quick_note_plugin import QuickNotePlugin
    registry.register("quick_note", QuickNotePlugin)
    plugin = registry.get("quick_note")
    assert plugin is not None

    # Не влияет на глобальный реестр
    assert PluginRegistry.list_plugins() != []
    # В глобальном реестре quick_note уже есть (не перезаписан)
    global_plugin = PluginRegistry.get_plugin("quick_note")
    assert global_plugin is not None


def test_plugin_registry_register_and_clear():
    """Можно регистрировать и очищать плагины в изолированном реестре."""
    registry = PluginRegistry()

    # Создаём тестовый плагин
    from plugins.quick_note_plugin import QuickNotePlugin
    registry.register("test_plugin", QuickNotePlugin)
    assert "test_plugin" in registry.list_registered()

    plugin = registry.get("test_plugin")
    assert plugin is not None

    registry.clear()
    assert registry.list_registered() == []


# --- Хелперы ---

def _default_kwargs(plugin_name: str) -> dict:
    """Возвращает минимальные kwargs для execute() плагина."""
    defaults = {
        "quick_note": {"text": "test"},
        "categorize": {"title": "test meeting"},
        "auto_categorize": {"title": "test"},
        "daily_summary": {"events": []},
        "smart_suggestions": {},
        "tag_suggestion": {},
        "weekly_report": {"events": []},
        "enable_auto": {},
        "show_auto_status": {},
        "update_dashboard": {"events": []},
    }
    return defaults.get(plugin_name, {})
