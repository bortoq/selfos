"""
Plugin Manifest — метаданные плагина.

Позволяет упаковывать и распространять плагины в стандартизированном формате.
"""

import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class PluginInfo:
    """
    Информация о плагине: метаданные + состояние.

    Доступна через plugin.get_info() после инициализации.
    """

    name: str = ""
    version: str = "0.1.0"
    author: str = "Unknown"
    description: str = ""
    dependencies: list[str] = field(default_factory=list)
    protocol: str = ""
    manifest_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "author": self.author,
            "description": self.description,
            "dependencies": self.dependencies,
            "protocol": self.protocol,
        }

PLUGIN_MANIFEST_FILENAME = "plugin.yaml"


@dataclass
class PluginManifest:
    """
    Манифест плагина Self OS.

    Описывает метаданные, точку входа и настройки плагина.

    Пример:
        >>> manifest = PluginManifest(
        ...     name="my-plugin",
        ...     version="1.0.0",
        ...     description="A custom plugin",
        ...     author="User",
        ...     entry_point="my_plugin:MyPlugin",
        ... )
    """

    name: str
    version: str
    description: str
    entry_point: str  # "module.path:ClassName"
    author: str = "Unknown"
    protocol: str = ""
    dependencies: list[str] = field(default_factory=list)
    config: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Автоматическая валидация после инициализации."""
        errors = self.validate()
        if errors:
            raise ValueError(f"Invalid plugin manifest: {'; '.join(errors)}")

    def validate(self) -> list[str]:
        """Проверяет корректность манифеста. Возвращает список ошибок."""
        errors: list[str] = []

        if not self.name or not re.match(r"^[a-zA-Z0-9_-]+$", self.name):
            errors.append(
                f"Invalid name '{self.name}': must match ^[a-zA-Z0-9_-]+$"
            )
        if not self.version:
            errors.append("Version is required")
        if not self.description:
            errors.append("Description is required")
        if not self.entry_point or ":" not in self.entry_point:
            errors.append(
                f"Invalid entry_point '{self.entry_point}': "
                "must be 'module.path:ClassName'"
            )
        if self.dependencies and not isinstance(self.dependencies, list):
            errors.append("Dependencies must be a list of strings")

        return errors

    def to_yaml(self) -> str:
        """Сериализует манифест в YAML."""
        return str(yaml.dump(asdict(self), default_flow_style=False, allow_unicode=True))

    @classmethod
    def from_yaml(cls, content: str) -> "PluginManifest":
        """Загружает манифест из YAML-строки."""
        data = yaml.safe_load(content)
        if not isinstance(data, dict):
            raise ValueError("Invalid YAML: expected a mapping")
        return cls(**data)

    @classmethod
    def from_file(cls, path: Path | str) -> "PluginManifest":
        """Загружает манифест из файла."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Manifest not found: {path}")
        return cls.from_yaml(path.read_text(encoding="utf-8"))

    @classmethod
    def find_in_dir(cls, directory: Path | str) -> Path | None:
        """Ищет `plugin.yaml` в указанной директории."""
        directory = Path(directory)
        candidate = directory / PLUGIN_MANIFEST_FILENAME
        return candidate if candidate.exists() else None
