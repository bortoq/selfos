from selfos.cli import build_parser

# ─── Legacy delegation commands ───────────────────────────────────────

def test_delegate_enable_command():
    parser = build_parser()
    args = parser.parse_args(["delegate", "enable", "email_send"])
    assert args.command == "delegate"
    assert args.action == "enable"
    assert args.action_type == "email_send"


def test_delegate_disable_command():
    parser = build_parser()
    args = parser.parse_args(["delegate", "disable", "quick_note"])
    assert args.action == "disable"
    assert args.action_type == "quick_note"


def test_delegate_status_command():
    parser = build_parser()
    args = parser.parse_args(["delegate", "status", "photo_classification"])
    assert args.action == "status"


# ─── Rule commands ────────────────────────────────────────────────────

def test_delegate_rule_list():
    parser = build_parser()
    args = parser.parse_args(["delegate", "rule", "list"])
    assert args.action == "rule"
    assert args.rule_action == "list"


def test_delegate_rule_add():
    parser = build_parser()
    args = parser.parse_args([
        "delegate", "rule", "add", "my-rule", "quick_note",
        "--effect", "allow",
        "--condition-type", "trust_threshold",
        "--condition-params", '{"min_trust": 5}',
        "--description", "My test rule",
        "--priority", "80",
    ])
    assert args.action == "rule"
    assert args.rule_action == "add"
    assert args.name == "my-rule"
    assert args.action_type == "quick_note"
    assert args.effect == "allow"
    assert args.condition_type == "trust_threshold"
    assert args.condition_params == {"min_trust": 5}
    assert args.description == "My test rule"
    assert args.priority == 80


def test_delegate_rule_add_defaults():
    """Test rule add with minimal arguments."""
    parser = build_parser()
    args = parser.parse_args([
        "delegate", "rule", "add", "min-rule", "photo_classification",
    ])
    assert args.effect == "allow"
    assert args.condition_type == "always"
    assert args.condition_params == {}
    assert args.description == ""
    assert args.priority == 50


def test_delegate_rule_remove():
    parser = build_parser()
    args = parser.parse_args(["delegate", "rule", "remove", "my-rule"])
    assert args.action == "rule"
    assert args.rule_action == "remove"
    assert args.name == "my-rule"


def test_delegate_rule_info():
    parser = build_parser()
    args = parser.parse_args(["delegate", "rule", "info", "my-rule"])
    assert args.action == "rule"
    assert args.rule_action == "info"
    assert args.name == "my-rule"


def test_delegate_rule_deny_effect():
    parser = build_parser()
    args = parser.parse_args([
        "delegate", "rule", "add", "deny-rule", "email_send",
        "--effect", "deny",
    ])
    assert args.effect == "deny"
