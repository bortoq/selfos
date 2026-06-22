# Phase 5c Integrations Design

## Scope

This design covers the full locally verifiable slice of `Phase 5c` for the current repository:

- Google Calendar runtime plugin + CLI
- Todoist runtime plugin + CLI
- GitHub runtime plugin + CLI
- new hook points for created/updated integration actions
- `SuggestionEngine` context expansion across email, calendar, tasks, and GitHub notifications
- deterministic HTTP-backed tests without requiring live credentials in CI

Live authentication and live API recording are explicitly out of scope for execution in this environment. The design keeps runtime code ready for real credentials while tests stay stable with fake HTTP transports and mock dependencies.

## Current Constraints

- Gmail OAuth/token infrastructure already exists in `src/selfos/integrations/`.
- `plugins/calendar_plugin.py` and `plugins/todoist_plugin.py` are still mock stubs.
- There is no GitHub integration module yet.
- `SuggestionEngine` currently builds context only from `ContextEngine` plus placeholder lists.
- Existing CI is intentionally simple and should not depend on external network or secret material.

## Recommended Approach

Use one small HTTP-backed plugin per integration and wire CLI commands directly to those plugins. Reuse the existing OAuth foundation only where it already fits naturally:

- Calendar uses the existing Google OAuth manager
- Todoist uses an API token from environment or config
- GitHub uses a Personal Access Token from environment or config

This keeps the implementation aligned with the roadmap but avoids overextending Phase 5c into a second auth refactor.

## Architecture

### Runtime modules

- `src/selfos/plugins/calendar_integration.py`
  - Google Calendar REST wrapper
  - list/today/create/update/delete/freebusy
- `src/selfos/plugins/todoist_integration.py`
  - Todoist REST wrapper
  - list/create/complete/projects/labels
- `src/selfos/plugins/github_integration.py`
  - GitHub REST wrapper
  - notifications/issues/prs/search

The legacy root-level `plugins/calendar_plugin.py` and `plugins/todoist_plugin.py` remain as compatibility adapters so existing plugin registry tests keep working while runtime logic moves under `src/selfos/plugins/`.

### CLI integration

Add top-level commands:

- `selfos calendar list|today|create|update|delete|freebusy`
- `selfos todoist list|create|complete|projects|labels`
- `selfos github notifications|issues|prs|search`

The CLI should use fakeable constructor helpers, mirroring the existing Gmail pattern.

### Hooks

Add hook points for integration-side state changes:

- `calendar:event_created`
- `calendar:event_updated`
- `task:created`
- `task:completed`
- `github:notification`
- `github:issue`

These are intentionally narrow. Read-only operations such as `calendar today` or `github prs` do not need dedicated hooks in this phase.

### SuggestionEngine context expansion

`SuggestionEngine._build_context()` should enrich the LLM payload with:

- `unread_emails` from Gmail when available
- `upcoming_events` from Calendar
- `active_tasks` from Todoist
- `github_notifications` and `github_pull_requests` from GitHub

If any integration is unavailable or not configured, the engine should degrade to empty lists for that source instead of failing the whole suggestion request.

## Data Contracts

Calendar event shape:

```python
{
    "id": str,
    "summary": str,
    "start": str,
    "end": str,
    "location": str,
    "status": str,
}
```

Todoist task shape:

```python
{
    "id": str,
    "content": str,
    "project_id": str | None,
    "priority": int,
    "due": str | None,
    "labels": list[str],
}
```

GitHub notification / issue / PR shape:

```python
{
    "id": str,
    "title": str,
    "repository": str,
    "url": str,
    "state": str,
    "type": str,
}
```

The CLI prints human-readable summaries; `SuggestionEngine` uses these normalized dictionaries directly.

## Error Handling

- Missing credentials should raise explicit `ValueError` messages from constructor helpers.
- HTTP 4xx/5xx should raise concise `ValueError` exceptions with service name and status.
- `SuggestionEngine` must swallow integration fetch failures and continue with remaining sources.
- Hooks must keep current isolation behavior: hook exceptions never break the core command path.

## Testing Strategy

Use deterministic tests as the primary coverage mechanism:

- unit tests for each integration module with `httpx.MockTransport`
- CLI tests with monkeypatched constructor helpers
- `SuggestionEngine` tests with fake integration providers and degraded-source scenarios
- keep VCR-style coverage as optional smoke testing only, not as the only test protecting behavior

This addresses the flakiness problem already observed with localhost-based VCR replay.

## Out of Scope

- mandatory live OAuth flows in CI
- GitHub OAuth/device-flow completion
- persistent background sync or webhook ingestion
- automatic execution of suggestions from new integrations

## Acceptance Criteria

- Calendar, Todoist, and GitHub commands work through real runtime modules
- `SuggestionEngine` includes all supported source buckets in context
- new integration failures do not break `selfos suggest --llm`
- tests are deterministic and pass without network access
- docs/version state moves to `0.7.0 / Phase 5c complete`
