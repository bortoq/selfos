from __future__ import annotations

from typing import Any

from selfos.cli import main


class DummySetupManager:
    def __init__(self) -> None:
        self.started = None

    def start_browser_flow(self) -> None:
        self.started = "browser"

    def start_device_flow(self) -> None:
        self.started = "device"

    def test_connection(self) -> bool:
        self.started = "test"
        return True


class DummyGmailPlugin:
    def unread_count(self) -> int:
        return 3

    def list_messages(
        self,
        max_results: int = 10,
        query: str | None = None,
        unread_only: bool = False,
    ) -> list[dict[str, Any]]:
        assert max_results == 10
        assert query is None
        assert unread_only is True
        return [{"subject": "Hello", "from": "boss@example.com", "date": "today"}]


def test_cli_profile_create_and_switch(capsys) -> None:
    main(["profile", "create", "work"])
    main(["profile", "switch", "work"])
    main(["profile", "current"])

    captured = capsys.readouterr()
    assert "work" in captured.out


def test_cli_plugin_setup_gmail_headless(monkeypatch, capsys) -> None:
    manager = DummySetupManager()
    monkeypatch.setattr("selfos.cli._create_oauth_manager", lambda provider, profile=None: manager)

    main(["plugin", "setup", "gmail", "--headless"])

    captured = capsys.readouterr()
    assert manager.started == "device"
    assert "gmail" in captured.out.lower()


def test_cli_gmail_unread_list(monkeypatch, capsys) -> None:
    monkeypatch.setattr("selfos.cli._create_gmail_plugin", lambda profile=None: DummyGmailPlugin())

    main(["gmail", "list", "--unread"])
    main(["gmail", "unread_count"])

    captured = capsys.readouterr()
    assert "Hello" in captured.out
    assert "3" in captured.out
