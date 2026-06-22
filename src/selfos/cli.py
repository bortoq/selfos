"""
Self OS CLI - Phase 3
Полностью переписан под Architecture Contract
"""

import argparse
import json
import sys
from typing import Any

from selfos.event_factory import EventFactory
from selfos.plugin_registry import PluginRegistry


def cmd_note(args: Any) -> None:
    plugin = PluginRegistry.get_plugin("quick_note")
    result = plugin.execute(text=" ".join(args.text))
    print(f"Note saved with tags: {', '.join(result['suggestions']['suggested_tags'])}")


def cmd_task(args: Any) -> None:
    title = " ".join(args.text)
    EventFactory.create_task_event(
        title,
        project=args.project or "Self OS",
        priority=args.priority or 2
    )
    print(f"Task created: {title}")


def cmd_status(args: Any) -> None:
    print("=== Self OS Status ===")
    print("Phase: 3 - Full Immersion")
    print("Status: Active")


def cmd_suggest(args: Any) -> None:
    plugin = PluginRegistry.get_plugin("smart_suggestions")
    result = plugin.execute()
    print("=== Smart Suggestions ===")
    for s in result["suggestions"]:
        print(f"- {s}")


def cmd_email(args: Any) -> None:
    from selfos.email.service import EmailService
    service = EmailService()

    if args.subcommand == "send":
        result = service.send_email(
            to=args.to,
            subject=args.subject,
            body=" ".join(args.body) if args.body else "",
            force_review=not args.auto
        )
        if not result["success"]:
            print(f"[ERROR] {result.get('error')}")
            return
        print(f"\n=== Email {result['status'].upper()} ===")
        print(f"To: {result['to']}")
        print(f"Subject: {result['subject']}")
        print(f"Body:\n{result['body']}")

    elif args.subcommand == "suggest":
        to = input("To: ").strip()
        subject = input("Subject: ").strip()
        body = input("Body (optional): ").strip()
        suggestion = service.suggest_email(to, subject, body)
        print("\n=== Suggested Email ===")
        print(f"To: {suggestion['message']['to']}")
        print(f"Subject: {suggestion['message']['subject']}")
        print(f"Body:\n{suggestion['message']['body']}")


def cmd_schedule(args: Any) -> None:
    from selfos.scheduler import Scheduler
    scheduler = Scheduler()

    if args.subcommand == "task":
        task = scheduler.add_task(args.title, args.due, args.priority)
        print(f"Task added: {task['title']}")
    elif args.subcommand == "event":
        event = scheduler.add_event(args.title, args.time, args.duration)
        print(f"Event added: {event['title']}")
    elif args.subcommand == "list":
        if args.type == "tasks":
            tasks = scheduler.list_tasks()
            if not tasks:
                print("(no tasks)")
            for t in tasks:
                print(f"- {t['title']}")
        else:
            events = scheduler.list_upcoming_events()
            if not events:
                print("(no upcoming events)")
            for e in events:
                print(f"- {e['title']} @ {e['timestamp']}")


def cmd_browser(args: Any) -> None:
    from selfos.browser import BrowserService
    browser = BrowserService()

    if args.subcommand == "open":
        url = browser.open_link(args.name)
        if url:
            print(f"Opened: {url}")
    elif args.subcommand == "search":
        url = browser.search(" ".join(args.query))
        print(f"Search URL: {url}")
    elif args.subcommand == "links":
        for link in browser.list_links(args.category):
            print(f"- {link.name}: {link.url}")


def cmd_context(args: Any) -> None:
    from selfos.context_engine import ContextEngine
    engine = ContextEngine()

    if args.subcommand == "summary":
        print(engine.get_context_summary())
    elif args.subcommand == "patterns":
        print(engine.get_patterns())
    elif args.subcommand == "suggest":
        for s in engine.get_proactive_suggestions():
            print(f"- {s}")


def cmd_delegate(args: Any) -> None:
    from selfos.delegation_engine import DelegationEngine

    engine = DelegationEngine()

    if args.action == "enable":
        engine.set_override(args.action_type, True)
        print(f"Auto execution enabled for: {args.action_type}")
    elif args.action == "disable":
        engine.set_override(args.action_type, False)
        print(f"Auto execution disabled for: {args.action_type}")
    elif args.action == "status":
        allowed = engine.should_auto_execute(args.action_type)
        print(f"{args.action_type}: {'AUTO' if allowed else 'REVIEW'}")
    elif args.action == "rule":
        _cmd_delegate_rule(engine, args)




