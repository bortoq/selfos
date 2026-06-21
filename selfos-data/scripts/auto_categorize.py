#!/usr/bin/env python3
"""
Auto Categorization - commits category directly when trust threshold is reached.
"""

import json
import re
from pathlib import Path

from scripts.trust_manager import can_auto, increase_trust

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


def apply_auto_category(event):
    """Apply category automatically if trust allows"""
    action_type = "event_categorization"
    
    if not can_auto(action_type):
        return False
    
    category = suggest_category(event["title"])
    event.setdefault("metadata", {})["category"] = category
    increase_trust(action_type)
    
    print(f"AUTO: Categorized '{event['title']}' as {category}")
    return True


def main():
    files = sorted(DATA_DIR.glob("*.json"))
    if not files:
        print("No events found.")
        return

    with open(files[-1]) as f:
        events = json.load(f)

    changed = False
    for event in events:
        if "category" in event.get("metadata", {}):
            continue
        
        if apply_auto_category(event):
            changed = True

    if changed:
        with open(files[-1], 'w') as f:
            json.dump(events, f, indent=2, ensure_ascii=False)
        print("Auto-categorized events saved.")
    else:
        print("No auto-categorization performed.")


if __name__ == "__main__":
    main()