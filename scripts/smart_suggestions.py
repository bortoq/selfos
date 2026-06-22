#!/usr/bin/env python3
"""
Smart Suggestions — thin wrapper over smart_suggestions plugin.
"""

from selfos.plugin_registry import PluginRegistry


def main():
    plugin = PluginRegistry.get_plugin("smart_suggestions")
    result = plugin.execute()
    print("=== Smart Suggestions ===\n")
    for s in result["suggestions"]:
        print(f"- {s}")


if __name__ == "__main__":
    main()