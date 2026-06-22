"""
BaseSelfOSPlugin — базовый класс для внутренних плагинов Self OS.

Все плагины, которые реализуют функциональность внутри Self OS 
(а не интеграцию с внешними сервисами), должны наследоваться от этого класса.
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseSelfOSPlugin(ABC):
    """
    Базовый класс для плагинов Self OS.
    """

    name: str = "base"
    description: str = "Base Self OS Plugin"

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {}

    @abstractmethod
    def execute(self, **kwargs: Any) -> Any:
        """
        Основной метод выполнения плагина.
        """
        pass

    def get_name(self) -> str:
        return self.name

    def get_description(self) -> str:
        return self.description