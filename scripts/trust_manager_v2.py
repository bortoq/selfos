#!/usr/bin/env python3
"""
Trust Manager v2 for Phase 2 (CLI entry point).

Core logic moved to src/selfos/trust.py.
"""

from selfos.trust import (
    can_auto,
    get_all_actions_status,
    get_threshold,
    increase_trust,
    is_force_review,
    load_config,
    load_trust,
    reset_trust,
    save_trust,
)

__all__ = [
    "can_auto",
    "get_all_actions_status",
    "get_threshold",
    "increase_trust",
    "is_force_review",
    "load_config",
    "load_trust",
    "reset_trust",
    "save_trust",
]


def main():
    print("=== Trust Status (Phase 2) ===\n")
    status = get_all_actions_status()
    for action, data in status.items():
        print(f"{action:25} | {data['status']:6} | {data['current']}/{data['threshold']}")


if __name__ == "__main__":
    main()
