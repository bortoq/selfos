from plugins.todoist_plugin import TodoistPlugin


def test_todoist_plugin_fetch_returns_list():
    plugin = TodoistPlugin()
    tasks = plugin.fetch()
    assert isinstance(tasks, list)
    assert len(tasks) > 0


def test_todoist_plugin_push():
    plugin = TodoistPlugin()
    event = {"title": "Test task"}
    result = plugin.push(event)
    assert result is True


def test_todoist_plugin_name():
    plugin = TodoistPlugin()
    assert plugin.name == "todoist"