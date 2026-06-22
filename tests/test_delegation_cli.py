from selfos.cli import build_parser


def test_delegate_enable_command():
    parser = build_parser()
    args = parser.parse_args(["delegate", "enable", "email_send"])
    assert args.command == "delegate"
    assert args.action == "enable"
    assert args.action_type == "email_send"


def test_delegate_status_command():
    parser = build_parser()
    args = parser.parse_args(["delegate", "status", "photo_classification"])
    assert args.action == "status"