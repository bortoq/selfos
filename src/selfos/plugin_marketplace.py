"""
Plugin Marketplace — каталог доступных плагинов (Phase 4, Stage 3).

Позволяет:
- Загружать каталог плагинов из YAML
- Искать плагины по имени, протоколу, тегам
- Сравнивать версии для обновления
- Устанавливать плагины из маркетплейса
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from selfos.config import plugins_dir as get_plugins_dir
from selfos.plugin_manifest import PluginManifest
from selfos.plugin_sdk import scaffold_plugin

# ─── Data models ──────────────────────────────────────────────────────

MARKETPLACE_FILENAME = "plugin-marketplace.yaml"


def _parse_version(version: str) -> tuple[int, ...]:
    """Разбирает семантическую версию в кортеж для сравнения."""
    try:
        parts = version.split(".")
        return tuple(int(p) for p in parts)
    except (ValueError, AttributeError):
        return (0, 0, 0)


def compare_versions(v1: str, v2: str) -> int:
    """
    Сравнивает две семантические версии.

    Returns:
        -1 if v1 < v2, 0 if equal, 1 if v1 > v2
    """
    t1 = _parse_version(v1)
    t2 = _parse_version(v2)
    if t1 < t2:
        return -1
    if t1 > t2:
        return 1
    return 0


@dataclass
class MarketplacePlugin:
    """
    Описание плагина в маркетплейсе.

    Содержит метаданные и инструкции по установке.
    """

    name: str
    description: str
    version: str
    author: str = "Unknown"
    entry_point: str = ""
    protocol: str = ""
    repo_url: str = ""
    dependencies: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    min_selfos_version: str = "0.1.0"

    def to_manifest(self) -> PluginManifest:
        """Создаёт PluginManifest для установки."""
        return PluginManifest(
            name=self.name,
            version=self.version,
            description=self.description,
            entry_point=self.entry_point or f"{self.name.replace('-', '_').lower()}:"
            f"{''.join(p.title() for p in self.name.replace('-', '_').split('_'))}Plugin",
            author=self.author,
            protocol=self.protocol,
            dependencies=list(self.dependencies),
        )


@dataclass
class PluginMarketplace:
    """
    Каталог плагинов — загружается из plugin-marketplace.yaml.

    Атрибуты:
        version: Версия формата каталога
        source:  URL источника для будущего online-режима
        plugins: Список доступных плагинов
    """

    version: str = "1.0"
    source: str = ""
    plugins: list[MarketplacePlugin] = field(default_factory=list)

    def find(self, name: str) -> MarketplacePlugin | None:
        """Ищет плагин по имени."""
        for p in self.plugins:
            if p.name == name:
                return p
        return None

    def search(self, query: str, field: str = "all") -> list[MarketplacePlugin]:
        """
        Поиск плагинов по запросу.

        Args:
            query: Строка поиска
            field: 'name', 'description', 'tags', 'protocol' или 'all'
        """
        q = query.lower()
        results: list[MarketplacePlugin] = []

        for p in self.plugins:
            if field == "name":
                if q in p.name.lower():
                    results.append(p)
            elif field == "protocol":
                if q in p.protocol.lower():
                    results.append(p)
            elif field == "description":
                if q in p.description.lower():
                    results.append(p)
            elif field == "tags":
                if any(q in t.lower() for t in p.tags):
                    results.append(p)
            else:  # all
                if (q in p.name.lower() or q in p.description.lower()
                        or any(q in t.lower() for t in p.tags)):
                    results.append(p)

        return results

    def to_yaml(self) -> str:
        """Сериализует каталог в YAML."""
        plugins_data = []
        for p in self.plugins:
            pd: dict[str, Any] = {
                "name": p.name,
                "version": p.version,
                "description": p.description,
            }
            if p.author != "Unknown":
                pd["author"] = p.author
            if p.entry_point:
                pd["entry_point"] = p.entry_point
            if p.protocol:
                pd["protocol"] = p.protocol
            if p.repo_url:
                pd["repo_url"] = p.repo_url
            if p.dependencies:
                pd["dependencies"] = list(p.dependencies)
            if p.tags:
                pd["tags"] = list(p.tags)
            if p.min_selfos_version != "0.1.0":
                pd["min_selfos_version"] = p.min_selfos_version
            plugins_data.append(pd)

        data = {
            "version": self.version,
            "plugins": plugins_data,
        }
        if self.source:
            data["source"] = self.source

        return str(yaml.dump(data, default_flow_style=False, allow_unicode=True))

    @classmethod
    def from_yaml(cls, content: str) -> PluginMarketplace:
        """Загружает каталог из YAML-строки."""
        try:
            data = yaml.safe_load(content)
        except yaml.YAMLError:
            return cls()
        if not data or not isinstance(data, dict):
            return cls()

        raw_plugins = data.get("plugins", [])
        if not isinstance(raw_plugins, list):
            return cls()

        plugins = []
        for raw in raw_plugins:
            if not isinstance(raw, dict):
                continue
            try:
                plugins.append(MarketplacePlugin(
                    name=str(raw.get("name", "")),
                    description=str(raw.get("description", "")),
                    version=str(raw.get("version", "0.1.0")),
                    author=str(raw.get("author", "Unknown")),
                    entry_point=str(raw.get("entry_point", "")),
                    protocol=str(raw.get("protocol", "")),
                    repo_url=str(raw.get("repo_url", "")),
                    dependencies=list(raw.get("dependencies", [])),
                    tags=list(raw.get("tags", [])),
                    min_selfos_version=str(raw.get("min_selfos_version", "0.1.0")),
                ))
            except (ValueError, TypeError):
                continue

        return cls(
            version=str(data.get("version", "1.0")),
            source=str(data.get("source", "")),
            plugins=plugins,
        )

    @classmethod
    def from_file(cls, path: Path | str) -> PluginMarketplace:
        """Загружает каталог из YAML-файла."""
        path = Path(path)
        if not path.exists():
            return cls()
        return cls.from_yaml(path.read_text(encoding="utf-8"))

    def save(self, path: Path | str) -> None:
        """Сохраняет каталог в YAML-файл."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_yaml(), encoding="utf-8")


