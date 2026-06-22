import pytest
from plugins.calendar_plugin import CalendarPlugin


def test_calendar_plugin_fetch_returns_list():
    plugin = CalendarPlugin()
    events = plugin.fetch()
    assert isinstance(events, list)
    assert len(events) > 0


def test_calendar_plugin_name():
    plugin = CalendarPlugin()
    assert plugin.name == "google_calendar"


def test_calendar_plugin_validate():
    plugin = CalendarPlugin()
    assert plugin.validate_config() is True