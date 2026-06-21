"""
Todoist Plugin for Self OS

Fetches tasks from Todoist.
"""

from typing import Any

from .base_plugin import BasePlugin


class TodoistPlugin(BasePlugin):
    name = "todoist"
    description = "Imports tasks from Todoist"

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self.project_id = self.config.get("project_id")

    def fetch(self) -> list[dict[str, Any]]:
        """
        Fetch tasks from Todoist.
        Currently returns mock data.
        """
        # TODO: Replace with real Todoist REST API
        tasks = [
            {
                "id": "todoist-task-demo-1",
                "timestamp": "2025-06-21T09:30:00Z",
                "source": "todoist",
                "type": "task",
                "title": "Review Phase 2 plugins",
                "metadata": {
                    "project": "Self OS",
                    "priority": 2,
                    "labels": ["planning"]
                }
            },
            {
                "id": "todoist-task-demo-2",
                "timestamp": "2025-06-21T11:00:00Z",
                "source": "todoist",
                "type": "task",
                "title": "Buy milk and bread",
                "metadata": {
                    "project": "Personal",
                    "priority": 3
                }
            }
        ]
        return tasks

    def push(self, event: dict[str, Any]) -> bool:
        """
        Create a new task in Todoist (stub).
        """
        print(f"[Todoist] Would create task: {event.get('title')}")
        return True
