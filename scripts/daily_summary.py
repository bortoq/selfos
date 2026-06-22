#!/usr/bin/env python3
"""
Daily Summary — thin wrapper over daily_summary plugin.
"""

from selfos.plugin_registry import PluginRegistry


def main():
    import json
    from datetime import datetime
    from pathlib import Path

    from selfos.config import data_dir

    today = datetime.now().date().isoformat()
    events = []
    for file in Path(data_dir()).glob("*.json"):
        if file.stem == today:
            with open(file) as f:
                events.extend(json.load(f))

    plugin = PluginRegistry.get_plugin("daily_summary")
    result = plugin.execute(events=events)
    print("Daily Summary:")
    print(result["summary"])


if __name__ == "__main__":
    main()