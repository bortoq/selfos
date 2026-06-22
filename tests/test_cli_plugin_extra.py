"""
Тесты для CLI команд плагинов: install, remove, update, search.
"""

from selfos.cli import build_parser


def test_plugin_install_parser():
    parser = build_parser()
    args = parser.parse_args(["plugin", "install", "example-greeter"])
    assert args.command == "plugin"
    assert args.action == "install"
    assert args.name == "example-greeter"


def test_plugin_remove_parser():
    parser = build_parser()
    args = parser.parse_args(["plugin", "remove", "my-plugin"])
    assert args.action == "remove"
    assert args.name == "my-plugin"


def test_plugin_update_all():
    """update without name = check all updates."""
    parser = build_parser()
    args = parser.parse_args(["plugin", "update"])
    assert args.action == "update"
    assert args.name is None


def test_plugin_update_specific():
    parser = build_parser()
    args = parser.parse_args(["plugin", "update", "my-plugin"])
    assert args.action == "update"
    assert args.name == "my-plugin"


def test_plugin_search():
    parser = build_parser()
    args = parser.parse_args(["plugin", "search", "note"])
    assert args.action == "search"
    assert args.query == "note"
    assert args.field == "all"


def test_plugin_search_with_field():
    parser = build_parser()
    args = parser.parse_args(["plugin", "search", "email", "--field", "tags"])
    assert args.query == "email"
    assert args.field == "tags"
