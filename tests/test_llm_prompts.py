from __future__ import annotations

from selfos.llm.prompts import PromptManager


def test_prompt_manager_loads_builtin_template() -> None:
    manager = PromptManager()
    template = manager.load_template("suggest_general")
    assert "system" in template
    assert "user_template" in template


def test_prompt_manager_renders_context() -> None:
    manager = PromptManager()
    rendered = manager.render(
        "suggest_general",
        {"summary": "hello", "events": ["a", "b"]},
    )
    assert "hello" in rendered
    assert "USER_DATA_START" in rendered
