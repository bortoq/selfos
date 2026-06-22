"""
EventFactory — единая фабрика для создания событий в Activity Log.

Все события в Self OS должны создаваться только через эту фабрику.
"""

from datetime import datetime
from typing import Any


class EventFactory:
    """
    Централизованная фабрика событий.
    Обеспечивает единообразие структуры событий.
    """

    @staticmethod
    def create_event(
        source: str,
        event_type: str,
        title: str,
        metadata: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Создаёт стандартизированное событие.

        Args:
            source: Источник события (например: "selfos", "github", "email")
            event_type: Тип события (например: "task", "note", "email", "event")
            title: Краткое описание события
            metadata: Дополнительные данные

        Returns:
            Словарь события в едином формате
        """
        if not source:
            raise ValueError("source cannot be empty")
        if not event_type:
            raise ValueError("event_type cannot be empty")
        if not title:
            raise ValueError("title cannot be empty")

        event = {
            "id": f"{event_type}-{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            "timestamp": datetime.now().isoformat() + "Z",
            "source": source,
            "type": event_type,
            "title": title,
            "metadata": metadata or {}
        }

        return event

    @staticmethod
    def create_task_event(
        title: str,
        project: str = "Self OS",
        priority: int = 2,
        **extra_metadata
    ) -> dict[str, Any]:
        """Создаёт событие задачи"""
        metadata = {
            "project": project,
            "priority": priority,
            **extra_metadata
        }
        return EventFactory.create_event("selfos", "task", title, metadata)

    @staticmethod
    def create_note_event(
        title: str,
        tags: list = None,
        category: str = "Other",
        **extra_metadata
    ) -> dict[str, Any]:
        """Создаёт событие заметки"""
        metadata = {
            "tags": tags or [],
            "category": category,
            **extra_metadata
        }
        return EventFactory.create_event("selfos", "note", title, metadata)

    @staticmethod
    def create_email_event(
        to: str,
        subject: str,
        delegation_status: str = "review",
        **extra_metadata
    ) -> dict[str, Any]:
        """Создаёт событие email"""
        metadata = {
            "to": to,
            "subject": subject,
            "delegation_status": delegation_status,
            **extra_metadata
        }
        title = f"Email to {to}: {subject}"
        return EventFactory.create_event("selfos", "email", title, metadata)