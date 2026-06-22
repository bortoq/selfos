"""
Hooks — система точек расширения ядра Self OS (Phase 4, Stage 4).

Плагины могут подписываться на события (before/after/instead) и
влиять на выполнение команд ядра.

Пример использования:
    class MyPlugin(BaseSelfOSPlugin):
        def on_register(self, hook_registry):
            hook_registry.subscribe("note:create", self.name, self.before_note, hook_type="before")
            hook_registry.subscribe("note:create", self.name, self.after_note, hook_type="after")

        def before_note(self, **context):
            context["text"] = f"[PREFIX] {context.get('text', '')}"
            return context

        def after_note(self, result, **context):
            result["hook_processed"] = True
            return result
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

# ─── Hook types ───────────────────────────────────────────────────────

HOOK_BEFORE = "before"  # Вызывается ДО операции, может изменить контекст
HOOK_AFTER = "after"    # Вызывается ПОСЛЕ операции, может изменить результат
HOOK_INSTEAD = "instead"  # Заменяет операцию (если вернул не None)

VALID_HOOK_TYPES = frozenset({HOOK_BEFORE, HOOK_AFTER, HOOK_INSTEAD})


# ─── Predefined hook points ───────────────────────────────────────────

HOOK_NOTE_CREATE = "note:create"
HOOK_TASK_CREATE = "task:create"
HOOK_EMAIL_SEND = "email:send"
HOOK_SUGGEST = "suggest:get"
HOOK_SCHEDULE_TASK = "schedule:task"
HOOK_SCHEDULE_EVENT = "schedule:event"
HOOK_BROWSER_OPEN = "browser:open"
HOOK_BROWSER_SEARCH = "browser:search"
HOOK_CONTEXT_SUMMARY = "context:summary"
HOOK_DELEGATE_CHECK = "delegate:check"
HOOK_PLUGIN_INSTALL = "plugin:install"
HOOK_PLUGIN_REMOVE = "plugin:remove"

ALL_HOOK_POINTS: frozenset[str] = frozenset({
    HOOK_NOTE_CREATE,
    HOOK_TASK_CREATE,
    HOOK_EMAIL_SEND,
    HOOK_SUGGEST,
    HOOK_SCHEDULE_TASK,
    HOOK_SCHEDULE_EVENT,
    HOOK_BROWSER_OPEN,
    HOOK_BROWSER_SEARCH,
    HOOK_CONTEXT_SUMMARY,
    HOOK_DELEGATE_CHECK,
    HOOK_PLUGIN_INSTALL,
    HOOK_PLUGIN_REMOVE,
})


# ─── Hook registry ────────────────────────────────────────────────────

class HookRegistry:
    """
    Реестр хуков — центральная точка расширения Self OS.

    Плагины подписываются через subscribe(), ядро вызывает
    trigger_before() / trigger_after() / trigger_instead().
    """

    def __init__(self) -> None:
        # _hooks[hook_point][hook_type] = [(plugin_name, handler), ...]
        self._hooks: dict[str, dict[str, list[tuple[str, Callable[..., Any]]]]] = {}

    def subscribe(
        self,
        hook_point: str,
        plugin_name: str,
        handler: Callable[..., Any],
        *,
        hook_type: str = HOOK_AFTER,
    ) -> None:
        """
        Подписать плагин на хук.

        Args:
            hook_point: Точка расширения (например "note:create")
            plugin_name: Имя плагина
            handler: Функция-обработчик
            hook_type: "before", "after" или "instead"
        """
        if hook_type not in VALID_HOOK_TYPES:
            raise ValueError(f"Invalid hook_type '{hook_type}'. Use: before, after, instead")

        if hook_point not in ALL_HOOK_POINTS:
            # Warn but allow (future hook points)
            pass

        if hook_point not in self._hooks:
            self._hooks[hook_point] = {}
        if hook_type not in self._hooks[hook_point]:
            self._hooks[hook_point][hook_type] = []

        # Удаляем старую подписку того же плагина (для замены при перезагрузке)
        self._hooks[hook_point][hook_type] = [
            (n, h) for n, h in self._hooks[hook_point][hook_type]
            if n != plugin_name
        ]
        self._hooks[hook_point][hook_type].append((plugin_name, handler))

    def unsubscribe(self, hook_point: str, plugin_name: str) -> bool:
        """Отписать плагин от точки."""
        removed = False
        if hook_point in self._hooks:
            for hook_type in list(self._hooks[hook_point].keys()):
                before = len(self._hooks[hook_point][hook_type])
                self._hooks[hook_point][hook_type] = [
                    (n, h) for n, h in self._hooks[hook_point][hook_type]
                    if n != plugin_name
                ]
                if len(self._hooks[hook_point][hook_type]) < before:
                    removed = True
        return removed

    def unsubscribe_all(self, plugin_name: str) -> int:
        """Отписать плагин от всех точек. Возвращает количество удалённых подписок."""
        count = 0
        for hook_point in list(self._hooks.keys()):
            for hook_type in list(self._hooks[hook_point].keys()):
                before = len(self._hooks[hook_point][hook_type])
                self._hooks[hook_point][hook_type] = [
                    (n, h) for n, h in self._hooks[hook_point][hook_type]
                    if n != plugin_name
                ]
                count += before - len(self._hooks[hook_point][hook_type])
        return count

    def list_subscriptions(self, hook_point: str | None = None) -> dict[str, list[dict[str, str]]]:
        """
        Возвращает список подписок.

        Returns:
            {hook_point: [{"plugin": name, "type": hook_type}, ...], ...}
        """
        result: dict[str, list[dict[str, str]]] = {}
        for hp, types in self._hooks.items():
            if hook_point is not None and hp != hook_point:
                continue
            entries: list[dict[str, str]] = []
            for ht, handlers in types.items():
                for name, _ in handlers:
                    entries.append({"plugin": name, "type": ht})
            if entries:
                result[hp] = entries
        return result

    def has_subscribers(self, hook_point: str) -> bool:
        """Проверяет, есть ли подписчики на точку."""
        return hook_point in self._hooks and any(
            handlers for handlers in self._hooks[hook_point].values()
        )

    def trigger_before(self, hook_point: str, **context: Any) -> dict[str, Any]:
        """
        Вызывает before-хуки. Каждый обработчик может изменить контекст.

        Returns:
            Обновлённый контекст (после всех before-обработчиков).
        """
        if hook_point not in self._hooks:
            return context
        before_handlers = self._hooks[hook_point].get(HOOK_BEFORE, [])
        for _name, handler in before_handlers:
            try:
                result = handler(**context)
                if isinstance(result, dict):
                    context.update(result)
            except Exception:
                pass  # Исключения в хуках не ломают основную логику
        return context

    def trigger_after(self, hook_point: str, result: Any = None, **context: Any) -> Any:
        """
        Вызывает after-хуки. Каждый обработчик может изменить результат.

        Returns:
            Финальный результат (после всех after-обработчиков).
        """
        if hook_point not in self._hooks:
            return result
        after_handlers = self._hooks[hook_point].get(HOOK_AFTER, [])
        final_result = result
        for _name, handler in after_handlers:
            try:
                modified = handler(result=final_result, **context)
                if modified is not None:
                    final_result = modified
            except Exception:
                pass
        return final_result

    def trigger_instead(self, hook_point: str, **context: Any) -> Any | None:
        """
        Вызывает instead-хуки. Если хук возвращает не None,
        его результат используется вместо стандартной логики.

        Returns:
            Результат instead-хука или None.
        """
        if hook_point not in self._hooks:
            return None
        instead_handlers = self._hooks[hook_point].get(HOOK_INSTEAD, [])
        for _name, handler in instead_handlers:
            try:
                result = handler(**context)
                if result is not None:
                    return result
            except Exception:
                pass
        return None


# ─── Глобальный экземпляр ────────────────────────────────────────────

_hook_registry: HookRegistry | None = None


def get_hook_registry() -> HookRegistry:
    """Возвращает глобальный экземпляр HookRegistry."""
    global _hook_registry
    if _hook_registry is None:
        _hook_registry = HookRegistry()
    return _hook_registry


def reset_hook_registry() -> None:
    """Сброс реестра (для тестов)."""
    global _hook_registry
    _hook_registry = None
