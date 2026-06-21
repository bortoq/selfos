#!/usr/bin/env python3
"""
Quick Note with Delegation

User writes a note → system suggests tags and category.
This demonstrates the delegation pattern for note-taking.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

DATA_DIR = Path("data/activity")


def suggest_tags_and_category(text: str) -> dict[str, Any]:
    """Simple rule-based suggestion engine for notes"""
    text_lower = text.lower()
    tags = []
    category = "Other"

    # Tag suggestions
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


def create_note_event(text: str, tags: list[str], category: str) -> dict[str, Any]:
    """Create a note event with suggestions"""
    timestamp = datetime.now().isoformat() + "Z"

    return {
        "id": f"note-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "timestamp": timestamp,
        "source": "selfos",
        "type": "note",
        "title": text[:80] + ("..." if len(text) > 80 else ""),
        "metadata": {
            "full_text": text,
            "tags": tags,
            "category": category,
            "delegation_status": "suggested"
        }
    }


def save_event(event: dict[str, Any]):
    date = event["timestamp"][:10]
    file_path = DATA_DIR / f"{date}.json"

    events = []
    if file_path.exists():
        with open(file_path) as f:
            events = json.load(f)

    events.append(event)
    with open(file_path, 'w') as f:
        json.dump(events, f, indent=2, ensure_ascii=False)

    print("Quick Note saved with suggestions.")


def main():
    if len(sys.argv) < 2:
        print("Usage: python quick_note.py \"Your note text here\"")
        sys.exit(1)

    text = " ".join(sys.argv[1:])

    suggestions = suggest_tags_and_category(text)

    print("\n=== Quick Note Delegation ===")
    print(f"Note: {text}")
    print(f"Suggested tags: {', '.join(suggestions['suggested_tags'])}")
    print(f"Suggested category: {suggestions['suggested_category']}")
    print("=============================\n")

    # In real usage, user would confirm or edit suggestions
    # For now we accept the suggestions automatically
    event = create_note_event(
        text,
        suggestions["suggested_tags"],
        suggestions["suggested_category"]
    )
    save_event(event)


if __name__ == "__main__":
    main()