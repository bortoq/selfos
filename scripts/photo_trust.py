#!/usr/bin/env python3
"""
Photo Classification Trust Handler

Extends trust system to photo_classification action.
"""

from scripts.trust_manager_v2 import can_auto, get_threshold, increase_trust


def classify_and_trust(filename: str, suggested_category: str) -> dict:
    """
    Simulate photo classification with trust tracking.
    """
    action_type = "photo_classification"

    if can_auto(action_type):
        # Auto mode - apply classification directly
        print(f"[AUTO] Photo '{filename}' classified as {suggested_category}")
        increase_trust(action_type)
        return {
            "status": "auto",
            "category": suggested_category
        }
    else:
        # Review mode
        print(f"[REVIEW] Suggested: {filename} → {suggested_category}")
        print(f"Current trust: {increase_trust(action_type)} / {get_threshold(action_type)}")
        return {
            "status": "review",
            "category": suggested_category
        }


if __name__ == "__main__":
    # Demo
    classify_and_trust("lunch.jpg", "food")
    classify_and_trust("receipt_001.png", "receipt")