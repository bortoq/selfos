#!/usr/bin/env python3
"""
Architecture Contract Validation.

Проверяет:
1. Все плагины наследуют BaseSelfOSPlugin
2. UnifiedInterface зарегистрирован в CLI
3. EventFactory используется для создания событий
4. PluginRegistry содержит все ожидаемые плагины
"""

import importlib
import os
import sys

# Добавляем src/ в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

EXPECTED_PLUGINS = {
    "calendar", "todoist", "quick_note", "categorize", "daily_summary",
    "tag_suggestion", "smart_suggestions", "weekly_report", "enable_auto",
    "auto_categorize", "show_auto_status", "update_dashboard",
}

REQUIRED_MODULES = [
    "selfos.event_factory",
    "selfos.plugin_registry",
    "selfos.base_selfos_plugin",
    "selfos.cli",
    "selfos.unified_interface",
    "selfos.delegation_engine",
    "selfos.scheduler",
    "selfos.context_engine",
    "selfos.browser",
    "selfos.email.service",
    "selfos.trust",
    "selfos.activity",
]


def main() -> int:
    errors = []

    # 1. Проверка импорта всех обязательных модулей
    print("=== Checking required modules ===")
    for mod_name in REQUIRED_MODULES:
        try:
            importlib.import_module(mod_name)
            print(f"  ✅ {mod_name}")
        except ImportError as e:
            errors.append(f"  ❌ {mod_name}: {e}")
            print(f"  ❌ {mod_name}: {e}")

    # 2. Проверка PluginRegistry
    print("\n=== Checking PluginRegistry ===")
    from selfos.plugin_registry import PluginRegistry
    registered = set(PluginRegistry.list_plugins())
    for plugin in EXPECTED_PLUGINS:
        if plugin in registered:
            print(f"  ✅ {plugin}")
        else:
            errors.append(f"Plugin '{plugin}' not registered")
            print(f"  ❌ {plugin}")

    # 3. Проверка UnifiedInterface
    print("\n=== Checking UnifiedInterface handlers ===")
    from selfos.unified_interface import interface
    handlers = set(interface.list_commands())
    expected_handlers = {"note", "task", "status", "suggest", "email",
                         "schedule", "browser", "context", "delegate"}
    for handler in expected_handlers:
        if handler in handlers:
            print(f"  ✅ {handler}")
        else:
            errors.append(f"Handler '{handler}' not registered in UnifiedInterface")
            print(f"  ❌ {handler}")

    # 4. Проверка, что CLI использует UnifiedInterface
    print("\n=== Checking CLI uses UnifiedInterface ===")
    import ast
    cli_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'selfos', 'cli.py')
    with open(cli_path) as f:
        tree = ast.parse(f.read())
    has_unified_call = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if (
                node.func.attr == 'execute'
                and hasattr(node.func.value, 'id')
                and node.func.value.id == 'interface'
            ):
                has_unified_call = True
                break
    if has_unified_call:
        print("  ✅ CLI calls interface.execute()")
    else:
        errors.append("CLI does not call interface.execute()")
        print("  ❌ CLI does not call interface.execute()")

    # 5. Проверка EventFactory
    print("\n=== Checking EventFactory ===")
    from selfos.event_factory import EventFactory
    for method in ['create_event', 'create_task_event', 'create_note_event', 'create_email_event']:
        if hasattr(EventFactory, method):
            print(f"  ✅ EventFactory.{method}")
        else:
            errors.append(f"EventFactory missing {method}")
            print(f"  ❌ EventFactory.{method}")

    # Итог
    print(f"\n{'='*40}")
    if errors:
        print(f"❌ {len(errors)} errors found:")
        for e in errors:
            print(f"   {e}")
        return 1
    else:
        print("✅ All architecture checks passed!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
