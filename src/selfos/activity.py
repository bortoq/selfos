"""
Activity Log — запись событий в Activity Log.

Функции для создания и сохранения стандартизированных событий.
Используется Scheduler и EmailService вместо прямых импортов из scripts/.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

DATA_DIR = Path("data/activity")


def create_task_event(
    title: str, project: str = "Self OS", priority: int = 2
) -> dict[str, Any]:
    """Create a standardized task event"""
    now = datetime.now(timezone.utc)
    timestamp = now.isoformat()

    return {
        "id": str(uuid4()),
        "timestamp": timestamp,
        "source": "selfos",
        "type": "task",
        "title": title,
        "metadata": {
            "project": project,
            "priority": priority,
            "created_via": "selfos",
        },
    }


def save_event(event: dict[str, Any]) -> None:
    """Save event to today's Activity Log"""
    date = event["timestamp"][:10]
    file_path = DATA_DIR / f"{date}.json"

    events: list[dict[str, Any]] = []
    if file_path.exists():
        with open(file_path) as f:
            events = json.load(f)

    events.append(event)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w') as f:
        json.dump(events, f, indent=2, ensure_ascii=False)
