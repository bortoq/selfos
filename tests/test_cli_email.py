import pytest
from src.selfos.cli import build_parser


def test_email_send_command():
    parser = build_parser()
    args = parser.parse_args(["email", "send", "test@example.com", "Hello", "Body", "--auto"])
    assert args.command == "email"
    assert args.subcommand == "send"
    assert args.to == "test@example.com"
    assert args.auto is True


def test_email_suggest_command():
    parser = build_parser()
    args = parser.parse_args(["email", "suggest"])
    assert args.command == "email"
    assert args.subcommand == "suggest"