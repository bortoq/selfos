"""
WeeklyReportPlugin — плагин для генерации еженедельного отчёта.
"""

from typing import Any

from selfos.base_selfos_plugin import BaseSelfOSPlugin


class WeeklyReportPlugin(BaseSelfOSPlugin):
    name = "weekly_report"
    description = "Generates weekly activity report"

    def execute(self, events: list[dict[str, Any]] = None, **kwargs) -> dict[str, Any]:
        events = events or []
        if not events:
            return {"report": "No activity in the last 7 days."}

        total = len(events)
        commits = sum(1 for e in events if e.get("type") == "commit")

        return {
            "report": f"Weekly Report: {total} events, {commits} commits",
            "total_events": total,
            "commits": commits
        }