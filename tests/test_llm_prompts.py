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
    assert "task_create" in rendered


def test_prompt_manager_templates_define_data_wrappers() -> None:
    manager = PromptManager()
    for template_name in ("suggest_general", "suggest_email", "suggest_summary"):
        rendered = manager.render(template_name, {"summary": "hello"})
        assert "<USER_DATA_START>" in rendered
        assert "<USER_DATA_END>" in rendered
