"""
QuickNotePlugin — плагин для создания заметок с делегированием.

Переведён из scripts/quick_note.py в соответствии с Architecture Contract.
"""

from typing import Any

from selfos.base_selfos_plugin import BaseSelfOSPlugin
from selfos.event_factory import EventFactory


def suggest_tags_and_category(text: str) -> dict[str, Any]:
    """Простая rule-based логика для предложения тегов и категории"""
    text_lower = text.lower()
    tags = []
    category = "Other"

    if any(word in text_lower for word in ["meeting", "call", "sync"]):
        tags.append("meeting")
        category = "Work"
    if any(word in text_lower for word in ["idea", "thought", "remember"]):
        tags.append("idea")
    if any(word in text_lower for word in ["buy", "shop", "need"]):
        tags.append("shopping")
        category = "Personal"
    if any(word in text_lower for word in ["health", "gym", "doctor"]):
        tags.append("health")
        category = "Health"

    if not tags:
        tags = ["note"]

    return {
        "suggested_tags": tags,
        "suggested_category": category
    }


class QuickNotePlugin(BaseSelfOSPlugin):
    """
    Плагин для создания заметок с автоматическим предложением тегов и категории.
    """

    name = "quick_note"
    description = "Creates notes with delegation (tag and category suggestions)"

    def __init__(self, config: dict[str, Any] = None):
        super().__init__(config)

    def execute(self, text: str, **kwargs) -> dict[str, Any]:
        """
        Создаёт заметку с делегированием.
        """
        suggestions = suggest_tags_and_category(text)

        event = EventFactory.create_note_event(
            title=text[:80] + ("..." if len(text) > 80 else ""),
            tags=suggestions["suggested_tags"],
            category=suggestions["suggested_category"],
            full_text=text,
            delegation_status="suggested"
        )

        return {
            "event": event,
            "suggestions": suggestions
        }
