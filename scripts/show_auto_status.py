#!/usr/bin/env python3
"""
Show auto status — CLI entry point.

Uses show_auto_status plugin via PluginRegistry.
"""

from selfos.plugin_registry import PluginRegistry


def main():
    plugin = PluginRegistry.get_plugin("show_auto_status")
    result = plugin.execute()
    print(result)


if __name__ == "__main__":
    main()
