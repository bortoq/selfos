#!/usr/bin/env python3
"""
Photo Classifier for Self OS (Phase 2)

Classifies images into categories:
- food
- receipt
- people
- document
- other

Currently uses simple filename-based rules.
Later can be replaced with real computer vision.
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

MEDIA_DIR = Path("media")
DATA_DIR = Path("data/activity")


def classify_photo(filename: str) -> str:
    """Simple rule-based classification"""
    name = filename.lower()

    if any(word in name for word in ["food", "meal", "lunch", "dinner", "breakfast", "eat"]):
        return "food"
    elif any(word in name for word in ["receipt", "check", "bill", "invoice"]):
        return "receipt"
    elif any(word in name for word in ["selfie", "family", "friends", "people", "portrait"]):
        return "people"
    elif any(word in name for word in ["doc", "document", "contract", "pdf", "scan"]):
        return "document"
    else:
        return "other"


def create_photo_event(filename: str, category: str) -> Dict[str, Any]:
    """Create standardized Activity Log event for a photo"""
    timestamp = datetime.now().isoformat() + "Z"

    return {
        "id": f"photo-{filename}",
        "timestamp": timestamp,
        "source": "photo",
        "type": "media",
        "title": f"Photo: {filename}",
        "metadata": {
            "filename": filename,
            "category": category,
            "path": f"media/{filename}"
        }
    }


def save_event(event: Dict[str, Any]):
    """Save event to today's Activity Log file"""
    date = event["timestamp"][:10]
    file_path = DATA_DIR / f"{date}.json"

    events = []
    if file_path.exists():
        with open(file_path, 'r') as f:
            events = json.load(f)

    # Avoid duplicates
    if not any(e["id"] == event["id"] for e in events):
        events.append(event)
        with open(file_path, 'w') as f:
            json.dump(events, f, indent=2, ensure_ascii=False)
        print(f"Saved photo event: {event['id']}")
    else:
        print(f"Duplicate photo skipped: {event['id']}")


def process_photos():
    """Process all photos in the media folder"""
    if not MEDIA_DIR.exists():
        print("Media folder does not exist.")
        return

    for file in MEDIA_DIR.iterdir():
        if file.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]:
            category = classify_photo(file.name)
            event = create_photo_event(file.name, category)
            save_event(event)
            print(f"Processed: {file.name} → {category}")


if __name__ == "__main__":
    process_photos()