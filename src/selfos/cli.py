"""
Self OS CLI - Phase 3
Полностью переписан под Architecture Contract
"""

import argparse
import dataclasses
import json
import os
import subprocess
import sys
import tempfile
from typing import Any

from selfos.event_factory import EventFactory
from selfos.hooks import get_hook_registry
from selfos.llm.suggestion_engine import SuggestionEngine
from selfos.plugin_registry import PluginRegistry


def cmd_note(args: Any) -> None:
    hooks = get_hook_registry()
    ctx = hooks.trigger_before("note:create", text=" ".join(args.text))
    plugin = PluginRegistry.get_plugin("quick_note")
    result = plugin.execute(text=ctx.get("text", ""))
    result = hooks.trigger_after("note:create", result=result, **ctx)
    tags = result.get("suggestions", {}).get("suggested_tags", [])
    print(f"Note saved with tags: {', '.join(tags)}")


def cmd_task(args: Any) -> None:
    hooks = get_hook_registry()
    ctx = hooks.trigger_before("task:create", title=" ".join(args.text),
                                project=args.project or "Self OS",
                                priority=args.priority or 2)
    EventFactory.create_task_event(
        ctx.get("title", ""),
        project=ctx.get("project", "Self OS"),
        priority=ctx.get("priority", 2)
    )
    result = {"title": ctx.get("title", "")}
    result = hooks.trigger_after("task:create", result=result, **ctx)
    print(f"Task created: {result.get('title', ctx.get('title', ''))}")


def cmd_status(args: Any) -> None:
    print("=== Self OS Status ===")
    print("Phase: 4 - Platform")
    print("Status: Active")


def cmd_suggest(args: Any) -> None:
    engine = _create_suggestion_engine()

    if getattr(args, "approve", None):
        result = engine.approve_suggestion(args.approve)
        print(f"Approved suggestion: {result['suggestion_id']}")
        return
    if getattr(args, "rate", None):
        suggestion_id, rating_raw = args.rate
        engine.rate_suggestion(suggestion_id, int(rating_raw))
        print(f"Rated suggestion {suggestion_id}: {rating_raw}")
        return
    if getattr(args, "stats", False):
        print(json.dumps(engine.get_stats(), indent=2, ensure_ascii=False))
        return
    if getattr(args, "clear_cache", False):
        engine.clear_cache()
        print("LLM cache cleared.")
        return

    mode = "llm" if getattr(args, "llm", False) else "rules"
    response = engine.get_suggestions(mode=mode, provider=getattr(args, "provider", None))
    print("=== Smart Suggestions ===")
    if response.get("backend_used") == "rules_fallback":
        reason = response.get("fallback_reason", "unknown")
        print(f"[fallback to rules] reason={reason}")
    for suggestion in response.get("suggestions", []):
        if isinstance(suggestion, dict):
            print(f"- [{suggestion.get('id')}] {suggestion.get('summary')}")
        else:
            print(f"- {suggestion}")


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


def _resolve_google_credentials() -> tuple[str, str]:
    client_id = os.getenv("GOOGLE_CLIENT_ID", "")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        raise ValueError(
            "Missing Google OAuth credentials. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET."
        )
    return client_id, client_secret


def _create_oauth_manager(provider: str, profile: str | None = None) -> Any:
    from selfos.config import current_profile
    from selfos.integrations.oauth_manager import OAuthManager, _get_provider_configs
    from selfos.integrations.token_store import SecureTokenStore

    provider_configs = _get_provider_configs()
    if provider not in provider_configs:
        raise ValueError(f"Unknown OAuth provider: {provider}")

    base_config = provider_configs[provider]
    if provider in {"gmail", "calendar"}:
        client_id, client_secret = _resolve_google_credentials()
    else:
        env_prefix = provider.upper()
        client_id = os.getenv(f"{env_prefix}_CLIENT_ID", "")
        client_secret = os.getenv(f"{env_prefix}_CLIENT_SECRET", "")
        if not client_id or not client_secret:
            raise ValueError(
                f"Missing OAuth credentials for {provider}. "
                f"Set {env_prefix}_CLIENT_ID and {env_prefix}_CLIENT_SECRET."
            )

    config = dataclasses.replace(
        base_config,
        client_id=client_id,
        client_secret=client_secret,
        scopes=list(base_config.scopes),
        extra_auth_params=dict(base_config.extra_auth_params),
        extra_token_params=dict(base_config.extra_token_params),
    )
    store = SecureTokenStore(profile=profile or current_profile())
    return OAuthManager(provider, config, store)


