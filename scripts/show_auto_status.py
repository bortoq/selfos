#!/usr/bin/env python3
"""
Shows which actions are currently in auto mode.
"""

from pathlib import Path

import yaml

from scripts.trust_manager import can_auto, get_threshold, load_trust

CONFIG_FILE = Path("selfos.yaml")


def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            return yaml.safe_load(f)
    return {}


def main():
    trust = load_trust()
    actions = ["event_categorization", "daily_summary", "tag_suggestion"]

    print("=== Auto Mode Status ===\n")
    
    for action in actions:
        threshold = get_threshold(action)
        current = trust.get(action, 0)
        auto_enabled = can_auto(action)
        
        status = "AUTO" if auto_enabled else "REVIEW"
        print(f"{action:25} | {status:6} | {current}/{threshold}")


if __name__ == "__main__":
    main()