# ─── Default marketplace path ─────────────────────────────────────────

def default_marketplace_path() -> Path:
    """Путь к умолчательному файлу маркетплейса в репозитории."""
    return Path(__file__).parent.parent.parent / "docs" / MARKETPLACE_FILENAME


def load_marketplace(path: Path | str | None = None) -> PluginMarketplace:
    """
    Загружает маркетплейс из файла.

    По умолчанию ищет docs/plugin-marketplace.yaml.
    """
    return PluginMarketplace.from_file(path or default_marketplace_path())


# ─── Installation helpers ─────────────────────────────────────────────

def install_plugin_from_marketplace(
    name: str,
    marketplace: PluginMarketplace | None = None,
    *,
    dest_dir: str | None = None,
) -> str:
    """
    Устанавливает плагин из маркетплейса.

    1. Ищет плагин по имени в маркетплейсе
    2. Создаёт директорию с плагином (scaffold или копирование)
    3. Регистрирует в глобальном реестре

    Args:
        name: Имя плагина из маркетплейса
        marketplace: Каталог (загружается по умолчанию)
        dest_dir: Целевая директория (по умолчанию ~/.selfos/plugins/<name>)

    Returns:
        Путь к директории с установленным плагином

    Raises:
        ValueError: если плагин не найден или уже установлен
    """
    from selfos.plugin_registry import PluginRegistry

    if marketplace is None:
        marketplace = load_marketplace()

    plugin_info = marketplace.find(name)
    if plugin_info is None:
        raise ValueError(f"Plugin '{name}' not found in marketplace")

    # Проверяем, не установлен ли уже
    if name in PluginRegistry.list_plugins():
        raise ValueError(f"Plugin '{name}' is already installed. Use 'update' to upgrade.")

    # Определяем целевую директорию
    if dest_dir is None:
        dest_dir = str(get_plugins_dir() / name.replace("-", "_"))

    # Создаём файлы плагина
    scaffold_plugin(
        name=name,
        dest_dir=dest_dir,
        author=plugin_info.author,
        description=plugin_info.description,
        protocol=plugin_info.protocol,
    )

    # Регистрируем
    manifest_path = Path(dest_dir) / "plugin.yaml"
    manifest = PluginManifest.from_file(manifest_path)
    # Обновляем версию из маркетплейса
    manifest.version = plugin_info.version
    # Перезаписываем plugin.yaml с актуальной версией
    manifest_path.write_text(manifest.to_yaml(), encoding="utf-8")

    # Добавляем в sys.path
    import sys
    plugins_root = str(get_plugins_dir())
    if plugins_root not in sys.path:
        sys.path.insert(0, plugins_root)

    PluginRegistry.install_global(manifest)
    return dest_dir


