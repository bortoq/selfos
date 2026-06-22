#!/usr/bin/env python3
"""
Enable Auto Mode — thin wrapper over enable_auto plugin.
"""

import sys

from selfos.plugin_registry import PluginRegistry


def main():
    if len(sys.argv) < 3:
        print("Usage: python enable_auto.py <enable|disable> <action_type>")
        sys.exit(1)

    command = sys.argv[1]
    action = sys.argv[2]
    plugin = PluginRegistry.get_plugin("enable_auto")
    result = plugin.execute(action=action, enable=(command == "enable"))
    print(result["message"])


if __name__ == "__main__":
    main()