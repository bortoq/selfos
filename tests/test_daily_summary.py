from selfos.plugin_registry import PluginRegistry


def test_daily_summary_empty():
    plugin = PluginRegistry.get_plugin("daily_summary")
    result = plugin.execute(events=[])
    assert result["summary"] == "No activity recorded today."


def test_daily_summary_basic():
    plugin = PluginRegistry.get_plugin("daily_summary")
    events = [
        {"type": "commit", "title": "Fix bug"},
        {"type": "event", "title": "Team meeting"},
        {"type": "commit", "title": "Add tests"},
    ]
    result = plugin.execute(events=events)
    assert "3 events" in result["summary"]
    assert "Commits: 2" in result["summary"]
    assert "Meetings: 1" in result["summary"]


def test_daily_summary_categories():
    plugin = PluginRegistry.get_plugin("daily_summary")
    events = [
        {"type": "commit", "title": "Work task", "metadata": {"category": "Work"}},
        {"type": "event", "title": "Gym", "metadata": {"category": "Health"}},
    ]
    result = plugin.execute(events=events)
    assert "Work" in result["summary"] or "Health" in result["summary"]
    assert result["total_events"] == 2