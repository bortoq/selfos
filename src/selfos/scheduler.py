"""
Scheduler Module for Self OS (Phase 3)

Простой встроенный планировщик задач и событий.
Заменяет базовые функции Todoist + Calendar.
"""

from datetime import datetime, timedelta
from typing import Any

from scripts.create_task import create_task_event
from scripts.create_task import save_event as save_activity


class Scheduler:
    """
    Встроенный планировщик задач и событий Self OS.
    """

    def __init__(self):
        self.tasks: list[dict[str, Any]] = []
        self.events: list[dict[str, Any]] = []

    def add_task(self, title: str, due_date: str = None, priority: int = 2) -> dict[str, Any]:
        """Добавить задачу"""
        task = create_task_event(title, project="Scheduler", priority=priority)
        task["metadata"]["due_date"] = due_date
        task["metadata"]["status"] = "pending"

        self.tasks.append(task)
        save_activity(task)
        return task

    def add_event(self, title: str, start_time: str, duration_minutes: int = 60) -> dict[str, Any]:
        """Добавить событие (встречу)"""
        event = {
            "id": f"event-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "timestamp": start_time,
            "source": "selfos",
            "type": "event",
            "title": title,
            "metadata": {
                "duration_minutes": duration_minutes,
                "created_via": "scheduler"
            }
        }
        self.events.append(event)
        save_activity(event)
        return event

    def list_tasks(self, status: str = None) -> list[dict[str, Any]]:
        """Получить список задач"""
        if status:
            return [t for t in self.tasks if t["metadata"].get("status") == status]
        return self.tasks

    def list_upcoming_events(self, days: int = 7) -> list[dict[str, Any]]:
        """Получить события на ближайшие N дней"""
        now = datetime.now()
        future = now + timedelta(days=days)
        return [
            e for e in self.events 
            if now.isoformat() <= e["timestamp"] <= future.isoformat()
        ]

    def complete_task(self, task_id: str) -> bool:
        """Отметить задачу выполненной"""
        for task in self.tasks:
            if task["id"] == task_id:
                task["metadata"]["status"] = "completed"
                return True
        return False