"""
DailySummaryPlugin — плагин для генерации ежедневной сводки.

Переведён из scripts/daily_summary.py в соответствии с Architecture Contract.
"""

from typing import Any

from selfos.base_selfos_plugin import BaseSelfOSPlugin


class DailySummaryPlugin(BaseSelfOSPlugin):
    """
    Плагин для генерации краткой ежедневной сводки активности.
    """

    name = "daily_summary"
    description = "Generates daily activity summary"

    def __init__(self, config: dict[str, Any] = None):
        super().__init__(config)

    def execute(self, **kwargs: Any) -> dict[str, Any]:
        """
        Генерирует сводку на основе списка событий.
        """
        events = kwargs.get('events', [])
        if not events:
            return {"summary": "No activity recorded today.", "total_events": 0}

        categories: dict[str, int] = {}
        commits = 0
        meetings = 0

        for event in events:
            cat = event.get("metadata", {}).get("category", "Other")
            categories[cat] = categories.get(cat, 0) + 1
            if event.get("type") == "commit":
                commits += 1
            if "meeting" in event.get("title", "").lower():
                meetings += 1

        parts = [f"Today: {len(events)} events.", f"Commits: {commits}."]
        if meetings:
            parts.append(f"Meetings: {meetings}.")
        top = sorted(categories.items(), key=lambda x: -x[1])[:3]
        if top:
            parts.append("Main categories: " + ", ".join(f"{k}({v})" for k, v in top))

        return {
            "summary": " ".join(parts),
            "total_events": len(events),
            "commits": commits,
            "meetings": meetings,
            "categories": dict(categories)
        }