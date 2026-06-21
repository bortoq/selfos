#!/usr/bin/env python3
"""
Daily Summary Generator for Self OS
Creates a short daily summary based on Activity Log.
"""

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

DATA_DIR = Path("data/activity")


def load_today_events():
    today = datetime.now().date().isoformat()
    events = []
    for file in DATA_DIR.glob("*.json"):
        if file.stem == today:
            with open(file) as f:
                events.extend(json.load(f))
    return events


def generate_summary(events):
    if not events:
        return "No activity recorded today."

    categories = defaultdict(int)
    commits = 0
    meetings = 0

    for event in events:
        cat = event.get("metadata", {}).get("category", "Other")
        categories[cat] += 1

        if event["type"] == "commit":
            commits += 1
        if "meeting" in event.get("title", "").lower():
            meetings += 1

    summary = f"Today: {len(events)} events. "
    summary += f"Commits: {commits}. "
    if meetings:
        summary += f"Meetings: {meetings}. "
    summary += "Main categories: " + ", ".join(
        [f"{k}({v})" for k, v in sorted(categories.items(), key=lambda x: -x[1])[:3]]
    )
    return summary


def main():
    events = load_today_events()
    summary = generate_summary(events)
    print("Daily Summary:")
    print(summary)


if __name__ == "__main__":
    main()