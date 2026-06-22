"""
WeeklyReportPlugin — плагин для генерации еженедельного отчёта.
"""

from collections import defaultdict
from typing import Any

from selfos.base_selfos_plugin import BaseSelfOSPlugin


class WeeklyReportPlugin(BaseSelfOSPlugin):
    name = "weekly_report"
    description = "Generates weekly activity report"

    def execute(self, **kwargs: Any) -> dict[str, Any]:
        events = kwargs.get('events', [])
        if not events:
            return {"report": "No activity in the last 7 days.", "total_events": 0}

        daily_counts: dict[str, int] = defaultdict(int)
        categories: dict[str, int] = defaultdict(int)
        total_commits = 0

        for event in events:
            date = event.get("timestamp", "")[:10]
            daily_counts[date] += 1
            cat = event.get("metadata", {}).get("category", "Other")
            categories[cat] += 1
            if event.get("type") == "commit":
                total_commits += 1

        report_lines = [
            "# Weekly Report",
            "",
            "**Period:** Last 7 days",
            f"**Total events:** {len(events)}",
            f"**Total commits:** {total_commits}",
            "",
            "## Daily Breakdown",
        ]
        for day in sorted(daily_counts.keys(), reverse=True):
            report_lines.append(f"- {day}: {daily_counts[day]} events")

        report_lines.extend(["", "## Category Distribution"])
        for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
            report_lines.append(f"- {cat}: {count}")

        high_commit_days = [d for d, c in daily_counts.items() if c > 5]
        if high_commit_days:
            report_lines.extend([
                "",
                "**Note:** On days with high activity (>5 events),"
                " consider checking Health category.",
            ])

        return {
            "report": "\n".join(report_lines),
            "total_events": len(events),
            "commits": total_commits,
            "categories": dict(categories),
        }