"""
BaseSelfOSPlugin — базовый класс для плагинов Self OS.

Все плагины Self OS должны наследоваться от этого класса.
"""

from abc import ABC, abstractmethod
from typing import Any

from selfos.plugin_manifest import PluginInfo


class BaseSelfOSPlugin(ABC):
    """
    Базовый класс для плагинов Self OS.

    Атрибуты класса (переопределяются в наследниках):
        name:        Уникальное имя плагина (обязательно)
        description: Краткое описание (обязательно)
        version:     Семантическая версия (рекомендуется)
        author:      Имя автора (рекомендуется)
        dependencies: Список зависимостей (опционально)
    """

    name: str = "base"
    description: str = "Base Self OS Plugin"
    version: str = "0.1.0"
    author: str = "Self OS Team"
    dependencies: list[str] = []
    protocol: str = ""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {}

    @abstractmethod
    def execute(self, **kwargs: Any) -> dict[str, Any]:
        """
        Основной метод выполнения плагина.
        Должен быть переопределён в наследниках.
        """
        pass

    def on_register(self, hook_registry: Any) -> None:  # noqa: B027
        """
        Вызывается после регистрации плагина в PluginRegistry.

        Плагин может подписаться на хуки через hook_registry.subscribe().

        По умолчанию ничего не делает — переопределите в наследнике.
        """
        pass

    def get_info(self) -> PluginInfo:
        """Возвращает метаданные плагина."""
        return PluginInfo(
            name=self.name,
            version=self.version,
            author=self.author,
            description=self.description,
            dependencies=self.dependencies,
            protocol=self.protocol,
        )
