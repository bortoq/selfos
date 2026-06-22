#!/usr/bin/env python3
"""
Create Task via Self OS

Allows creating tasks that are recorded in the Activity Log.
Can later be pushed to Todoist or other services via plugins.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

DATA_DIR = Path("data/activity")


def create_task_event(title: str, project: str = "Self OS", priority: int = 2) -> dict[str, Any]:
    """Create a standardized task event"""
    timestamp = datetime.now().isoformat() + "Z"

    return {
        "id": f"task-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "timestamp": timestamp,
        "source": "selfos",
        "type": "task",
        "title": title,
        "metadata": {
            "project": project,
            "priority": priority,
            "created_via": "selfos"
        }
    }


def save_event(event: dict[str, Any]):
    """Save event to today's Activity Log"""
    date = event["timestamp"][:10]
    file_path = DATA_DIR / f"{date}.json"

    events = []
    if file_path.exists():
        with open(file_path) as f:
            events = json.load(f)

    events.append(event)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w') as f:
        json.dump(events, f, indent=2, ensure_ascii=False)

    print(f"Task created and saved: {event['title']}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python create_task.py \"Task title\" [project] [priority]")
        sys.exit(1)

    title = sys.argv[1]
    project = sys.argv[2] if len(sys.argv) > 2 else "Self OS"
    priority = int(sys.argv[3]) if len(sys.argv) > 3 else 2

    event = create_task_event(title, project, priority)
    save_event(event)


if __name__ == "__main__":
    main()