def _create_gmail_plugin(profile: str | None = None) -> Any:
    from selfos.plugins.gmail_plugin import GmailPlugin

    return GmailPlugin(_create_oauth_manager("gmail", profile=profile))


def _create_calendar_plugin(profile: str | None = None) -> Any:
    from selfos.plugins.calendar_integration import GoogleCalendarPlugin

    return GoogleCalendarPlugin(_create_oauth_manager("calendar", profile=profile))


def _create_todoist_plugin() -> Any:
    from selfos.plugins.todoist_integration import TodoistPluginClient

    api_token = os.getenv("TODOIST_API_TOKEN", "")
    if not api_token:
        raise ValueError("Missing Todoist API token. Set TODOIST_API_TOKEN.")
    return TodoistPluginClient(api_token=api_token)


def _create_github_plugin() -> Any:
    from selfos.plugins.github_integration import GitHubPlugin

    api_token = os.getenv("GITHUB_TOKEN", "") or os.getenv("GITHUB_API_TOKEN", "")
    if not api_token:
        raise ValueError("Missing GitHub API token. Set GITHUB_TOKEN.")
    return GitHubPlugin(api_token=api_token)


def _create_suggestion_engine() -> SuggestionEngine:
    return SuggestionEngine()


def _confirm_cloud_opt_in(provider: str) -> bool:
    answer = input(
        f"Warning: {provider} sends redacted context to a cloud LLM provider. "
        "Email subjects, event titles, and task names may still be visible. "
        "Proceed with cloud access? [y/N]: "
    ).strip().lower()
    return answer in {"y", "yes"}


def _edit_text_in_editor(initial_text: str = "") -> str:
    editor = os.getenv("EDITOR")
    if not editor:
        raise ValueError("No message body provided and EDITOR is not set")

    with tempfile.NamedTemporaryFile(mode="w+", suffix=".txt", delete=False) as handle:
        handle.write(initial_text)
        handle.flush()
        temp_path = handle.name

    try:
        subprocess.run([editor, temp_path], check=True)
        with open(temp_path, encoding="utf-8") as handle:
            return handle.read().strip()
    finally:
        try:
            os.unlink(temp_path)
        except OSError:
            pass


def cmd_profile(args: Any) -> None:
    from selfos.config import create_profile, current_profile, list_profiles, set_current_profile

    if args.action == "create":
        path = create_profile(args.name)
        print(f"Profile created: {args.name} ({path})")
    elif args.action == "switch":
        selected = set_current_profile(args.name)
        print(f"Current profile: {selected}")
    elif args.action == "current":
        print(current_profile())
    elif args.action == "list":
        profiles = list_profiles()
        if not profiles:
            print("(no profiles)")
            return
        for profile in profiles:
            print(profile)


def cmd_config(args: Any) -> None:
    from selfos.config import llm_config, update_llm_config

    if args.topic != "llm":
        raise ValueError("Only 'llm' config is supported")

    if not any([args.provider, args.model, args.api_key, args.cloud_opt_in]):
        print(json.dumps(llm_config(), indent=2, ensure_ascii=False))
        return

    current = llm_config()
    requested_provider = args.provider or current.get("provider")
    is_cloud_provider = requested_provider in {"openai", "anthropic"}
    has_cloud_opt_in = bool(args.cloud_opt_in or current.get("cloud_opt_in"))
    if is_cloud_provider and not has_cloud_opt_in:
        if not _confirm_cloud_opt_in(str(requested_provider)):
            raise ValueError("Cloud provider requires explicit opt-in.")
        has_cloud_opt_in = True

    updates: dict[str, Any] = {}
    if args.provider:
        updates["provider"] = args.provider
    if args.model:
        updates["model"] = args.model
    if args.api_key:
        updates["api_key"] = args.api_key
    if args.cloud_opt_in or has_cloud_opt_in:
        updates["cloud_opt_in"] = True
    print(json.dumps(update_llm_config(updates), indent=2, ensure_ascii=False))


