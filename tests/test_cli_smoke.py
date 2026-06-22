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


def test_cli_no_args():
    """No args: argparse exits with code 2."""
    with pytest.raises(SystemExit) as exc_info:
        main([])
    assert exc_info.value.code == 2


def test_cli_unknown_command():
    """Unknown command: argparse exits with code 2."""
    with pytest.raises(SystemExit):
        main(["unknown-command-xyz"])
