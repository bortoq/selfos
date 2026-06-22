from selfos.plugin_registry import PluginRegistry


def test_smart_suggestions_returns_list():
    plugin = PluginRegistry.get_plugin("smart_suggestions")
    result = plugin.execute(recent_events=[])
    assert isinstance(result["suggestions"], list)
    assert len(result["suggestions"]) > 0


def test_smart_suggestions_content():
    plugin = PluginRegistry.get_plugin("smart_suggestions")
    events = [
        {"type": "event", "title": "Team sync meeting"},
        {"type": "task", "title": "Finish Phase 2 plugins"},
    ]
    result = plugin.execute(recent_events=events)
    text = " ".join(result["suggestions"]).lower()
    assert any(word in text for word in ["focus", "meeting", "work", "deep"])