def cmd_gmail(args: Any) -> None:
    plugin = _create_gmail_plugin()

    if args.subcommand == "list":
        messages = plugin.list_messages(
            max_results=args.max_results,
            unread_only=args.unread,
        )
        for message in messages:
            print(f"{message['subject']} | {message['from']} | {message['date']}")
    elif args.subcommand == "read":
        message = plugin.read_message(args.message_id)
        print(f"Subject: {message['subject']}")
        print(f"From: {message['from']}")
        print(f"Date: {message['date']}")
        print()
        print(message["body"] or message["snippet"])
    elif args.subcommand == "send":
        body = args.body if args.body is not None else _edit_text_in_editor()
        result = plugin.send_message(to=args.to, subject=args.subject, body=body)
        print(f"Sent Gmail message: {result.get('id', '?')}")
    elif args.subcommand == "search":
        messages = plugin.search_messages(args.query, max_results=args.max_results)
        for message in messages:
            print(f"{message['subject']} | {message['from']} | {message['date']}")
    elif args.subcommand == "unread_count":
        print(plugin.unread_count())
    elif args.subcommand == "labels":
        for label in plugin.list_labels():
            print(label)


def cmd_calendar(args: Any) -> None:
    hooks = get_hook_registry()
    plugin = _create_calendar_plugin()

    if args.subcommand == "today":
        for event in plugin.today():
            print(f"{event['summary']} | {event['start']} -> {event['end']}")
    elif args.subcommand == "list":
        for event in plugin.list_events(
            time_min=args.time_min,
            time_max=args.time_max,
            max_results=args.max_results,
        ):
            print(f"{event['summary']} | {event['start']} -> {event['end']}")
    elif args.subcommand == "create":
        ctx = hooks.trigger_before(
            "calendar:event_created",
            summary=args.summary,
            start=args.start,
            end=args.end,
            location=args.location,
        )
        result = plugin.create_event(
            summary=ctx.get("summary", args.summary),
            start=ctx.get("start", args.start),
            end=ctx.get("end", args.end),
            location=ctx.get("location", args.location),
        )
        result = hooks.trigger_after("calendar:event_created", result=result, **ctx)
        print(f"Created calendar event: {result.get('id')} | {result.get('summary', '')}")
    elif args.subcommand == "update":
        ctx = hooks.trigger_before("calendar:event_updated", event_id=args.event_id)
        result = plugin.update_event(args.event_id, summary=args.summary)
        result = hooks.trigger_after("calendar:event_updated", result=result, **ctx)
        print(f"Updated calendar event: {result.get('id')} | {result.get('summary', '')}")
    elif args.subcommand == "delete":
        deleted = plugin.delete_event(args.event_id)
        print(f"Deleted calendar event: {args.event_id}" if deleted else "Delete failed")
    elif args.subcommand == "freebusy":
        result = plugin.freebusy(args.time_min, args.time_max)
        print(json.dumps(result, indent=2, ensure_ascii=False))


def cmd_todoist(args: Any) -> None:
    hooks = get_hook_registry()
    plugin = _create_todoist_plugin()

    if args.subcommand == "list":
        for task in plugin.list_tasks(project_id=args.project_id, label=args.label):
            print(f"{task['id']} | {task['content']}")
    elif args.subcommand == "create":
        ctx = hooks.trigger_before(
            "task:created",
            content=args.content,
            due=args.due,
            priority=args.priority,
        )
        result = plugin.create_task(
            content=ctx.get("content", args.content),
            due=ctx.get("due", args.due),
            priority=ctx.get("priority", args.priority),
        )
        result = hooks.trigger_after("task:created", result=result, **ctx)
        print(f"Created Todoist task: {result.get('id')} | {result.get('content', '')}")
    elif args.subcommand == "complete":
        ctx = hooks.trigger_before("task:completed", task_id=args.task_id)
        completed = plugin.complete_task(args.task_id)
        hooks.trigger_after("task:completed", result={"completed": completed}, **ctx)
        print(f"Completed Todoist task: {args.task_id}")
    elif args.subcommand == "projects":
        for project in plugin.list_projects():
            print(f"{project['id']} | {project['name']}")
    elif args.subcommand == "labels":
        for label in plugin.list_labels():
            print(label["name"])


