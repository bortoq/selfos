"""Smoke tests for CLI commands."""

import pytest

from selfos.cli import main


def test_cli_status(capsys):
    """status command prints version info."""
    main(["status"])
    captured = capsys.readouterr()
    assert "Self OS" in captured.out
    assert "Active" in captured.out


def test_cli_note(capsys):
    """note command creates a note."""
    main(["note", "test", "note", "content"])
    captured = capsys.readouterr()
    assert "Note saved" in captured.out


def test_cli_task(capsys):
    """task command creates a task."""
    main(["task", "test", "task"])
    captured = capsys.readouterr()
    assert "Task created:" in captured.out


def test_cli_suggest(capsys):
    """suggest command returns suggestions."""
    main(["suggest"])
    captured = capsys.readouterr()
    assert "Smart Suggestions" in captured.out


def test_cli_browser_links(capsys):
    """browser links lists quick links."""
    main(["browser", "links"])
    captured = capsys.readouterr()
    assert "gmail" in captured.out.lower()


def test_cli_browser_open(capsys):
    """browser open returns URL."""
    main(["browser", "open", "gmail"])
    captured = capsys.readouterr()
    assert "Opened:" in captured.out


def test_cli_browser_search(capsys):
    """browser search returns URL."""
    main(["browser", "search", "test", "query"])
    captured = capsys.readouterr()
    assert "Search URL:" in captured.out


def test_cli_schedule_task(capsys):
    """schedule task adds a task."""
    main(["schedule", "task", "Test task", "--due", "tomorrow"])
    captured = capsys.readouterr()
    assert "Task added:" in captured.out


def test_cli_schedule_event(capsys):
    """schedule event adds an event."""
    main(["schedule", "event", "Meeting", "14:00", "--duration", "60"])
    captured = capsys.readouterr()
    assert "Event added:" in captured.out


def test_cli_schedule_list_tasks(capsys):
    """schedule list tasks."""
    main(["schedule", "list", "tasks"])
    # May be empty, just check it doesn't crash


def test_cli_context_summary(capsys):
    """context summary works."""
    main(["context", "summary"])
    captured = capsys.readouterr()
    assert captured.out is not None


def test_cli_context_patterns(capsys):
    """context patterns works."""
    main(["context", "patterns"])
    captured = capsys.readouterr()
    assert captured.out is not None


def test_cli_context_suggest(capsys):
    """context suggest works."""
    main(["context", "suggest"])
    captured = capsys.readouterr()
    assert captured.out is not None


def test_cli_delegate_status(capsys):
    """delegate status shows current mode."""
    main(["delegate", "status", "email_send"])
    captured = capsys.readouterr()
    assert "AUTO" in captured.out or "REVIEW" in captured.out


def test_cli_delegate_enable(capsys):
    """delegate enable turns on auto."""
    main(["delegate", "enable", "email_send"])
    captured = capsys.readouterr()
    assert "enabled" in captured.out


def test_cli_delegate_disable(capsys):
    """delegate disable turns off auto."""
    main(["delegate", "disable", "email_send"])
    captured = capsys.readouterr()
    assert "disabled" in captured.out


def test_cli_no_args():
    """No args: argparse exits with code 2."""
    with pytest.raises(SystemExit) as exc_info:
        main([])
    assert exc_info.value.code == 2


def test_cli_unknown_command():
    """Unknown command: argparse exits with code 2."""
    with pytest.raises(SystemExit):
        main(["unknown-command-xyz"])
