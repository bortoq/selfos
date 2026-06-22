from plugins.categorize_plugin import CategorizePlugin


def test_categorize_plugin():
    plugin = CategorizePlugin()
    result = plugin.execute(title="Morning gym session")
    assert result["suggested_category"] == "Health"