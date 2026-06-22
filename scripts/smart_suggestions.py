#!/usr/bin/env python3
"""
Smart Suggestions Engine for Phase 2

Generates intelligent suggestions by combining data from multiple sources:
- Calendar events
- Todoist tasks
- Activity Log

This demonstrates "умные" предложения на основе внешних данных.
"""

from typing import Any


def get_recent_events(days: int = 3) -> list[dict[str, Any]]:
    """Mock function - in real version would read from Activity Log"""
    return [
        {"type": "event", "title": "Team sync meeting", "source": "google_calendar"},
        {"type": "task", "title": "Finish Phase 2 plugins", "source": "todoist"},
        {"type": "commit", "title": "Add photo classifier", "source": "github"},
    ]


def generate_smart_suggestions() -> list[str]:
    """Generate smart suggestions based on recent activity"""
    events = get_recent_events()
    suggestions = []

    # Example logic
    has_meeting = any("meeting" in e["title"].lower() for e in events)
    has_work_task = any(
        "phase" in e["title"].lower()
        or "plugin" in e["title"].lower()
        for e in events
    )

    if has_meeting:
        suggestions.append("Consider blocking focus time after the meeting")

    if has_work_task:
        suggestions.append("You have active work tasks — maybe schedule deep work block?")

    if not suggestions:
        suggestions.append("Everything looks calm today. Good time for reflection.")

    return suggestions


def main():
    print("=== Smart Suggestions ===\n")
    suggestions = generate_smart_suggestions()
    for s in suggestions:
        print(f"- {s}")


if __name__ == "__main__":
    main()