def cmd_github(args: Any) -> None:
    hooks = get_hook_registry()
    plugin = _create_github_plugin()

    if args.subcommand == "notifications":
        notifications = plugin.notifications()
        for item in notifications:
            hooks.trigger_after("github:notification", result=item, **item)
            print(f"{item['repository']} | {item['title']}")
    elif args.subcommand == "issues":
        issues = plugin.issues(args.repo, state=args.state)
        for item in issues:
            hooks.trigger_after("github:issue", result=item, **item)
            print(f"{item['state']} | {item['title']}")
    elif args.subcommand == "prs":
        for item in plugin.pull_requests(args.repo, state=args.state):
            print(f"{item['state']} | {item['title']}")
    elif args.subcommand == "search":
        for item in plugin.search(args.query):
            print(f"{item['state']} | {item['title']}")




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

    elif args.action == "install":
        name = args.name
        if name.startswith("http://") or name.startswith("https://") or name.startswith("git@"):
            from selfos.plugin_marketplace import install_plugin_from_url
            try:
                dest = install_plugin_from_url(name)
                repo_name = name.rstrip("/").split("/")[-1].replace(".git", "")
                print(f"Plugin '{repo_name}' installed from {name}")
                print(f"  Location: {dest}")
            except (ValueError, RuntimeError) as e:
                print(f"[ERROR] {e}")
                sys.exit(1)
        else:
            from selfos.plugin_marketplace import install_plugin_from_marketplace
            try:
                dest = install_plugin_from_marketplace(name)
                print(f"Plugin '{name}' installed in {dest}")
            except ValueError as e:
                print(f"[ERROR] {e}")
                sys.exit(1)

    elif args.action == "remove":
        from selfos.plugin_marketplace import remove_plugin
        name = args.name
        if remove_plugin(name, cleanup_files=True):
            print(f"Plugin '{name}' removed.")
        else:
            print(f"Plugin '{name}' not found.")

    elif args.action == "update":
        from selfos.plugin_marketplace import check_for_updates, update_plugin
        if args.name:
            name = args.name
            try:
                new_version = update_plugin(name)
                print(f"Plugin '{name}' updated to v{new_version}")
            except ValueError as e:
                print(f"[ERROR] {e}")
                sys.exit(1)
        else:
            updates = check_for_updates()
            if not updates:
                print("All plugins are up to date.")
            else:
                print("=== Available Updates ===")
                for u in updates:
                    print(f"  {u['name']}: v{u['current_version']} -> v{u['available_version']}")
                    if u.get("description"):
                        print(f"    {u['description']}")
                    print()
                print("Use 'selfos plugin update <name>' to update a specific plugin.")

    elif args.action == "search":
        from selfos.plugin_marketplace import load_marketplace
        marketplace = load_marketplace()
        results = marketplace.search(args.query, field=args.field)
        if not results:
            print(f"No plugins found matching '{args.query}'.")
            return
        print(f"=== Marketplace Results for '{args.query}' ===")
        for p in results:
            print(f"  {p.name} v{p.version}")
            print(f"    Author: {p.author}")
            print(f"    Description: {p.description}")
            if p.protocol:
                print(f"    Protocol: {p.protocol}")
            if p.tags:
                print(f"    Tags: {', '.join(p.tags)}")
            print()
        print("Use 'selfos plugin install <name>' to install a plugin.")

    elif args.action == "setup":
        if args.name not in {"gmail", "calendar"}:
            raise ValueError("Only 'gmail' and 'calendar' setup are supported")
        manager = _create_oauth_manager(args.name)
        if args.test:
            ok = manager.test_connection()
            print(f"{args.name} connection: {'OK' if ok else 'FAILED'}")
        elif args.headless:
            manager.start_device_flow()
            print(f"{args.name} OAuth setup completed via device flow")
        else:
            manager.start_browser_flow()
            print(f"{args.name} OAuth setup completed via browser flow")


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
    suggest.add_argument("--llm", action="store_true")
    suggest.add_argument("--provider", choices=["ollama", "openai", "anthropic"])
    suggest.add_argument("--approve")
    suggest.add_argument("--rate", nargs=2, metavar=("ID", "RATING"))
    suggest.add_argument("--stats", action="store_true")
    suggest.add_argument("--clear-cache", action="store_true")
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

    # config
    config = subparsers.add_parser("config", help="Manage configuration")
    config_sub = config.add_subparsers(dest="topic", required=True)
    config_llm = config_sub.add_parser("llm", help="Manage LLM configuration")
    config_llm.add_argument("--provider", choices=["ollama", "openai", "anthropic"])
    config_llm.add_argument("--model")
    config_llm.add_argument("--api-key")
    config_llm.add_argument("--cloud-opt-in", action="store_true")
    config_llm.set_defaults(func=cmd_config)

    # profile
    profile = subparsers.add_parser("profile", help="Manage runtime profiles")
    profile_sub = profile.add_subparsers(dest="action", required=True)
    profile_create = profile_sub.add_parser("create", help="Create a profile")
    profile_create.add_argument("name")
    profile_create.set_defaults(func=cmd_profile)
    profile_switch = profile_sub.add_parser("switch", help="Switch active profile")
    profile_switch.add_argument("name")
    profile_switch.set_defaults(func=cmd_profile)
    profile_current = profile_sub.add_parser("current", help="Show active profile")
    profile_current.set_defaults(func=cmd_profile)
    profile_list = profile_sub.add_parser("list", help="List profiles")
    profile_list.set_defaults(func=cmd_profile)

    # gmail
    gmail = subparsers.add_parser("gmail", help="Gmail integration")
    gmail_sub = gmail.add_subparsers(dest="subcommand", required=True)
    gmail_list = gmail_sub.add_parser("list", help="List messages")
    gmail_list.add_argument("--unread", action="store_true")
    gmail_list.add_argument("--max-results", dest="max_results", type=int, default=10)
    gmail_list.set_defaults(func=cmd_gmail)
    gmail_read = gmail_sub.add_parser("read", help="Read a message")
    gmail_read.add_argument("message_id")
    gmail_read.set_defaults(func=cmd_gmail)
    gmail_send = gmail_sub.add_parser("send", help="Send a message")
    gmail_send.add_argument("--to", required=True)
    gmail_send.add_argument("--subject", required=True)
    gmail_send.add_argument("--body")
    gmail_send.set_defaults(func=cmd_gmail)
    gmail_search = gmail_sub.add_parser("search", help="Search messages")
    gmail_search.add_argument("query")
    gmail_search.add_argument("--max-results", dest="max_results", type=int, default=10)
    gmail_search.set_defaults(func=cmd_gmail)
    gmail_unread = gmail_sub.add_parser("unread_count", help="Count unread messages")
    gmail_unread.set_defaults(func=cmd_gmail)
    gmail_labels = gmail_sub.add_parser("labels", help="List labels")
    gmail_labels.set_defaults(func=cmd_gmail)

    # calendar
    calendar = subparsers.add_parser("calendar", help="Google Calendar integration")
    calendar_sub = calendar.add_subparsers(dest="subcommand", required=True)
    calendar_today = calendar_sub.add_parser("today", help="List today's events")
    calendar_today.set_defaults(func=cmd_calendar)
    calendar_list = calendar_sub.add_parser("list", help="List events")
    calendar_list.add_argument("--time-min")
    calendar_list.add_argument("--time-max")
    calendar_list.add_argument("--max-results", dest="max_results", type=int, default=10)
    calendar_list.set_defaults(func=cmd_calendar)
    calendar_create = calendar_sub.add_parser("create", help="Create event")
    calendar_create.add_argument("--summary", required=True)
    calendar_create.add_argument("--start", required=True)
    calendar_create.add_argument("--end", required=True)
    calendar_create.add_argument("--location")
    calendar_create.set_defaults(func=cmd_calendar)
    calendar_update = calendar_sub.add_parser("update", help="Update event")
    calendar_update.add_argument("event_id")
    calendar_update.add_argument("--summary", required=True)
    calendar_update.set_defaults(func=cmd_calendar)
    calendar_delete = calendar_sub.add_parser("delete", help="Delete event")
    calendar_delete.add_argument("event_id")
    calendar_delete.set_defaults(func=cmd_calendar)
    calendar_freebusy = calendar_sub.add_parser("freebusy", help="Check free/busy")
    calendar_freebusy.add_argument("time_min")
    calendar_freebusy.add_argument("time_max")
    calendar_freebusy.set_defaults(func=cmd_calendar)

    # todoist
    todoist = subparsers.add_parser("todoist", help="Todoist integration")
    todoist_sub = todoist.add_subparsers(dest="subcommand", required=True)
    todoist_list = todoist_sub.add_parser("list", help="List tasks")
    todoist_list.add_argument("--project-id")
    todoist_list.add_argument("--label")
    todoist_list.set_defaults(func=cmd_todoist)
    todoist_create = todoist_sub.add_parser("create", help="Create task")
    todoist_create.add_argument("--content", required=True)
    todoist_create.add_argument("--due")
    todoist_create.add_argument("--priority", type=int, default=1)
    todoist_create.set_defaults(func=cmd_todoist)
    todoist_complete = todoist_sub.add_parser("complete", help="Complete task")
    todoist_complete.add_argument("task_id")
    todoist_complete.set_defaults(func=cmd_todoist)
    todoist_projects = todoist_sub.add_parser("projects", help="List projects")
    todoist_projects.set_defaults(func=cmd_todoist)
    todoist_labels = todoist_sub.add_parser("labels", help="List labels")
    todoist_labels.set_defaults(func=cmd_todoist)

    # github
    github = subparsers.add_parser("github", help="GitHub integration")
    github_sub = github.add_subparsers(dest="subcommand", required=True)
    github_notifications = github_sub.add_parser("notifications", help="List notifications")
    github_notifications.set_defaults(func=cmd_github)
    github_issues = github_sub.add_parser("issues", help="List issues")
    github_issues.add_argument("repo")
    github_issues.add_argument("--state", default="open")
    github_issues.set_defaults(func=cmd_github)
    github_prs = github_sub.add_parser("prs", help="List pull requests")
    github_prs.add_argument("repo")
    github_prs.add_argument("--state", default="open")
    github_prs.set_defaults(func=cmd_github)
    github_search = github_sub.add_parser("search", help="Search issues and pull requests")
    github_search.add_argument("query")
    github_search.set_defaults(func=cmd_github)

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

    plugin_install = plugin_sub.add_parser("install", help="Install a plugin from marketplace")
    plugin_install.add_argument("name", help="Plugin name (from marketplace)")
    plugin_install.set_defaults(func=cmd_plugin)

    plugin_remove = plugin_sub.add_parser("remove", help="Remove an installed plugin")
    plugin_remove.add_argument("name", help="Plugin name")
    plugin_remove.set_defaults(func=cmd_plugin)

    plugin_update = plugin_sub.add_parser("update", help="Check or apply plugin updates")
    plugin_update.add_argument("name", nargs="?", default=None,
                               help="Plugin name (omit to list all updates)")
    plugin_update.set_defaults(func=cmd_plugin)

    plugin_search = plugin_sub.add_parser("search", help="Search plugins in marketplace")
    plugin_search.add_argument("query", help="Search query")
    plugin_search.add_argument("--field", choices=["name", "description", "tags", "all"],
                               default="all", help="Field to search in")
    plugin_search.set_defaults(func=cmd_plugin)

    plugin_setup = plugin_sub.add_parser("setup", help="Run OAuth setup for an integration")
    plugin_setup.add_argument("name", help="Integration name")
    plugin_setup.add_argument("--headless", action="store_true")
    plugin_setup.add_argument("--test", action="store_true")
    plugin_setup.set_defaults(func=cmd_plugin)

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