def _cmd_delegate_rule(engine: Any, args: Any) -> None:
    """Handle delegation rule subcommands."""
    from selfos.delegation_rules import DelegationRule

    if args.rule_action == "list":
        rules = engine.list_rules()
        if not rules:
            print("No delegation rules defined.")
            return
        print("=== Delegation Rules ===")
        for r in rules:
            status = "ON" if r["enabled"] else "OFF"
            print(f"  {r['name']} [{status}] (priority {r['priority']})")
            print(f"    Action: {r['action_type']} -> {r['effect']}")
            print(f"    Condition: {r['condition_type']} {r.get('condition_params', {})}")
            if r["description"]:
                print(f"    Description: {r['description']}")
            print()

    elif args.rule_action == "add":
        rule = DelegationRule(
            name=args.name,
            action_type=args.action_type,
            effect=args.effect,
            condition_type=args.condition_type,
            condition_params=args.condition_params or {},
            description=args.description or "",
            priority=args.priority or 50,
            enabled=True,
        )
        try:
            engine.add_rule(rule)
            print(f"Rule '{args.name}' added.")
        except ValueError as e:
            print(f"[ERROR] {e}")
            import sys
            sys.exit(1)

    elif args.rule_action == "remove":
        if engine.remove_rule(args.name):
            print(f"Rule '{args.name}' removed.")
        else:
            print(f"Rule '{args.name}' not found.")

    elif args.rule_action == "info":
        rule = engine.get_rule(args.name)
        if rule:
            for k, v in rule.items():
                k_display = k.replace("_", " ").title()
                print(f"{k_display}: {v}")
        else:
            print(f"Rule '{args.name}' not found.")

