# Phase 5a No-Live-Auth Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the local, testable slice of Phase 5a: profile-aware OAuth/token infrastructure, persistent rate limiting, Gmail CLI/plugin behavior, and regression fixes that let the suite run in sandboxed environments without live Google authentication.

**Architecture:** Keep Google-specific HTTP behavior behind a small Gmail client/plugin layer that depends on the existing OAuth manager and token store. Fix path resolution first so `SELFOS_HOME` and profile directories are reliable at runtime and in tests. Add CLI entry points for `plugin setup gmail`, `profile`, and `gmail` commands with fakeable dependencies.

**Tech Stack:** Python 3.10+, `httpx`, `pytest`

---

### Task 1: Fix runtime path resolution and sandbox-safe test defaults

**Files:**
- Modify: `src/selfos/config.py`
- Modify: `src/selfos/activity.py`
- Modify: `src/selfos/trust.py`
- Create: `tests/conftest.py`
- Test: `tests/test_scheduler.py`
- Test: `tests/test_email_service.py`

- [ ] **Step 1: Write the failing test**

```python
def test_default_selfos_home_isolated(tmp_path, monkeypatch):
    monkeypatch.delenv("SELFOS_HOME", raising=False)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_scheduler.py tests/test_email_service.py -q`
Expected: FAIL with write attempts under `/home/user/.selfos/...`

- [ ] **Step 3: Write minimal implementation**

```python
def _get_home() -> Path:
    env_home = os.getenv("SELFOS_HOME")
    if env_home:
        return Path(env_home)
    return Path.cwd() / ".selfos"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_scheduler.py tests/test_email_service.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/conftest.py src/selfos/config.py src/selfos/activity.py src/selfos/trust.py
git commit -m "fix: isolate selfos runtime paths in tests"
```

### Task 2: Add profile-aware config helpers and token/rate-limit storage

**Files:**
- Modify: `src/selfos/config.py`
- Create: `src/selfos/integrations/rate_limiter.py`
- Modify: `src/selfos/integrations/token_store.py`
- Test: `tests/test_token_store.py`
- Test: `tests/test_rate_limiter.py`

- [ ] **Step 1: Write the failing test**

```python
def test_profile_dir_uses_current_profile(tmp_path, monkeypatch):
    monkeypatch.setenv("SELFOS_HOME", str(tmp_path))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_token_store.py tests/test_rate_limiter.py -q`
Expected: FAIL because `profile_dir()` and `RateLimiter` are missing or incomplete

- [ ] **Step 3: Write minimal implementation**

```python
def profile_dir(profile: str | None = None) -> Path:
    selected = profile or current_profile()
    return _get_home() / "profiles" / selected
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_token_store.py tests/test_rate_limiter.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/selfos/config.py src/selfos/integrations/token_store.py src/selfos/integrations/rate_limiter.py tests/test_token_store.py tests/test_rate_limiter.py
git commit -m "feat: add profile-aware token and rate-limit storage"
```

### Task 3: Add Gmail client/plugin and CLI entry points without live auth

**Files:**
- Create: `src/selfos/plugins/__init__.py`
- Create: `src/selfos/plugins/gmail_plugin.py`
- Modify: `src/selfos/cli.py`
- Modify: `src/selfos/unified_interface.py`
- Test: `tests/test_gmail_plugin.py`
- Test: `tests/test_cli_gmail.py`

- [ ] **Step 1: Write the failing test**

```python
def test_gmail_unread_count_uses_query_filter():
    plugin = GmailPlugin(...)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_gmail_plugin.py tests/test_cli_gmail.py -q`
Expected: FAIL because Gmail plugin and CLI commands do not exist

- [ ] **Step 3: Write minimal implementation**

```python
class GmailPlugin:
    def unread_count(self) -> int:
        return self.list_count(query="is:unread")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_gmail_plugin.py tests/test_cli_gmail.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/selfos/plugins/__init__.py src/selfos/plugins/gmail_plugin.py src/selfos/cli.py src/selfos/unified_interface.py tests/test_gmail_plugin.py tests/test_cli_gmail.py
git commit -m "feat: add gmail cli and plugin"
```

### Task 4: Verify phase slice and regressions together

**Files:**
- Modify: `pyproject.toml`
- Test: `tests/test_cli_smoke.py`
- Test: `tests/test_delegation_engine.py`

- [ ] **Step 1: Write the failing test**

```python
def test_plugin_setup_gmail_headless(monkeypatch):
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest -q`
Expected: FAIL if integration wiring or dependency declarations are incomplete

- [ ] **Step 3: Write minimal implementation**

```python
dependencies = [
    "pyyaml>=6.0",
    "httpx>=0.27",
]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml
git commit -m "test: verify phase 5a no-live-auth slice"
```
