from selfos.plugin_registry import PluginRegistry


def test_weekly_report_empty():
    plugin = PluginRegistry.get_plugin("weekly_report")
    result = plugin.execute(events=[])
    assert "No activity" in result["report"]


def test_weekly_report_basic():
    plugin = PluginRegistry.get_plugin("weekly_report")
    events = [
        {"timestamp": "2025-06-20T10:00:00Z", "type": "commit", "title": "Fix bug"},
        {"timestamp": "2025-06-21T14:00:00Z", "type": "event", "title": "Meeting"},
        {"timestamp": "2025-06-22T09:00:00Z", "type": "commit", "title": "Add tests"},
    ]
    result = plugin.execute(events=events)
    assert len(result["report"]) > 50
    assert result["total_events"] == 3
    assert result["commits"] == 2


def test_weekly_report_categories():
    plugin = PluginRegistry.get_plugin("weekly_report")
    events = [
        {"timestamp": "2025-06-20T10:00:00Z", "type": "event", "metadata": {"category": "Work"}},
        {"timestamp": "2025-06-21T14:00:00Z", "type": "event", "metadata": {"category": "Health"}},
    ]
    result = plugin.execute(events=events)
    assert "Work" in result["report"]
    assert "Health" in result["report"]
    assert result["total_events"] == 2