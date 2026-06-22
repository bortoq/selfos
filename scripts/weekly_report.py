#!/usr/bin/env python3
"""
Weekly Report — thin wrapper over weekly_report plugin.
"""

from selfos.plugin_registry import PluginRegistry


def main():
    import json
    from datetime import datetime, timedelta
    from pathlib import Path

    from selfos.config import data_dir

    today = datetime.now().date()
    events = []
    for i in range(7):
        day = today - timedelta(days=i)
        file = Path(data_dir()) / f"{day.isoformat()}.json"
        if file.exists():
            with open(file) as f:
                events.extend(json.load(f))

    plugin = PluginRegistry.get_plugin("weekly_report")
    result = plugin.execute(events=events)
    print(result["report"])


if __name__ == "__main__":
    main()