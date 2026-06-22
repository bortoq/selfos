# Phase 5b Unified Suggestion Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a unified suggestion pipeline with rules and LLM backends, local stateful approval/rating/stats, and CLI integration with automatic rules fallback when LLM is unavailable.

**Architecture:** A new `SuggestionEngine` in `src/selfos/llm/` becomes the only orchestration layer for suggestions. Existing rules-based behavior is preserved by routing the `smart_suggestions` plugin and CLI through the engine in `rules` mode, while `llm` mode adds providers, prompt rendering, cost guarding, parsing, persistence, and fallback.

**Tech Stack:** Python 3.10+, `httpx`, `pytest`, `pyyaml`

---

### Task 1: Add failing tests for the new suggestion engine and state model

**Files:**
- Create: `tests/test_llm_suggestion_engine.py`
- Create: `tests/test_llm_state.py`
- Test: `tests/test_smart_suggestions.py`

- [ ] **Step 1: Write the failing test**

```python
def test_llm_engine_falls_back_to_rules_when_provider_unavailable():
    response = engine.get_suggestions(mode="llm")
    assert response["backend_used"] == "rules_fallback"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_llm_suggestion_engine.py tests/test_llm_state.py -q`
Expected: FAIL because `selfos.llm` package and engine do not exist

- [ ] **Step 3: Write minimal implementation**

```python
class SuggestionEngine:
    def get_suggestions(self, mode: str = "rules") -> dict[str, Any]:
        return {"backend_used": "rules", "suggestions": []}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_llm_suggestion_engine.py tests/test_llm_state.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_llm_suggestion_engine.py tests/test_llm_state.py src/selfos/llm
git commit -m "feat: add llm suggestion engine scaffold"
```

### Task 2: Implement provider abstraction, prompt loading, and security helpers

**Files:**
- Create: `src/selfos/llm/models.py`
- Create: `src/selfos/llm/providers.py`
- Create: `src/selfos/llm/prompts.py`
- Create: `src/selfos/llm/security.py`
- Create: `src/selfos/llm/templates/suggest_general.yaml`
- Create: `src/selfos/llm/templates/suggest_email.yaml`
- Create: `src/selfos/llm/templates/suggest_summary.yaml`
- Create: `tests/test_llm_providers.py`
- Create: `tests/test_llm_prompts.py`
- Create: `tests/test_llm_security.py`

- [ ] **Step 1: Write the failing test**

```python
def test_ollama_provider_reports_unavailable_on_http_error():
    provider = OllamaProvider(...)
    assert provider.is_available() is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_llm_providers.py tests/test_llm_prompts.py tests/test_llm_security.py -q`
Expected: FAIL because providers, prompts, and security helpers are missing

- [ ] **Step 3: Write minimal implementation**

```python
class OllamaProvider(BaseLLMProvider):
    def is_available(self) -> bool:
        try:
            self._http.get(f"{self.base_url}/api/tags")
            return True
        except httpx.HTTPError:
            return False
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_llm_providers.py tests/test_llm_prompts.py tests/test_llm_security.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/selfos/llm/models.py src/selfos/llm/providers.py src/selfos/llm/prompts.py src/selfos/llm/security.py src/selfos/llm/templates tests/test_llm_providers.py tests/test_llm_prompts.py tests/test_llm_security.py
git commit -m "feat: add llm providers prompts and security helpers"
```

### Task 3: Implement cost guard and local suggestion state

**Files:**
- Create: `src/selfos/llm/cost_guard.py`
- Create: `src/selfos/llm/state.py`
- Modify: `src/selfos/config.py`
- Create: `tests/test_llm_cost_guard.py`
- Create: `tests/test_llm_state.py`

- [ ] **Step 1: Write the failing test**

```python
def test_cost_guard_blocks_when_daily_budget_exceeded():
    guard.record_usage(...)
    assert guard.can_spend(...) is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_llm_cost_guard.py tests/test_llm_state.py -q`
Expected: FAIL because cost guard and state persistence are missing

- [ ] **Step 3: Write minimal implementation**

```python
class CostGuard:
    def can_spend(self, estimated_cost: float) -> bool:
        return self._spent_today() + estimated_cost <= self.max_cost_usd_per_day
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_llm_cost_guard.py tests/test_llm_state.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/selfos/config.py src/selfos/llm/cost_guard.py src/selfos/llm/state.py tests/test_llm_cost_guard.py tests/test_llm_state.py
git commit -m "feat: add llm cost guard and local state"
```

### Task 4: Integrate SuggestionEngine with rules and LLM flows

**Files:**
- Create: `src/selfos/llm/suggestion_engine.py`
- Modify: `plugins/smart_suggestions_plugin.py`
- Modify: `src/selfos/context_engine.py`
- Modify: `src/selfos/delegation_engine.py`
- Create: `tests/test_llm_suggestion_engine.py`

- [ ] **Step 1: Write the failing test**

```python
def test_rules_engine_returns_normalized_suggestions():
    response = engine.get_suggestions(mode="rules")
    assert response["suggestions"][0]["backend_used"] == "rules"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_llm_suggestion_engine.py tests/test_smart_suggestions.py -q`
Expected: FAIL because the engine is not yet wired to rules and plugin paths

- [ ] **Step 3: Write minimal implementation**

```python
class SuggestionEngine:
    def _rules_suggestions(self) -> SuggestionResponse:
        ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_llm_suggestion_engine.py tests/test_smart_suggestions.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/selfos/llm/suggestion_engine.py plugins/smart_suggestions_plugin.py src/selfos/context_engine.py src/selfos/delegation_engine.py tests/test_llm_suggestion_engine.py tests/test_smart_suggestions.py
git commit -m "feat: unify rules and llm suggestion pipeline"
```

### Task 5: Extend CLI for LLM suggest, approval, rating, stats, cache, and config

**Files:**
- Modify: `src/selfos/cli.py`
- Modify: `src/selfos/unified_interface.py`
- Create: `tests/test_cli_suggest_llm.py`

- [ ] **Step 1: Write the failing test**

```python
def test_cli_suggest_llm_falls_back_to_rules(capsys):
    main(["suggest", "--llm"])
    assert "fallback" in capsys.readouterr().out.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_cli_suggest_llm.py -q`
Expected: FAIL because CLI flags and config command do not exist

- [ ] **Step 3: Write minimal implementation**

```python
suggest.add_argument("--llm", action="store_true")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_cli_suggest_llm.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/selfos/cli.py src/selfos/unified_interface.py tests/test_cli_suggest_llm.py
git commit -m "feat: add llm suggestion cli controls"
```

### Task 6: Run full verification and regression suite

**Files:**
- Modify: `pyproject.toml`
- Test: `tests/test_cli_smoke.py`
- Test: `tests/test_smart_suggestions.py`

- [ ] **Step 1: Write the failing test**

```python
def test_smart_suggestions_plugin_remains_backward_compatible():
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest -q`
Expected: FAIL if compatibility, typing, or CLI regressions remain

- [ ] **Step 3: Write minimal implementation**

```python
dependencies = [
    "httpx>=0.27",
    "pyyaml>=6.0",
]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `ruff check src tests && mypy src && pytest -q`
Expected: all commands succeed

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml
git commit -m "test: verify phase 5b unified suggestion pipeline"
```
