# Phase 5b Unified Suggestion Pipeline Design

## Goal

Implement Phase 5b as a single suggestion system with two backend modes: `rules` and `llm`. `selfos suggest` keeps the current rules-based behavior by default. `selfos suggest --llm` runs the LLM pipeline and automatically falls back to rules-based suggestions when the configured LLM backend is unavailable or unusable.

## Scope

This design covers the full Phase 5b scope for the current repository:

- provider abstraction for `Ollama`, `OpenAI`, and `Anthropic`
- cost guard with daily cost accounting and semantic cache
- prompt loading and rendering
- unified `SuggestionEngine`
- CLI for `--llm`, `--provider`, `--approve`, `--rate`, `--stats`, `--clear-cache`
- local config for LLM provider settings
- prompt-safety and PII-redaction basics
- tests for providers, engine, fallback, CLI, and state handling

This design does not include Phase 5c source integrations. Gmail context is treated as optional data: if live OAuth/token setup is missing, the engine still works from activity and local context.

## Current-State Constraints

The current codebase already has:

- `ContextEngine` for activity-based summaries and proactive suggestions
- `smart_suggestions` plugin with simple rules-based output
- CLI routing through `UnifiedInterface`
- no `llm/` package
- no approval/rating/stats storage for suggestions

The main design constraint is to avoid splitting orchestration across the old plugin and a new LLM path. The code should converge on one engine while preserving backward compatibility for current CLI and plugin tests.

## Architecture

### Core Decision

Introduce `src/selfos/llm/suggestion_engine.py` as the only orchestration entry point for suggestions.

- `mode="rules"` returns normalized rules-based suggestions
- `mode="llm"` builds prompt context, calls the provider, validates output, records usage, and returns normalized suggestions
- `mode="llm"` falls back to `rules` automatically when the provider is unavailable, budget is exceeded, or the LLM output cannot be recovered after retry

### Package Structure

Add `src/selfos/llm/`:

- `models.py` — typed response models for suggestion flow
- `providers.py` — provider abstraction and concrete providers
- `cost_guard.py` — daily budget, semantic cache key, usage stats
- `prompts.py` — built-in prompt templates and local overrides
- `security.py` — PII redaction and prompt-sanitizer helpers
- `state.py` — local persistence for suggestions, ratings, cache, and stats
- `suggestion_engine.py` — orchestration and fallback logic

## Data Model

### Suggestion

Each suggestion is normalized into a structured record:

- `id`: stable local identifier
- `title`: short user-facing label
- `summary`: actionable detail
- `action`: symbolic action such as `email_reply`, `task_create`, `note`, `review_schedule`
- `confidence`: float in `[0, 0.95]`
- `backend_used`: `rules`, `llm`, or `rules_fallback`
- `source_context`: metadata describing whether Gmail/activity/context data were used
- `status`: `new`, `approved`, `dismissed`

### SuggestionResponse

- `backend_requested`
- `backend_used`
- `provider`
- `suggestions`
- `fallback_reason`
- `cached`
- `usage`

### Local State

Store Phase 5b state under `~/.selfos/llm/`:

- `suggestions.json` — issued suggestions and statuses
- `ratings.json` — user ratings by suggestion id
- `stats.json` — counters for requests, fallback, latency, approvals, ratings
- `cache.json` — semantic prompt-response cache

This is sufficient for current CLI requirements and KPI tracking without introducing a database.

## Providers

### Base Provider

`BaseLLMProvider` exposes:

- `complete(prompt, max_tokens, temperature)`
- `is_available()`
- `count_tokens(text)`

### Runtime Policy

- default runtime provider: `Ollama`
- `OpenAI` and `Anthropic` implemented with real request formatting
- cloud providers covered by mock tests, not required for local runtime in CI

### Availability Rules

- `OllamaProvider.is_available()` checks local HTTP endpoint
- `OpenAIProvider.is_available()` and `AnthropicProvider.is_available()` require configured API key
- if the requested provider is unavailable, the engine falls back to rules mode instead of failing the command

## Cost Guard

### Budget Model

Track estimated cost per request using a per-model price table. Daily guard is cost-based, not token-count-only.

