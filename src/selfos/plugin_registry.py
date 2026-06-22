"""
PluginRegistry — реестр плагинов Self OS.

Поддерживает:
- Глобальный экземпляр для production (PluginRegistry.get_plugin())
- Изолированные экземпляры для тестов (PluginRegistry() + .register()/.get())
- Установку плагинов из манифеста (.install() / .install_global())
- Обнаружение плагинов в директориях (.discover() / .discover_global())
"""

from pathlib import Path
from typing import Any

from selfos.config import plugins_dir as get_plugins_dir
from selfos.plugin_manifest import PluginManifest


class PluginRegistry:
    """Реестр плагинов Self OS (instance-based, с глобальным singleton'ом)."""

    _global_registry: 'PluginRegistry | None' = None

    def __init__(self) -> None:
        self._plugins: dict[str, type] = {}
        self._instances: dict[str, Any] = {}
        self._manifests: dict[str, PluginManifest] = {}

    # --- Instance API ---

    def register(self, name: str, plugin_class: type) -> None:
        """Зарегистрировать класс плагина."""
        if not name:
            raise ValueError("Plugin name cannot be empty")
        if name in self._plugins:
            raise ValueError(f"Plugin '{name}' is already registered")
        self._plugins[name] = plugin_class
        # Вызываем on_register, если метод определён
        if hasattr(plugin_class, 'on_register'):
            from selfos.hooks import get_hook_registry
            try:
                # Создаём временный экземпляр для вызова on_register
                instance = plugin_class(self._get_default_config(name))
                instance.on_register(get_hook_registry())
            except Exception:
                pass

    def get(self, name: str, config: dict[str, Any] | None = None) -> Any:
        """Получить экземпляр плагина (с кэшированием)."""
        if name not in self._plugins:
            raise ValueError(f"Plugin '{name}' is not registered")
        if name not in self._instances:
            plugin_class = self._plugins[name]
            cfg = config if config is not None else self._get_default_config(name)
            self._instances[name] = plugin_class(cfg)
        return self._instances[name]

    def list_registered(self) -> list[str]:
        """Список зарегистрированных имён плагинов."""
        return list(self._plugins.keys())

    def clear(self) -> None:
        """Очистить реестр и экземпляры."""
        self._plugins.clear()
        self._instances.clear()
        self._manifests.clear()

    def _get_default_config(self, name: str) -> dict[str, Any]:
        """Возвращает конфигурацию по умолчанию из манифеста."""
        manifest = self._manifests.get(name)
        return manifest.config.copy() if manifest and manifest.config else {}

    # --- Установка и обнаружение ---

    def install(self, manifest: PluginManifest) -> None:
        """Устанавливает плагин из манифеста (динамический импорт entry_point)."""
        if manifest.name in self._plugins:
            raise ValueError(f"Plugin '{manifest.name}' is already installed")

        # Динамический импорт: "my_plugin:MyPlugin"
        module_path, class_name = manifest.entry_point.split(":", 1)
        import importlib
        import sys as _sys
        # Clear stale caches: sys.modules + path importer cache
        for _k in list(_sys.modules):
            if _k == module_path or _k == module_path.split(".")[0]:
                _sys.modules.pop(_k, None)
        importlib.invalidate_caches()
        module = importlib.import_module(module_path)
        plugin_class = getattr(module, class_name)
        if not isinstance(plugin_class, type):
            raise TypeError(f"Entry point '{manifest.entry_point}' is not a class")

        self._plugins[manifest.name] = plugin_class
        self._manifests[manifest.name] = manifest

    def discover(self, directory: Path | str | None = None) -> list[str]:
        """
        Сканирует директорию в поисках plugin.yaml и устанавливает найденные плагины.

        Args:
            directory: Путь к директории с плагинами.
                       По умолчанию ~/.selfos/plugins/.

        Returns:
            Список имён установленных плагинов.
        """
        search_dir = Path(directory) if directory else get_plugins_dir()
        if not search_dir.exists():
            return []

        installed: list[str] = []
        for item in search_dir.iterdir():
            if item.is_dir():
                manifest_path = PluginManifest.find_in_dir(item)
                if manifest_path:
                    manifest = PluginManifest.from_file(manifest_path)
                    if manifest.name not in self._plugins:
                        try:
                            self.install(manifest)
                            installed.append(manifest.name)
                        except Exception:
                            pass  # Логирование в будущем
        return installed

    def get_manifest(self, name: str) -> PluginManifest | None:
        """Возвращает манифест установленного плагина."""
        return self._manifests.get(name)

    def list_with_metadata(self) -> list[dict[str, Any]]:
        """Возвращает список плагинов с метаданными."""
        result: list[dict[str, Any]] = []
        for name in self._plugins:
            manifest = self._manifests.get(name)
            if manifest:
                result.append({
                    "name": manifest.name,
                    "version": manifest.version,
                    "author": manifest.author,
                    "description": manifest.description,
                    "protocol": manifest.protocol,
                })
            else:
                # Built-in plugin без манифеста
                try:
                    instance = self.get(name)
                    if hasattr(instance, 'get_info'):
                        info = instance.get_info()
                        result.append(info.to_dict())
                    else:
                        result.append({"name": name, "description": "", "version": "?"})
                except Exception:
                    result.append({"name": name, "description": "", "version": "?"})
        return result

    # --- Глобальный singleton ---

    @classmethod
    def _get_global(cls) -> 'PluginRegistry':
        if cls._global_registry is None:
            reg = PluginRegistry()
            _auto_register(reg)
            reg.discover()
            cls._global_registry = reg
        return cls._global_registry

    # --- Classmethod API ---

    @classmethod
    def get_plugin(cls, name: str, config: dict[str, Any] | None = None) -> Any:
        return cls._get_global().get(name, config)

    @classmethod
    def list_plugins(cls) -> list[str]:
        return cls._get_global().list_registered()

    @classmethod
    def clear_global(cls) -> None:
        cls._get_global().clear()

    @classmethod
    def install_global(cls, manifest: PluginManifest) -> None:
        """Устанавливает плагин в глобальный реестр."""
        cls._get_global().install(manifest)

    @classmethod
    def discover_global(cls, directory: Path | str | None = None) -> list[str]:
        """Сканирует и устанавливает плагины из директории."""
        return cls._get_global().discover(directory)

    @classmethod
    def list_plugins_with_metadata(cls) -> list[dict[str, Any]]:
        """Список плагинов с метаданными."""
        return cls._get_global().list_with_metadata()

    @classmethod
    def get_plugin_manifest(cls, name: str) -> PluginManifest | None:
        """Возвращает манифест плагина."""
        return cls._get_global().get_manifest(name)


