import pytest
from plugins.quick_note_plugin import QuickNotePlugin


def test_quick_note_plugin_execute():
    plugin = QuickNotePlugin()
    result = plugin.execute(text="Had a team meeting today")
    assert "event" in result
    assert "suggestions" in result
    assert result["suggestions"]["suggested_category"] == "Work"