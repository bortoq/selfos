#!/usr/bin/env python3
"""
Tag Suggestion Engine for Self OS
Suggests relevant tags for events.
"""

import json
import re
from pathlib import Path

DATA_DIR = Path("data/activity")

TAG_RULES = [
    (r"(urgent|asap|deadline)", ["urgent"]),
    (r"(meeting|call|sync)", ["meeting"]),
    (r"(bug|fix|error)", ["bug"]),
    (r"(feature|implement|add)", ["feature"]),
    (r"(review|pr|pull request)", ["review"]),
    (r"(personal|family|friend)", ["personal"]),
]


def suggest_tags(title: str):
    tags = set()
    title_lower = title.lower()
    for pattern, tag_list in TAG_RULES:
        if re.search(pattern, title_lower):
            tags.update(tag_list)
    return list(tags) if tags else ["general"]


def main():
    files = sorted(DATA_DIR.glob("*.json"))
    if not files:
        print("No events found.")
        return

    with open(files[-1]) as f:
        events = json.load(f)

    for event in events[-5:]:
        tags = suggest_tags(event["title"])
        print(f"Event: {event['title']}")
        print(f"Suggested tags: {', '.join(tags)}\n")


if __name__ == "__main__":
    main()