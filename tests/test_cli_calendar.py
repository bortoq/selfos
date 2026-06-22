from __future__ import annotations

from selfos.cli import main


class DummyCalendarPlugin:
    def today(self) -> list[dict[str, str]]:
        return [
            {
                "summary": "Standup",
                "start": "2026-06-22T09:00:00Z",
                "end": "2026-06-22T09:30:00Z",
            }
        ]

    def create_event(
        self,
        *,
        summary: str,
        start: str,
        end: str,
        location: str | None = None,
    ) -> dict[str, str]:
        assert summary == "Planning"
        return {"id": "evt-1", "summary": summary}


def test_cli_calendar_today_and_create(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        "selfos.cli._create_calendar_plugin",
        lambda profile=None: DummyCalendarPlugin(),
    )

    main(["calendar", "today"])
    main(
        [
            "calendar",
            "create",
            "--summary",
            "Planning",
            "--start",
            "2026-06-22T12:00:00Z",
            "--end",
            "2026-06-22T13:00:00Z",
        ]
    )

    captured = capsys.readouterr()
    assert "Standup" in captured.out
    assert "evt-1" in captured.out
