#!/usr/bin/env python3
"""
Weekly Report Generator for Self OS
Generates a simple weekly activity report.
"""

import json
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

DATA_DIR = Path("data/activity")


def load_last_7_days_events():
    events = []
    today = datetime.now().date()
    
    for i in range(7):
        day = today - timedelta(days=i)
        file = DATA_DIR / f"{day.isoformat()}.json"
        if file.exists():
            with open(file) as f:
                events.extend(json.load(f))
    return events


def generate_weekly_report(events):
    if not events:
        return "No activity in the last 7 days."

    daily_counts = defaultdict(int)
    categories = defaultdict(int)
    total_commits = 0

    for event in events:
        date = event["timestamp"][:10]
        daily_counts[date] += 1
        cat = event.get("metadata", {}).get("category", "Other")
        categories[cat] += 1
        if event["type"] == "commit":
            total_commits += 1

    report = f"""# Weekly Report

**Period:** Last 7 days
**Total events:** {len(events)}
**Total commits:** {total_commits}

## Daily Breakdown
"""
    for day in sorted(daily_counts.keys(), reverse=True):
        report += f"- {day}: {daily_counts[day]} events\n"

    report += "\n## Category Distribution\n"
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        report += f"- {cat}: {count}\n"

    # Simple correlation example
    high_commit_days = [d for d, c in daily_counts.items() if c > 5]
    if high_commit_days:
        report += (
            "\n**Note:** On days with high activity (>5 events),"
            " consider checking Health category.\n"
        )

    return report


def main():
    events = load_last_7_days_events()
    report = generate_weekly_report(events)
    print(report)


if __name__ == "__main__":
    main()