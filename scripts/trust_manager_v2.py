#!/usr/bin/env python3
"""
Trust Manager v2 for Phase 2

Extends trust system to support new action types:
- photo_classification
- calendar_import
- todoist_import
- quick_note
"""

import json
from pathlib import Path

import yaml

TRUST_FILE = Path("data/trust.json")
CONFIG_FILE = Path("selfos.yaml")

NEW_ACTIONS = [
    "photo_classification",
    "calendar_import",
    "todoist_import",
    "quick_note"
]


def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            return yaml.safe_load(f)
    return {}


def load_trust():
    if TRUST_FILE.exists():
        with open(TRUST_FILE) as f:
            return json.load(f)
    return {}


def save_trust(trust):
    TRUST_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TRUST_FILE, 'w') as f:
        json.dump(trust, f, indent=2)


def get_threshold(action_type: str) -> int:
    config = load_config()
    thresholds = config.get("trust_thresholds", {})
    # Default thresholds for new actions
    defaults = {
        "photo_classification": 6,
        "calendar_import": 8,
        "todoist_import": 8,
        "quick_note": 5
    }
    return thresholds.get(action_type, defaults.get(action_type, 10))


def is_force_review(action_type: str) -> bool:
    config = load_config()
    force = config.get("force_review", {})
    return force.get(action_type, False)


def increase_trust(action_type: str) -> int:
    trust = load_trust()
    trust[action_type] = trust.get(action_type, 0) + 1
    save_trust(trust)
    return trust[action_type]


def reset_trust(action_type: str):
    trust = load_trust()
    if action_type in trust:
        del trust[action_type]
        save_trust(trust)
    print(f"Trust counter for '{action_type}' has been reset.")


def can_auto(action_type: str) -> bool:
    if is_force_review(action_type):
        return False
    trust = load_trust()
    threshold = get_threshold(action_type)
    return trust.get(action_type, 0) >= threshold


def get_all_actions_status():
    """Return status of all known actions"""
    trust = load_trust()
    result = {}
    for action in NEW_ACTIONS + ["event_categorization", "daily_summary"]:
        threshold = get_threshold(action)
        current = trust.get(action, 0)
        auto = can_auto(action)
        result[action] = {
            "current": current,
            "threshold": threshold,
            "status": "AUTO" if auto else "REVIEW"
        }
    return result


if __name__ == "__main__":
    print("=== Trust Status (Phase 2) ===\n")
    status = get_all_actions_status()
    for action, data in status.items():
        print(f"{action:25} | {data['status']:6} | {data['current']}/{data['threshold']}")