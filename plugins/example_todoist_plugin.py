"""
Example Todoist Plugin for Self OS

Template plugin for importing tasks from Todoist.
"""

from typing import Any

from .base_plugin import BasePlugin


class TodoistPlugin(BasePlugin):
    """
    Plugin for importing tasks from Todoist.
    """

    name = "todoist"
    description = "Imports tasks from Todoist"

    def __init__(self, config: dict[str, Any] = None):
        super().__init__(config)
        self.project_id = self.config.get("project_id")

    def fetch(self) -> list[dict[str, Any]]:
        """
        Fetch tasks from Todoist.
        Currently returns mock data.
        """
        # TODO: Replace with real Todoist API integration
        mock_tasks = [
            {
                "id": "todoist-task-001",
                "timestamp": "2025-06-22T09:15:00Z",
                "source": "todoist",
                "type": "task",
                "title": "Finish Self OS Phase 2 planning",
                "metadata": {
                    "project": "Self OS",
                    "priority": 2
                }
            },
            {
                "id": "todoist-task-002",
                "timestamp": "2025-06-22T11:45:00Z",
                "source": "todoist",
                "type": "task",
                "title": "Buy groceries",
                "metadata": {
                    "project": "Personal",
                    "priority": 3
                }
            }
        ]
        return mock_tasks


if __name__ == "__main__":
    plugin = TodoistPlugin()
    tasks = plugin.fetch()
    for task in tasks:
        print(task)