"""
Example Calendar Plugin for Self OS

This is a template plugin for importing calendar events.
In a real implementation it would connect to Google Calendar, Outlook, etc.
"""

from typing import Any

from .base_plugin import BasePlugin


class CalendarPlugin(BasePlugin):
    """
    Plugin for importing calendar events.

    In production this would use Google Calendar API, Microsoft Graph, etc.
    """

    name = "calendar"
    description = "Imports events from calendar services"

    def __init__(self, config: dict[str, Any] = None):
        super().__init__(config)
        self.calendar_id = self.config.get("calendar_id", "primary")

    def fetch(self) -> list[dict[str, Any]]:
        """
        Fetch calendar events.
        Currently returns mock data for demonstration.
        """
        # TODO: Replace with real API call
        mock_events = [
            {
                "id": f"calendar-{self.calendar_id}-1",
                "timestamp": "2025-06-22T10:00:00Z",
                "source": "calendar",
                "type": "event",
                "title": "Team sync meeting",
                "metadata": {
                    "location": "Google Meet",
                    "attendees": 5
                }
            },
            {
                "id": f"calendar-{self.calendar_id}-2",
                "timestamp": "2025-06-22T14:30:00Z",
                "source": "calendar",
                "type": "event",
                "title": "Dentist appointment",
                "metadata": {
                    "location": "Dental Clinic"
                }
            }
        ]
        return mock_events

    def validate_config(self) -> bool:
        return "calendar_id" in self.config or True  # calendar_id is optional in demo


# Usage example
if __name__ == "__main__":
    plugin = CalendarPlugin({"calendar_id": "primary"})
    events = plugin.fetch()
    for event in events:
        print(event)