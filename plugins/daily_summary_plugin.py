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
        events = kwargs['events']
        """
        Генерирует сводку на основе списка событий.
        """
        if not events:
            return {"summary": "No activity recorded today."}

        commits = sum(1 for e in events if e.get("type") == "commit")
        meetings = sum(1 for e in events if "meeting" in e.get("title", "").lower())

        categories: dict[str, int] = {}
        for event in events:
            cat = event.get("metadata", {}).get("category", "Other")
            categories[cat] = categories.get(cat, 0) + 1

        summary = f"Today: {len(events)} events. Commits: {commits}."
        if meetings:
            summary += f" Meetings: {meetings}."

        return {
            "summary": summary,
            "total_events": len(events),
            "commits": commits,
            "meetings": meetings,
            "categories": categories
        }