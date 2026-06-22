#!/usr/bin/env python3
"""
Create Task via Self OS (CLI entry point).

Core logic moved to src/selfos/activity.py.
"""

import sys

from selfos.activity import create_task_event, save_event

__all__ = ["create_task_event", "save_event"]


def main():
    if len(sys.argv) < 2:
        print("Usage: python create_task.py \"Task title\" [project] [priority]")
        sys.exit(1)

    title = sys.argv[1]
    project = sys.argv[2] if len(sys.argv) > 2 else "Self OS"
    priority = int(sys.argv[3]) if len(sys.argv) > 3 else 2

    event = create_task_event(title, project, priority)
    save_event(event)


if __name__ == "__main__":
    main()
