# Phase 5c Integrations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the locally verifiable Phase 5c slice: Calendar, Todoist, and GitHub integrations with CLI access, hook coverage, and expanded LLM suggestion context.

**Architecture:** Add small HTTP-backed integration modules under `src/selfos/plugins/`, keep compatibility shims for legacy plugin registry imports, and extend `SuggestionEngine` with best-effort multi-source context collection. Tests stay deterministic through `httpx.MockTransport` and monkeypatched CLI factories.

**Tech Stack:** Python, `httpx`, pytest, existing OAuth/token foundation, existing CLI and hook registry

---

### Task 1: Add failing tests for integration runtime modules

**Files:**
- Create: `tests/test_calendar_integration.py`
- Create: `tests/test_todoist_integration.py`
- Create: `tests/test_github_integration.py`

- [ ] Write failing tests for list/create/update/delete behaviors using fake HTTP responses.
- [ ] Run targeted tests and verify they fail because the runtime modules do not exist yet.
- [ ] Implement minimal runtime modules.
- [ ] Re-run targeted tests until green.

### Task 2: Add failing CLI tests

**Files:**
- Create: `tests/test_cli_calendar.py`
- Create: `tests/test_cli_todoist.py`
- Create: `tests/test_cli_github.py`
- Modify: `src/selfos/cli.py`

- [ ] Write failing CLI tests around `calendar`, `todoist`, and `github` commands using monkeypatched constructor helpers.
- [ ] Run targeted tests and verify the parser/commands fail before implementation.
- [ ] Add minimal command handlers and parser wiring.
- [ ] Re-run targeted tests until green.

### Task 3: Extend hooks and compatibility adapters

**Files:**
- Modify: `src/selfos/hooks.py`
- Modify: `plugins/calendar_plugin.py`
- Modify: `plugins/todoist_plugin.py`

- [ ] Add failing hook tests if needed for new hook points.
- [ ] Implement new hook constants and point registration support.
- [ ] Convert legacy root-level plugins into adapters over the new runtime modules.
- [ ] Re-run hook and legacy plugin tests.

### Task 4: Expand SuggestionEngine context

**Files:**
- Modify: `src/selfos/llm/suggestion_engine.py`
- Modify: `tests/test_llm_suggestion_engine.py`

- [ ] Write failing tests proving calendar/tasks/github data appears in the built context and degraded integrations do not break LLM flow.
- [ ] Implement constructor-injected integration providers and best-effort context aggregation.
- [ ] Re-run targeted tests until green.

### Task 5: Update docs and version state

**Files:**
- Modify: `pyproject.toml`
- Modify: `src/selfos/__init__.py`
- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Modify: `docs/current-state.md`
- Modify: `docs/architecture-overview.md`
- Modify: `docs/roadmap.md`

- [ ] Update version references to `0.7.0`.
- [ ] Mark `Phase 5c` complete in docs.
- [ ] Document new commands and multi-source suggestion context.

### Task 6: Verify end to end

**Files:**
- Verify only

- [ ] Run targeted integration and CLI tests.
- [ ] Run `ruff check src tests`.
- [ ] Run `mypy src`.
- [ ] Run `pytest -q`.
- [ ] Leave `selfos.yaml` untouched.
