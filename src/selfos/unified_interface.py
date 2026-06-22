"""
UnifiedInterface — единый интерфейс Self OS (Phase 3, Этап 5).

Объединяет:
- CLI (основной пользователь)
- Web (заготовка)
- Voice / Chat (заготовка)

Предоставляет единую точку входа для пользователя.
"""

import argparse
from collections.abc import Callable
from typing import Any


class UnifiedInterface:
    """
    Единый интерфейс Self OS.
    """

    def __init__(self) -> None:
        self.handlers: dict[str, Callable[..., Any]] = {}

    def register_handler(self, action: str, handler: Callable[..., Any]) -> None:
        """Регистрирует обработчик команды"""
        self.handlers[action] = handler

    def execute(self, command: str, **kwargs: Any) -> dict[str, Any]:
        """Выполняет команду через единый интерфейс.

        Обработчикам (cmd_*) передаётся argparse.Namespace,
        собранный из **kwargs — это обеспечивает совместимость
        как с CLI (через парсер), так и с будущими Web/Voice вызовами.
        """
        if command not in self.handlers:
            return {
                "success": False,
                "error": f"Unknown command: {command}"
            }

        try:
            handler = self.handlers[command]
            args = argparse.Namespace(**kwargs)
            result = handler(args)
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

    def list_commands(self) -> list[str]:
        return list(self.handlers.keys())


# Глобальный экземпляр единого интерфейса
interface = UnifiedInterface()


def register_default_handlers() -> None:
    """Регистрирует базовые обработчики"""
    from selfos.cli import (
        cmd_browser,
        cmd_calendar,
        cmd_config,
        cmd_context,
        cmd_delegate,
        cmd_email,
        cmd_github,
        cmd_gmail,
        cmd_note,
        cmd_plugin,
        cmd_profile,
        cmd_schedule,
        cmd_status,
        cmd_suggest,
        cmd_task,
        cmd_todoist,
    )

    interface.register_handler("note", cmd_note)
    interface.register_handler("task", cmd_task)
    interface.register_handler("status", cmd_status)
    interface.register_handler("suggest", cmd_suggest)
    interface.register_handler("email", cmd_email)
    interface.register_handler("schedule", cmd_schedule)
    interface.register_handler("browser", cmd_browser)
    interface.register_handler("context", cmd_context)
    interface.register_handler("config", cmd_config)
    interface.register_handler("profile", cmd_profile)
    interface.register_handler("gmail", cmd_gmail)
    interface.register_handler("calendar", cmd_calendar)
    interface.register_handler("todoist", cmd_todoist)
    interface.register_handler("github", cmd_github)
    interface.register_handler("delegate", cmd_delegate)
    interface.register_handler("plugin", cmd_plugin)


# Автоматическая регистрация при импорте
register_default_handlers()
