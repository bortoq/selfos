import pytest

from src.selfos.cli import build_parser


def test_cli_note_command():
    parser = build_parser()
    args = parser.parse_args(["note", "Remember", "to", "buy", "coffee"])
    assert args.command == "note"
    assert "Remember" in args.text


def test_cli_task_command():
    parser = build_parser()
    args = parser.parse_args(
        ["task", "Finish", "Phase", "3", "--project", "SelfOS", "--priority", "1"]
    )
    assert args.command == "task"
    assert args.project == "SelfOS"
    assert args.priority == 1


def test_cli_status_command():
    parser = build_parser()
    args = parser.parse_args(["status"])
    assert args.command == "status"


def test_cli_suggest_command():
    parser = build_parser()
    args = parser.parse_args(["suggest"])
    assert args.command == "suggest"


def test_cli_unknown_command():
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["unknown"])