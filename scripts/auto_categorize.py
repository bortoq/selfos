#!/usr/bin/env python3
"""
Auto-categorize — CLI entry point.

Uses categorize plugin via PluginRegistry.
"""

from selfos.plugin_registry import PluginRegistry


def main():
    plugin = PluginRegistry.get_plugin("auto_categorize")
    result = plugin.execute(title=" ".join(sys.argv[1:]) if len(sys.argv) > 1 else "")
    print(result)


if __name__ == "__main__":
    import sys
    main()