def remove_plugin(name: str, *, cleanup_files: bool = True) -> bool:
    """
    Удаляет плагин из реестра и (опционально) с диска.

    Args:
        name: Имя плагина
        cleanup_files: Удалять ли файлы плагина

    Returns:
        True если плагин был удалён
    """
    from selfos.plugin_registry import PluginRegistry

    registry = PluginRegistry._get_global()

    # Проверяем, установлен ли
    if name not in registry.list_registered():
        return False

    manifest = registry.get_manifest(name)

    # Удаляем из реестра
    registry._plugins.pop(name, None)
    registry._instances.pop(name, None)
    registry._manifests.pop(name, None)

    # Очищаем глобальный кэш, если нужно
    if PluginRegistry._global_registry is registry:
        pass  # Сохраняем ссылку

    if cleanup_files and manifest:
        # Ищем директорию плагина
        # Сначала ищем в ~/.selfos/plugins/<name>/
        plugin_dir = get_plugins_dir() / name.replace("-", "_")
        if plugin_dir.exists():
            import shutil
            shutil.rmtree(plugin_dir)
            return True

    return True


def check_for_updates(
    marketplace: PluginMarketplace | None = None,
) -> list[dict[str, Any]]:
    """
    Проверяет обновления для установленных плагинов.

    Returns:
        Список словарей с name, current_version, available_version
    """
    from selfos.plugin_registry import PluginRegistry

    if marketplace is None:
        marketplace = load_marketplace()

    updates: list[dict[str, Any]] = []
    for p in PluginRegistry.list_plugins_with_metadata():
        name = p.get("name", "")
        current_ver = p.get("version", "0.0.0")
        mp_plugin = marketplace.find(name)
        if mp_plugin and compare_versions(current_ver, mp_plugin.version) < 0:
            updates.append({
                "name": name,
                "current_version": current_ver,
                "available_version": mp_plugin.version,
                "description": mp_plugin.description,
            })

    return updates


def update_plugin(
    name: str,
    marketplace: PluginMarketplace | None = None,
) -> str:
    """
    Обновляет плагин до последней версии из маркетплейса.

    Args:
        name: Имя плагина
        marketplace: Каталог (загружается по умолчанию)

    Returns:
        Новая версия

    Raises:
        ValueError: если плагин не найден в маркетплейсе или не установлен
    """
    from selfos.plugin_registry import PluginRegistry

    if marketplace is None:
        marketplace = load_marketplace()

    plugin_info = marketplace.find(name)
    if plugin_info is None:
        raise ValueError(f"Plugin '{name}' not found in marketplace")

    # Проверяем, что плагин установлен
    manifest = PluginRegistry.get_plugin_manifest(name)
    if manifest is None:
        raise ValueError(f"Plugin '{name}' is not installed. Use 'install' first.")

    current_ver = manifest.version
    if compare_versions(current_ver, plugin_info.version) >= 0:
        return current_ver  # Уже актуальная версия

    # Обновляем manifest
    manifest.version = plugin_info.version
    manifest.description = plugin_info.description

    # Сохраняем обновлённый manifest в файл (если есть)
    plugin_dir = get_plugins_dir() / name.replace("-", "_")
    manifest_path = plugin_dir / "plugin.yaml"
    if manifest_path.exists():
        manifest_path.write_text(manifest.to_yaml(), encoding="utf-8")

    # Перерегистрируем
    registry = PluginRegistry._get_global()
    registry._manifests[name] = manifest

    return plugin_info.version
