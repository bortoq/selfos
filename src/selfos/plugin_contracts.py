"""
Plugin contracts — TypedDicts и Protocols для плагинов Self OS.

Даёт type-safe контракты для execute() вместо голого **kwargs.

Использование:
    plugin = PluginRegistry.get_plugin("quick_note")
    assert isinstance(plugin, NotingPlugin)
    result = plugin.execute(text="Hello")  # IDE подсказывает параметры
"""

from typing import Any, Protocol, TypedDict, runtime_checkable

# ─── Базовые типы ───────────────────────────────────────────────────

class PluginRequest(TypedDict, total=False):
    """Базовый запрос к плагину."""
    pass


class PluginResponse(TypedDict, total=False):
    """Базовый ответ плагина."""
    success: bool
    error: str


# ─── Конкретные типы запросов ────────────────────────────────────────

class NoteRequest(PluginRequest):
    """Параметры для quick_note / noting-плагинов."""
    text: str


class CategorizeRequest(PluginRequest):
    """Параметры для категоризации."""
    title: str


class EventsRequest(PluginRequest):
    """Параметры с списком событий."""
    events: list[dict[str, Any]]


class SmartSuggestRequest(PluginRequest):
    """Параметры для smart_suggestions."""
    recent_events: list[dict[str, Any]] | None


# ─── Конкретные типы ответов ─────────────────────────────────────────

class NoteResponse(PluginResponse):
    """Ответ noting-плагина."""
    event: dict[str, Any]
    suggestions: dict[str, Any]


class CategorizeResponse(PluginResponse):
    """Ответ плагина категоризации."""
    title: str
    suggested_category: str
    status: str


class SummaryResponse(PluginResponse):
    """Ответ daily_summary / weekly_report."""
    summary: str
    total_events: int


class SuggestionsResponse(PluginResponse):
    """Ответ smart_suggestions."""
    suggestions: list[str]


# ─── Protocols ───────────────────────────────────────────────────────

@runtime_checkable
class NotingPlugin(Protocol):
    """Плагин для создания заметок."""
    name: str
    description: str

    def execute(self, text: str, **kwargs: Any) -> dict[str, Any]:
        ...


@runtime_checkable
class CategorizerPlugin(Protocol):
    """Плагин для категоризации."""
    name: str
    description: str

    def execute(self, title: str, **kwargs: Any) -> dict[str, Any]:
        ...


@runtime_checkable
class SummarizerPlugin(Protocol):
    """Плагин для суммаризации событий."""
    name: str
    description: str

    def execute(self, events: list[dict[str, Any]], **kwargs: Any) -> dict[str, Any]:
        ...


@runtime_checkable
class SmartSuggestPlugin(Protocol):
    """Плагин проактивных предложений."""
    name: str
    description: str

    def execute(self, recent_events: list[dict[str, Any]] | None = None,
                **kwargs: Any) -> dict[str, Any]:
        ...
