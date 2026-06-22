#!/usr/bin/env python3
"""
Event Categorization Engine for Self OS
Suggests category for new events.
In Review mode it creates GitHub Issues.
"""

import json
import os
import re
import sys
from pathlib import Path

DATA_DIR = Path("data/activity")
CATEGORIES = ["Work", "Personal", "Health", "Finance", "Other"]

RULES = [
    (r"(meeting|standup|call|sync)", "Work"),
    (r"(gym|run|sport|health|doctor)", "Health"),
    (r"(buy|shop|payment|invoice|salary)", "Finance"),
    (r"(family|friend|birthday|vacation)", "Personal"),
]


def suggest_category(title: str) -> str:
    title_lower = title.lower()
    for pattern, category in RULES:
        if re.search(pattern, title_lower):
            return category
    return "Other"


def create_issue_suggestion(event, category):
    """Simulate creating a GitHub Issue (in real run it would use GitHub API)"""
    print(f"::notice::Suggestion: Categorize '{event['title']}' as {category}")
    print(f"Event ID: {event['id']}")
    # In production this would call GitHub API to create an Issue


def main():
    create_issue = "--create-issue" in sys.argv

    files = sorted(DATA_DIR.glob("*.json"))
    if not files:
        print("No events found.")
        return

    with open(files[-1], 'r') as f:
        events = json.load(f)

    for event in events[-5:]:
        if event.get("metadata", {}).get("category"):
            continue

        suggested = suggest_category(event["title"])

        if create_issue:
            create_issue_suggestion(event, suggested)
        else:
            print(f"Event: {event['title']} → Suggested: {suggested}")

    print("Categorization completed.")


if __name__ == "__main__":
    main()