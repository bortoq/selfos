"""
End-to-end тест Phase 4.

Проверяет сквозной сценарий:
  Создать плагин → Зарегистрировать → Установить из маркетплейса →
  Обновить → Удалить → Подписаться на хуки
"""

import sys
from pathlib import Path

import pytest

from selfos.base_selfos_plugin import BaseSelfOSPlugin
from selfos.hooks import (
    HOOK_NOTE_CREATE,
    get_hook_registry,
    reset_hook_registry,
)
from selfos.plugin_manifest import PluginManifest
from selfos.plugin_marketplace import (
    MarketplacePlugin,
    PluginMarketplace,
    check_for_updates,
    compare_versions,
    install_plugin_from_marketplace,
    remove_plugin,
    update_plugin,
)
from selfos.plugin_registry import PluginRegistry
from selfos.plugin_sdk import scaffold_plugin, validate_plugin


class TestPhase4E2E:
    """Сквозной тест всех возможностей Phase 4."""

    def test_full_plugin_lifecycle(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """
        1. Создать плагин через scaffold
        2. Проверить manifest
        3. Валидировать плагин
        4. Зарегистрировать
        5. Установить из маркетплейса
        6. Обновить
        7. Удалить
        """
        reset_hook_registry()
        import selfos.config as _config
        plugins_root = tmp_path / "plugins"
        plugins_root.mkdir(parents=True, exist_ok=True)
        monkeypatch.setattr(_config, "plugins_dir", lambda: plugins_root)
        monkeypatch.syspath_prepend(str(plugins_root))
        # Изоляция: очищаем кеш импорта от предыдущих тестов
        for mod in list(sys.modules):
            if mod in ("mp_installed", "mp_installed.mp_installed",
                       "e2e_test_plugin", "e2e_test_plugin.e2e_test_plugin",
                       "first_plugin", "first_plugin.first_plugin",
                       "test_plugin", "test_plugin.test_plugin"):
                sys.modules.pop(mod, None)

        # 1. Scaffold
        name = "e2e-test-plugin"
        dest_dir = str(plugins_root / name.replace("-", "_"))
        files = scaffold_plugin(
            name=name,
            dest_dir=dest_dir,
            author="Tester",
            description="E2E test plugin",
            protocol="NotingPlugin",
        )
        assert len(files) >= 3  # plugin.yaml, __init__.py, module

        # 2. Проверка manifest
        manifest_path = Path(dest_dir) / "plugin.yaml"
        assert manifest_path.exists()
        manifest = PluginManifest.from_file(manifest_path)
        assert manifest.name == name
        assert manifest.version == "0.1.0"
        assert manifest.author == "Tester"

        # 3. Валидация
        import importlib
        safe_name = name.replace("-", "_")
        # The class is in safe_name.py inside the safe_name package
        module = importlib.import_module(f"{safe_name}.{safe_name}")
        plugin_class = module.E2ETestPluginPlugin
        errors = validate_plugin(plugin_class)
        assert errors == [], f"Validation errors: {errors}"

        # 4. Регистрация (через установку)
        registry = PluginRegistry()
        registry.install(manifest)
        assert name in registry.list_registered()

        # 5. Установка из маркетплейса
        mp = PluginMarketplace(plugins=[
            MarketplacePlugin(name="mp-installed", description="MP test",
                              version="1.0.0", author="Marketplace"),
        ])
        mp_dest = str(plugins_root / "mp_installed")
        install_plugin_from_marketplace("mp-installed", marketplace=mp, dest_dir=mp_dest)
        assert "mp-installed" in PluginRegistry.list_plugins()

        # 6. Обновление
        mp2 = PluginMarketplace(plugins=[
            MarketplacePlugin(name="mp-installed", description="MP test v2",
                              version="2.0.0", author="Marketplace"),
        ])
        updates = check_for_updates(marketplace=mp2)
        matching = [u for u in updates if u["name"] == "mp-installed"]
        assert len(matching) == 1
        assert matching[0]["current_version"] == "1.0.0"
        assert matching[0]["available_version"] == "2.0.0"

        new_ver = update_plugin("mp-installed", marketplace=mp2)
        assert new_ver == "2.0.0"
        updated_manifest = PluginRegistry.get_plugin_manifest("mp-installed")
        assert updated_manifest is not None
        assert updated_manifest.version == "2.0.0"

        # 7. Удаление + очистка sys.modules для изоляции
        removed = remove_plugin("mp-installed", cleanup_files=True)
        assert removed is True
        assert "mp-installed" not in PluginRegistry.list_plugins()
        for mod_name in ["mp_installed", "mp_installed.mp_installed",
                         "e2e_test_plugin", "e2e_test_plugin.e2e_test_plugin"]:
            sys.modules.pop(mod_name, None)

    def test_hooks_integration(self, tmp_path: Path) -> None:
        """
        Проверяет, что плагин может подписаться на хуки
        через on_register() и получать события.
        """
        reset_hook_registry()

        # Создаём плагин, который подписывается на note:create
        call_count = []

        class HookTestPlugin(BaseSelfOSPlugin):
            name = "hook-test-e2e"
            description = "Test hooks"
            version = "1.0.0"

            def execute(self, **kwargs):
                return {"result": "ok"}

            def on_register(self, hook_registry):
                call_count.append("on_register_called")
                hook_registry.subscribe(
                    HOOK_NOTE_CREATE, self.name,
                    self.before_hook, hook_type="before",
                )

            def before_hook(self, **context):
                context["text"] = f"[HOOKED] {context.get('text', '')}"
                return context

        # Прямая проверка: вызываем on_register вручную с экземпляром

        # Прямая проверка: вызываем on_register вручную с экземпляром
        instance = HookTestPlugin({})
        hook_reg = get_hook_registry()
        instance.on_register(hook_reg)

        assert len(call_count) == 1

        # Триггерим хуки — before_hook должен сработать
        ctx = hook_reg.trigger_before(HOOK_NOTE_CREATE, text="hello")
        assert ctx["text"] == "[HOOKED] hello"

    def test_delegation_rules_e2e(self, tmp_path: Path) -> None:
        """
        Проверяет создание, применение и удаление правил делегирования.
        """
        from selfos.delegation_engine import DelegationEngine
        from selfos.delegation_rules import DelegationRule

        engine = DelegationEngine(rules_file=str(tmp_path / "e2e_rules.yaml"))

        # Добавляем правило
        engine.add_rule(DelegationRule(
            name="e2e-allow-notes",
            action_type="quick_note",
            effect="allow",
            condition_type="always",
            priority=80,
        ))

        # Проверяем, что правило работает
        assert engine.should_auto_execute("quick_note") is True

        # Добавляем запрещающее правило с высшим приоритетом
        engine.add_rule(DelegationRule(
            name="e2e-deny-notes",
            action_type="quick_note",
            effect="deny",
            condition_type="always",
            priority=90,
        ))
        assert engine.should_auto_execute("quick_note") is False

        # Удаляем запрещающее — должно снова разрешить
        engine.remove_rule("e2e-deny-notes")
        assert engine.should_auto_execute("quick_note") is True

    def test_version_comparison(self) -> None:
        """Проверка semver comparison."""
        assert compare_versions("1.0.0", "1.0.0") == 0
        assert compare_versions("0.9.0", "1.0.0") == -1
        assert compare_versions("2.0.0", "1.9.9") == 1
        assert compare_versions("1.0.0-alpha", "1.0.0") in (-1, 0, 1)

    def test_marketplace_search_e2e(self) -> None:
        """Поиск в маркетплейсе."""
        mp = PluginMarketplace(plugins=[
            MarketplacePlugin(name="note-helper", description="Helps with notes",
                              version="1.0.0", tags=["note", "utility"]),
            MarketplacePlugin(name="email-sorter", description="Sorts emails",
                              version="1.0.0", tags=["email"]),
        ])

        # Поиск по имени
        assert len(mp.search("note", field="name")) == 1
        # Поиск по тегам
        assert len(mp.search("email", field="tags")) == 1
        # Поиск по всем полям
        assert len(mp.search("note", field="all")) >= 1
        # Нет совпадений
        assert len(mp.search("nonexistent")) == 0
