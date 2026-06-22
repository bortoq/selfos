from selfos.plugin_registry import PluginRegistry


def test_update_dashboard_basic():
    plugin = PluginRegistry.get_plugin("update_dashboard")
    events = [
        {"timestamp": "2025-06-22T10:00:00Z", "title": "Task done"},
        {"timestamp": "2025-06-22T11:00:00Z", "title": "Postponed task"},
    ]
    result = plugin.execute(events=events, trust={})
    assert result["status"] == "Dashboard updated"
    assert result["events_count"] == 2
    assert 0 <= result["score"] <= 100


def test_update_dashboard_empty():
    plugin = PluginRegistry.get_plugin("update_dashboard")
    result = plugin.execute(events=[], trust={})
    assert result["score"] == 50
    assert result["events_count"] == 0