### Cache Model

Use a semantic cache key derived from meaningful context features:

- count of unread emails included
- count of active tasks/events included
- selected template name
- provider/model
- hour bucket

The cache is used only for LLM mode and only for successful structured responses.

## Prompt System

Built-in prompt templates live in `src/selfos/llm/templates/`:

- `suggest_general.yaml`
- `suggest_email.yaml`
- `suggest_summary.yaml`

User overrides are loaded from `~/.selfos/prompts/` first, then built-ins.

Prompts render to a strict JSON-output instruction. User data is wrapped with explicit markers so the model sees it as external content, not system instructions.

## Security

### PII Redaction

For cloud providers, redact common PII before prompt construction:

- email addresses
- phone numbers
- URLs

Restoration is applied only to structured suggestion text after model output is accepted.

For `Ollama`, redaction remains enabled by default but can be disabled through config later without changing the engine interface.

### Prompt Sanitizer

Before accepting model output:

- scan context for suspicious phrases such as instruction-overrides
- cap confidence at `0.95`
- reject malformed or non-JSON responses after bounded retry

## SuggestionEngine Flow

1. Load runtime config.
2. Build context from `ContextEngine`.
3. Optionally enrich with Gmail data if available.
4. If mode is `rules`, return normalized rules-based suggestions.
5. If mode is `llm`:
   - sanitize/redact context
   - render prompt
   - check provider availability
   - check cost budget and cache
   - call provider
   - parse JSON
   - validate fields and clamp confidence
   - persist suggestions and usage
6. If any LLM-stage failure is non-recoverable, return rules-based fallback with `backend_used="rules_fallback"`.

## CLI Integration

Extend `selfos suggest`:

- `selfos suggest`
- `selfos suggest --llm`
- `selfos suggest --llm --provider ollama`
- `selfos suggest --approve <id>`
- `selfos suggest --rate <id> <1-5>`
- `selfos suggest --stats`
- `selfos suggest --clear-cache`

Add `selfos config llm`:

- show current LLM config
- set provider/model
- set API key for cloud providers
- record cloud opt-in

Approval updates suggestion state and attempts execution only when an action maps cleanly onto an existing delegated action. Otherwise it marks the suggestion approved for manual follow-up and reports that it is display-only.

## Integration with Existing Code

### smart_suggestions Plugin

Do not remove the plugin. Convert it into a thin adapter over `SuggestionEngine(mode="rules")`. This preserves existing plugin registry behavior while removing duplicate rules orchestration.

### DelegationEngine

Add a lightweight `evaluate_suggestion()` method that:

- maps LLM action names to delegation action types when possible
- returns `auto_execute`, `queue_for_approval`, or `display_only`

For this phase, approval execution remains conservative. Unknown or unmapped actions are never auto-executed.

## Error Handling

- provider unavailable -> rules fallback
- parse failure -> one retry with stricter JSON instruction, then rules fallback
- cost budget exceeded -> rules fallback
- missing cloud credentials -> rules fallback unless provider was explicitly forced and no fallback allowed in future phases
- corrupt local state -> rebuild empty state file and continue

## Testing Strategy

### Unit

- providers with mocked HTTP
- cost guard accounting and cache keys
- prompt loading and override precedence
- redaction and sanitizer helpers
- suggestion state persistence

### Integration

- `SuggestionEngine` rules mode
- `SuggestionEngine` llm mode with mocked provider
- fallback from unavailable `Ollama`
- fallback on invalid JSON
- approval/rating/stats updates

### CLI

- `selfos suggest --llm`
- `selfos suggest --llm` fallback behavior
- `selfos suggest --approve`
- `selfos suggest --rate`
- `selfos suggest --stats`
- `selfos suggest --clear-cache`
- `selfos config llm`

## Acceptance Criteria

Phase 5b is complete when:

- `selfos suggest` still works in rules mode
- `selfos suggest --llm` works with mocked provider responses
- `Ollama` unavailability automatically falls back to rules mode
- `OpenAI` and `Anthropic` providers are implemented and covered by mock tests
- approvals, ratings, cache, and stats are persisted locally
- full test suite passes with fresh verification
