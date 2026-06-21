#!/usr/bin/env python3
"""
Trust Manager for Self OS Phase 1
Handles trust levels, thresholds, and reset functionality.
"""

import json
from pathlib import Path

import yaml

TRUST_FILE = Path("data/trust.json")
CONFIG_FILE = Path("selfos.yaml")


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
    return thresholds.get(action_type, 10)


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


if __name__ == "__main__":
    # Demo usage
    print("Current thresholds:")
    for action in ["event_categorization", "daily_summary", "tag_suggestion"]:
        print(f"  {action}: {get_threshold(action)}")

    count = increase_trust("event_categorization")
    print(f"\nTrust for event_categorization: {count}")
    print(f"Can run auto: {can_auto('event_categorization')}")