"""
Trust Manager — система доверия для делегирования действий.

Хранит счётчики доверия в data/trust.json и пороги в selfos.yaml.
"""

import json
from typing import Any

import yaml

from selfos.config import config_file, trust_file

TRUST_FILE = trust_file()
CONFIG_FILE = config_file()

NEW_ACTIONS = [
    "photo_classification",
    "calendar_import",
    "todoist_import",
    "quick_note",
]


def load_config() -> dict[str, Any]:
    """Load config from selfos.yaml"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            result = yaml.safe_load(f)
            return result if isinstance(result, dict) else {}
    return {}


def load_trust() -> dict[str, int]:
    if TRUST_FILE.exists():
        with open(TRUST_FILE) as f:
            result: dict[str, int] = json.load(f)
            return result
    return {}


def save_trust(trust: dict[str, int]) -> None:
    TRUST_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TRUST_FILE, 'w') as f:
        json.dump(trust, f, indent=2)


def get_threshold(action_type: str) -> int:
    config = load_config()
    thresholds = config.get("trust_thresholds", {})
    defaults = {
        "photo_classification": 6,
        "calendar_import": 8,
        "todoist_import": 8,
        "quick_note": 5,
    }
    val = thresholds.get(action_type, defaults.get(action_type, 10))
    return int(val)


def is_force_review(action_type: str) -> bool:
    config = load_config()
    force = config.get("force_review", {})
    val = force.get(action_type, False)
    return bool(val)


def increase_trust(action_type: str) -> int:
    trust = load_trust()
    trust[action_type] = trust.get(action_type, 0) + 1
    save_trust(trust)
    return trust[action_type]


def reset_trust(action_type: str) -> None:
    trust = load_trust()
    if action_type in trust:
        del trust[action_type]
        save_trust(trust)


def can_auto(action_type: str) -> bool:
    if is_force_review(action_type):
        return False
    trust = load_trust()
    threshold = get_threshold(action_type)
    return trust.get(action_type, 0) >= threshold


def get_all_actions_status() -> dict[str, dict[str, Any]]:
    trust = load_trust()
    result: dict[str, dict[str, Any]] = {}
    for action in NEW_ACTIONS + ["event_categorization", "daily_summary"]:
        threshold = get_threshold(action)
        current = trust.get(action, 0)
        auto = can_auto(action)
        result[action] = {
            "current": current,
            "threshold": threshold,
            "status": "AUTO" if auto else "REVIEW",
        }
    return result
