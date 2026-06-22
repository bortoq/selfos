from __future__ import annotations

from selfos.cli import main


class DummyGitHubPlugin:
    def notifications(self) -> list[dict[str, str]]:
        return [{"id": "n1", "title": "Review PR", "repository": "bortoq/selfos"}]

    def issues(self, repo: str, state: str = "open") -> list[dict[str, str]]:
        assert repo == "bortoq/selfos"
        return [{"id": "1", "title": "Bug", "state": state}]


def test_cli_github_notifications_and_issues(monkeypatch, capsys) -> None:
    monkeypatch.setattr("selfos.cli._create_github_plugin", lambda: DummyGitHubPlugin())

    main(["github", "notifications"])
    main(["github", "issues", "bortoq/selfos"])

    captured = capsys.readouterr()
    assert "Review PR" in captured.out
    assert "Bug" in captured.out