def cmd_plugin(args: Any) -> None:
    """Plugin management commands."""
    from selfos.plugin_registry import PluginRegistry

    if args.action == "list":
        meta = PluginRegistry.list_plugins_with_metadata()
        if not meta:
            print("No plugins installed.")
            return
        print("=== Installed Plugins ===")
        for info in meta:
            print(f"  {info['name']} v{info.get('version', '?')}")
            print(f"    Author: {info.get('author', '?')}")
            print(f"    Description: {info.get('description', '?')}")
            if info.get('protocol'):
                print(f"    Protocol: {info['protocol']}")
            print()

    elif args.action == "init":
        from selfos.plugin_sdk import scaffold_plugin
        name = args.name
        path = args.path or name.replace("-", "_")
        files = scaffold_plugin(
            name=name,
            dest_dir=path,
            author=args.author or "",
            description=args.description or "",
            protocol=args.protocol or "",
        )
        print(f"Created plugin '{name}' in {path}/")
        for f in files:
            print(f"  - {f}")
        print()
        print("Next steps:")
        print(f"  1. Implement execute() in {path}/{name.replace('-', '_')}.py")
        print(f"  2. Register: cd {path} && python -c \"")
        print("       from selfos.plugin_registry import PluginRegistry")
        print("       from plugin_manifest import PluginManifest")
        print("       manifest = PluginManifest.from_file('plugin.yaml')")
        print("       PluginRegistry.install_global(manifest)")
        print("     \"")
        print("  3. Test: selfos plugin list")

    elif args.action == "info":
        from selfos.plugin_registry import PluginRegistry
        manifest = PluginRegistry.get_plugin_manifest(args.name)
        if manifest:
            print(f"Name: {manifest.name}")
            print(f"Version: {manifest.version}")
            print(f"Author: {manifest.author}")
            print(f"Description: {manifest.description}")
            print(f"Entry point: {manifest.entry_point}")
            print(f"Protocol: {manifest.protocol}")
            if manifest.dependencies:
                print(f"Dependencies: {', '.join(manifest.dependencies)}")
        else:
            # Built-in plugin
            try:
                plugin = PluginRegistry.get_plugin(args.name)
                info = plugin.get_info()
                for k, v in info.to_dict().items():
                    print(f"{k.replace('_', ' ').title()}: {v}")
            except ValueError:
                print(f"Plugin '{args.name}' not found.")
                sys.exit(1)

    elif args.action == "create":
        # create = init + immediate registration
        from selfos.plugin_manifest import PluginManifest
        from selfos.plugin_registry import PluginRegistry
        from selfos.plugin_sdk import scaffold_plugin

        name = args.name
        path = args.path or name.replace("-", "_")
        scaffold_plugin(
            name=name,
            dest_dir=path,
            author=args.author or "",
            description=args.description or "",
            protocol=args.protocol or "",
        )

        manifest = PluginManifest.from_file(f"{path}/plugin.yaml")
        PluginRegistry.install_global(manifest)
        print(f"Plugin '{name}' created and registered.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="selfos", description="Self OS - Personal Operating System"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # note
    note = subparsers.add_parser("note", help="Create a note")
    note.add_argument("text", nargs="+")
    note.set_defaults(func=cmd_note)

    # task
    task = subparsers.add_parser("task", help="Create a task")
    task.add_argument("text", nargs="+")
    task.add_argument("--project", "-p")
    task.add_argument("--priority", "-P", type=int)
    task.set_defaults(func=cmd_task)

    # status
    status = subparsers.add_parser("status", help="Show status")
    status.set_defaults(func=cmd_status)

    # suggest
    suggest = subparsers.add_parser("suggest", help="Get suggestions")
    suggest.set_defaults(func=cmd_suggest)

    # email
    email = subparsers.add_parser("email", help="Email operations")
    email_sub = email.add_subparsers(dest="subcommand", required=True)
    email_send = email_sub.add_parser("send", help="Send email")
    email_send.add_argument("to")
    email_send.add_argument("subject")
    email_send.add_argument("body", nargs="*")
    email_send.add_argument("--auto", action="store_true")
    email_send.set_defaults(func=cmd_email)
    email_suggest = email_sub.add_parser("suggest", help="Email suggestions")
    email_suggest.set_defaults(func=cmd_email)

    # schedule
    schedule = subparsers.add_parser("schedule", help="Task and event scheduler")
    schedule_sub = schedule.add_subparsers(dest="subcommand", required=True)
    schedule_task = schedule_sub.add_parser("task", help="Add a task")
    schedule_task.add_argument("title")
    schedule_task.add_argument("--due")
    schedule_task.add_argument("--priority", type=int, default=2)
    schedule_task.set_defaults(func=cmd_schedule)
    schedule_event = schedule_sub.add_parser("event", help="Add an event")
    schedule_event.add_argument("title")
    schedule_event.add_argument("time")
    schedule_event.add_argument("--duration", type=int, default=60)
    schedule_event.set_defaults(func=cmd_schedule)
    schedule_list = schedule_sub.add_parser("list", help="List tasks or events")
    schedule_list.add_argument("type", choices=["tasks", "events"])
    schedule_list.set_defaults(func=cmd_schedule)

    # browser
    browser = subparsers.add_parser("browser", help="Quick web access")
    browser_sub = browser.add_subparsers(dest="subcommand", required=True)
    browser_open = browser_sub.add_parser("open", help="Open a quick link")
    browser_open.add_argument("name")
    browser_open.set_defaults(func=cmd_browser)
    browser_search = browser_sub.add_parser("search", help="Web search")
    browser_search.add_argument("query", nargs="+")
    browser_search.set_defaults(func=cmd_browser)
    browser_links = browser_sub.add_parser("links", help="List quick links")
    browser_links.add_argument("--category")
    browser_links.set_defaults(func=cmd_browser)

    # context
    context = subparsers.add_parser("context", help="Context Engine")
    context_sub = context.add_subparsers(dest="subcommand", required=True)
    context_summary = context_sub.add_parser("summary", help="Show summary")
    context_summary.set_defaults(func=cmd_context)
    context_patterns = context_sub.add_parser("patterns", help="Show patterns")
    context_patterns.set_defaults(func=cmd_context)
    context_suggest = context_sub.add_parser("suggest", help="Get proactive suggestions")
    context_suggest.set_defaults(func=cmd_context)

    # delegate
    delegate = subparsers.add_parser("delegate", help="Manage delegation")
    delegate_sub = delegate.add_subparsers(dest="action", required=True)

    # legacy: enable/disable/status
    delegate_enable = delegate_sub.add_parser("enable", help="Enable auto-execution")
    delegate_enable.add_argument("action_type")
    delegate_enable.set_defaults(func=cmd_delegate)

    delegate_disable = delegate_sub.add_parser("disable", help="Disable auto-execution")
    delegate_disable.add_argument("action_type")
    delegate_disable.set_defaults(func=cmd_delegate)

    delegate_status = delegate_sub.add_parser("status", help="Check delegation status")
    delegate_status.add_argument("action_type")
    delegate_status.set_defaults(func=cmd_delegate)

    # rules subcommand
    delegate_rule = delegate_sub.add_parser("rule", help="Manage delegation rules")
    delegate_rule_sub = delegate_rule.add_subparsers(dest="rule_action", required=True)

    rule_list = delegate_rule_sub.add_parser("list", help="List all rules")
    rule_list.set_defaults(func=cmd_delegate)

    rule_add = delegate_rule_sub.add_parser("add", help="Add a delegation rule")
    rule_add.add_argument("name", help="Rule name (unique identifier)")
    rule_add.add_argument("action_type", help="Action type (e.g. quick_note)")
    rule_add.add_argument("--effect", choices=["allow", "deny"], default="allow",
                          help="Effect when condition matches")
    rule_add.add_argument("--condition-type", dest="condition_type",
                          choices=["always", "never", "trust_threshold", "time_range"],
                          default="always", help="Type of condition")
    rule_add.add_argument("--condition-params", dest="condition_params",
                          type=json.loads, default={},
                          help="Condition parameters (JSON dict)")
    rule_add.add_argument("--description", "-d", default="", help="Rule description")
    rule_add.add_argument("--priority", "-p", type=int, default=50,
                          help="Rule priority (higher = higher priority)")
    rule_add.set_defaults(func=cmd_delegate)

    rule_remove = delegate_rule_sub.add_parser("remove", help="Remove a rule")
    rule_remove.add_argument("name", help="Rule name")
    rule_remove.set_defaults(func=cmd_delegate)

    rule_info = delegate_rule_sub.add_parser("info", help="Show rule details")
    rule_info.add_argument("name", help="Rule name")
    rule_info.set_defaults(func=cmd_delegate)

    # plugin management (Phase 4)
    plugin = subparsers.add_parser("plugin", help="Manage plugins")
    plugin_sub = plugin.add_subparsers(dest="action", required=True)

    plugin_list = plugin_sub.add_parser("list", help="List installed plugins")
    plugin_list.set_defaults(func=cmd_plugin)

    plugin_init = plugin_sub.add_parser("init", help="Scaffold a new plugin")
    plugin_init.add_argument("name", help="Plugin name (e.g. my-plugin)")
    plugin_init.add_argument("--author", help="Author name")
    plugin_init.add_argument("--description", help="Plugin description")
    plugin_init.add_argument("--protocol", choices=[
        "", "NotingPlugin", "CategorizerPlugin", "SummarizerPlugin",
    ], default="", help="Protocol to implement")
    plugin_init.add_argument("--path", "-p", help="Target directory")
    plugin_init.set_defaults(func=cmd_plugin)

    plugin_info = plugin_sub.add_parser("info", help="Show plugin metadata")
    plugin_info.add_argument("name", help="Plugin name")
    plugin_info.set_defaults(func=cmd_plugin)

    plugin_create = plugin_sub.add_parser("create", help="Create and register a plugin")
    plugin_create.add_argument("name", help="Plugin name")
    plugin_create.add_argument("--author", help="Author name")
    plugin_create.add_argument("--description", help="Plugin description")
    plugin_create.add_argument("--protocol", choices=[
        "", "NotingPlugin", "CategorizerPlugin", "SummarizerPlugin",
    ], default="", help="Protocol to implement")
    plugin_create.add_argument("--path", "-p", help="Target directory")
    plugin_create.set_defaults(func=cmd_plugin)

    return parser


def main(argv: list[str] | None = None) -> None:
    from selfos.unified_interface import interface
    parser = build_parser()
    args = parser.parse_args(argv)

    if hasattr(args, "func"):
        kwargs = {k: v for k, v in vars(args).items()
                  if k not in ('func', 'command')}
        result = interface.execute(args.command, **kwargs)
        if not result.get("success", True):
            print(f"[ERROR] {result.get('error')}", file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
