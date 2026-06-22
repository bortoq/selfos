"""
Self OS CLI - Phase 3
Полностью переписан под Architecture Contract
"""

import argparse
import sys

from src.selfos.event_factory import EventFactory
from src.selfos.plugin_registry import PluginRegistry


def cmd_note(args):
    plugin = PluginRegistry.get_plugin("quick_note")
    result = plugin.execute(text=" ".join(args.text))
    print(f"Note saved with tags: {', '.join(result['suggestions']['suggested_tags'])}")


def cmd_task(args):
    title = " ".join(args.text)
    EventFactory.create_task_event(
        title,
        project=args.project or "Self OS",
        priority=args.priority or 2
    )
    print(f"Task created: {title}")


def cmd_status(args):
    print("=== Self OS Status ===")
    print("Phase: 3 - Full Immersion")
    print("Status: Active")


def cmd_suggest(args):
    plugin = PluginRegistry.get_plugin("smart_suggestions")
    result = plugin.execute()
    print("=== Smart Suggestions ===")
    for s in result["suggestions"]:
        print(f"- {s}")


def cmd_email(args):
    from src.selfos.email.service import EmailService
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


def cmd_schedule(args):
    from src.selfos.scheduler import Scheduler
    scheduler = Scheduler()

    if args.subcommand == "task":
        task = scheduler.add_task(args.title, args.due, args.priority)
        print(f"Task added: {task['title']}")
    elif args.subcommand == "event":
        event = scheduler.add_event(args.title, args.time, args.duration)
        print(f"Event added: {event['title']}")
    elif args.subcommand == "list":
        if args.type == "tasks":
            for t in scheduler.list_tasks():
                print(f"- {t['title']}")
        else:
            for e in scheduler.list_upcoming_events():
                print(f"- {e['title']} @ {e['timestamp']}")


def cmd_browser(args):
    from src.selfos.browser import BrowserService
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


def cmd_context(args):
    from src.selfos.context_engine import ContextEngine
    engine = ContextEngine()

    if args.subcommand == "summary":
        print(engine.get_context_summary())
    elif args.subcommand == "patterns":
        print(engine.get_patterns())
    elif args.subcommand == "suggest":
        for s in engine.get_proactive_suggestions():
            print(f"- {s}")


def cmd_delegate(args):
    from src.selfos.delegation_engine import DelegationEngine

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


def build_parser():
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
    delegate = subparsers.add_parser("delegate", help="Manage delegation overrides")
    delegate.add_argument("action", choices=["enable", "disable", "status"])
    delegate.add_argument("action_type")
    delegate.set_defaults(func=cmd_delegate)

    return parser


def main(argv: list[str] | None = None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if hasattr(args, "func"):
        try:
            args.func(args)
        except Exception as e:
            print(f"[ERROR] {e}")
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()