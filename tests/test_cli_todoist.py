from __future__ import annotations

from selfos.cli import main


class DummyTodoistPlugin:
    def list_tasks(
        self,
        *,
        project_id: str | None = None,
        label: str | None = None,
    ) -> list[dict[str, object]]:
        return [{"id": "t1", "content": "Ship Phase 5c", "priority": 4}]

    def create_task(
        self,
        *,
        content: str,
        due: str | None = None,
        priority: int = 1,
    ) -> dict[str, object]:
        assert content == "Write docs"
        return {"id": "t2", "content": content}

    def complete_task(self, task_id: str) -> bool:
        assert task_id == "t1"
        return True


def test_cli_todoist_list_create_complete(monkeypatch, capsys) -> None:
    monkeypatch.setattr("selfos.cli._create_todoist_plugin", lambda: DummyTodoistPlugin())

    main(["todoist", "list"])
    main(["todoist", "create", "--content", "Write docs"])
    main(["todoist", "complete", "t1"])

    captured = capsys.readouterr()
    assert "Ship Phase 5c" in captured.out
    assert "t2" in captured.out
    assert "Completed" in captured.out