# === Регистрация встроенных плагинов ===

from plugins.auto_categorize_plugin import AutoCategorizePlugin
from plugins.calendar_plugin import CalendarPlugin
from plugins.categorize_plugin import CategorizePlugin
from plugins.daily_summary_plugin import DailySummaryPlugin
from plugins.enable_auto_plugin import EnableAutoPlugin
from plugins.quick_note_plugin import QuickNotePlugin
from plugins.show_auto_status_plugin import ShowAutoStatusPlugin
from plugins.smart_suggestions_plugin import SmartSuggestionsPlugin
from plugins.tag_suggestion_plugin import TagSuggestionPlugin
from plugins.todoist_plugin import TodoistPlugin
from plugins.update_dashboard_plugin import UpdateDashboardPlugin
from plugins.weekly_report_plugin import WeeklyReportPlugin


def _auto_register(registry: PluginRegistry) -> None:
    """Регистрирует все встроенные плагины."""
    registry.register("calendar", CalendarPlugin)
    registry.register("todoist", TodoistPlugin)
    registry.register("quick_note", QuickNotePlugin)
    registry.register("categorize", CategorizePlugin)
    registry.register("daily_summary", DailySummaryPlugin)
    registry.register("tag_suggestion", TagSuggestionPlugin)
    registry.register("smart_suggestions", SmartSuggestionsPlugin)
    registry.register("weekly_report", WeeklyReportPlugin)
    registry.register("enable_auto", EnableAutoPlugin)
    registry.register("auto_categorize", AutoCategorizePlugin)
    registry.register("show_auto_status", ShowAutoStatusPlugin)
    registry.register("update_dashboard", UpdateDashboardPlugin)
