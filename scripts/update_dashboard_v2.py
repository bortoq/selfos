#!/usr/bin/env python3
"""
Update Dashboard — thin wrapper over update_dashboard plugin.
"""

import json
from pathlib import Path

from selfos.config import data_dir, trust_file
from selfos.plugin_registry import PluginRegistry


def main():
    # Load data
    events = []
    for file in Path(data_dir()).glob("*.json"):
        with open(file) as f:
            events.extend(json.load(f))

    trust = {}
    tf = trust_file()
    if tf.exists():
        with open(tf) as f:
            trust = json.load(f)

    plugin = PluginRegistry.get_plugin("update_dashboard")
    result = plugin.execute(events=events, trust=trust)

    print(result["status"])
    print(f"Events: {result['events_count']}")
    print(f"Score: {result['score']}/100")
    print(f"Actions: {result['suggested_actions']}")


if __name__ == "__main__":
    main()