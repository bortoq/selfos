#!/usr/bin/env python3
"""
Import GitHub activity into Self OS Activity Log
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path("data/activity")
DATA_DIR.mkdir(parents=True, exist_ok=True)


def create_event(commit):
    """Create standardized event from GitHub commit data"""
    return {
        "id": f"github-commit-{commit['sha'][:8]}",
        "timestamp": commit['commit']['author']['date'],
        "source": "github",
        "type": "commit",
        "title": commit['commit']['message'].split('\n')[0],
        "metadata": {
            "repo": os.environ.get("GITHUB_REPOSITORY", "unknown"),
            "url": commit['html_url']
        }
    }


def save_event(event):
    """Save event to JSON file"""
    date = event['timestamp'][:10]  # YYYY-MM-DD
    file_path = DATA_DIR / f"{date}.json"

    events = []
    if file_path.exists():
        with open(file_path, 'r') as f:
            events = json.load(f)

    # Avoid duplicates
    if not any(e['id'] == event['id'] for e in events):
        events.append(event)
        with open(file_path, 'w') as f:
            json.dump(events, f, indent=2, ensure_ascii=False)
        print(f"Saved event: {event['id']}")
    else:
        print(f"Duplicate skipped: {event['id']}")


if __name__ == "__main__":
    # Placeholder: In real usage this would fetch from GitHub API
    # For now we create a sample event
    sample_commit = {
        "sha": "abc123def456",
        "commit": {
            "message": "Add Activity Log import script",
            "author": {
                "date": datetime.now(timezone.utc).isoformat()
            }
        },
        "html_url": "https://github.com/example/repo/commit/abc123def456"
    }

    event = create_event(sample_commit)
    save_event(event)
    print("Import completed.")