"""
Google Calendar Plugin for Self OS

Fetches events from Google Calendar.
In real usage requires OAuth2 credentials.
"""

from datetime import datetime, timedelta
from typing import Any

from .base_plugin import BasePlugin


class CalendarPlugin(BasePlugin):
    name = "google_calendar"
    description = "Imports events from Google Calendar"

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self.calendar_id = self.config.get("calendar_id", "primary")
        self.days_back = self.config.get("days_back", 7)

    def fetch(self) -> list[dict[str, Any]]:
        """
        Fetch calendar events.
        Currently returns mock data. Replace with real Google Calendar API call.
        """
        # TODO: Implement real Google Calendar API integration
        # For now we return mock events
        now = datetime.now()
        events = [
            {
                "id": f"gcal-{self.calendar_id}-mock1",
                "timestamp": (now - timedelta(days=1)).isoformat() + "Z",
                "source": "google_calendar",
                "type": "event",
                "title": "Project sync meeting",
                "metadata": {
                    "calendar_id": self.calendar_id,
                    "location": "Google Meet",
                    "attendees": 4
                }
            },
            {
                "id": f"gcal-{self.calendar_id}-mock2",
                "timestamp": (now - timedelta(days=2)).isoformat() + "Z",
                "source": "google_calendar",
                "type": "event",
                "title": "Dentist appointment",
                "metadata": {
                    "calendar_id": self.calendar_id,
                    "location": "Clinic"
                }
            }
        ]
        return events

    def validate_config(self) -> bool:
        return True  # In production would check for credentials
