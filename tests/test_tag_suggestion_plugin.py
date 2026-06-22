import pytest
from plugins.tag_suggestion_plugin import TagSuggestionPlugin


def test_tag_suggestion_plugin():
    plugin = TagSuggestionPlugin()
    result = plugin.execute(title="Urgent bug fix needed")
    assert "bug" in result["suggested_tags"]