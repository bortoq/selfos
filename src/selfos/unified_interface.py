"""
UnifiedInterface — единый интерфейс Self OS (Phase 3, Этап 5).

Объединяет:
- CLI
- Web (заготовка)
- Voice / Chat (заготовка)

Предоставляет единую точку входа для пользователя.
"""

from typing import Dict, Any, Callable
from src.selfos.plugin_registry import PluginRegistry


class UnifiedInterface:
    """
    Единый интерфейс Self OS.
    """

    def __init__(self):
        self.handlers: Dict[str, Callable] = {}

    def register_handler(self, command: str, handler: Callable):
        """Регистрирует обработчик команды"""
        self.handlers[command] = handler

    def execute(self, command: str, **kwargs) -> Dict[str, Any]:
        """Выполняет команду через единый интерфейс"""
        if command not in self.handlers:
            return {
                "success": False,
                "error": f"Unknown command: {command}"
            }

        try:
            result = self.handlers[command](**kwargs)
            return {
                "success": True,
                "command": command,
                "result": result
            }
        except Exception as e:
            return {
                "success": False,
                "command": command,
                "error": str(e)
            }

    def list_commands(self) -> list:
        return list(self.handlers.keys())


# Глобальный экземпляр единого интерфейса
interface = UnifiedInterface()


def register_default_handlers():
    """Регистрирует базовые обработчики"""
    from src.selfos.cli import (
        cmd_note, cmd_task, cmd_status, cmd_suggest,
        cmd_email, cmd_schedule, cmd_browser, cmd_context, cmd_delegate
    )

    interface.register_handler("note", cmd_note)
    interface.register_handler("task", cmd_task)
    interface.register_handler("status", cmd_status)
    interface.register_handler("suggest", cmd_suggest)
    interface.register_handler("email", cmd_email)
    interface.register_handler("schedule", cmd_schedule)
    interface.register_handler("browser", cmd_browser)
    interface.register_handler("context", cmd_context)
    interface.register_handler("delegate", cmd_delegate)


# Автоматическая регистрация при импорте
register_default_handlers()