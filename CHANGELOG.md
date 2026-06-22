# Changelog

All notable changes to Self OS are documented here.

---

## [0.6.0] — 2026-06-22 — Phase 5b: LLM-powered Suggestions

### Features
- Unified `SuggestionEngine` with `rules` and `llm` backends
- Ollama default runtime with automatic fallback to rules-based suggestions
- OpenAI and Anthropic provider adapters with mock-tested request handling
- Prompt templates, semantic cache, local suggestion state, ratings, and stats
- CLI: `selfos suggest --llm --provider ... --approve --rate --stats --clear-cache`
- CLI: `selfos config llm` for provider/model/api key configuration

### Security
- PII redaction before LLM calls
- Prompt sanitizer integrated in `SuggestionEngine`
- Explicit cloud opt-in for `openai` and `anthropic`

---

## [0.5.0] — 2026-06-22 — Phase 5a: OAuth2 Foundation + Gmail

### Features
- OAuth2 infrastructure with browser and device flows
- Profile-aware token storage and runtime paths
- Persistent integration rate limiter
- Gmail plugin with unread count, list, read, send, search, and labels
- CLI: `selfos gmail ...`, `selfos plugin setup gmail`, `selfos profile ...`

---

## [0.4.0] — 2026-06-22 — Phase 4: Platform

### Stage 5 — Stabilization & Documentation
- Architecture Contract updated to **v2.0** (Platform principles, Phase 4 components)
- Architecture Overview rewritten with full component table (27 modules)
- Developer guide (`docs/plugin-development.md`) with quick start, SDK, hooks, publishing
- **E2E test** (`test_phase4_e2e.py`) for full plugin lifecycle
- Version bumped to `0.4.0`

### Stage 4 — Platform Extension (Hooks + Community)
- `HookRegistry`: 12 hook points, `before/after/instead`, exception isolation
- CLI commands (note, task, suggest) trigger hooks
- `BaseSelfOSPlugin.on_register()` for automatic hook subscription
- Community plugin install via `install_plugin_from_url()` (git clone)
- Rating + downloads in `MarketplacePlugin`

### Stage 3 — Plugin Marketplace
- `PluginMarketplace` with search, semver comparison, YAML catalog
- `install_plugin_from_marketplace()` / `remove_plugin()` / `update_plugin()` / `check_for_updates()`
- `docs/plugin-marketplace.yaml` — local catalog with example plugins
- CLI: `selfos plugin install/remove/update/search`

### Stage 2 — Custom Delegation Rules
- `DelegationRule` dataclass (4 condition types: `always`, `never`, `trust_threshold`, `time_range`)
- `DelegationRuleSet` with YAML load/save/validate/match
- Decision order: Overrides → Custom Rules → Critical → Trust
- CLI: `selfos delegate rule add/list/remove/info`

### Stage 1 — Plugin Platform Core
- `PluginManifest` dataclass + YAML I/O + validation
- `PluginRegistry`: `install()` (dynamic import), `discover()`, `list_with_metadata()`
- `BaseSelfOSPlugin` — base class with `version`, `author`, `dependencies`, `protocol`
- `plugin_sdk`: `scaffold_plugin()`, `validate_plugin()`, `create_plugin()`
- CLI: `selfos plugin list/info/init/create`

### Bug Fixes (post-Stage 5 audit)
- **Flaky test resolved**: root cause was frozen module binding after `from X import y` — replaced with runtime-resolution wrapper + `importlib.invalidate_caches()`.
- Ruff clean (18 → 0 errors)
- Version synced across all config files
- `EnableAutoPlugin` rejects empty action
- `install_plugin_from_url` emits security warning
- `selfos.yaml` cleaned of corrupt `''` key
- CI workflows: fixed YAML syntax + GH expression quoting

---

## [0.3.0] — 2026-06-21 — Phase 3: Full Immersion

### Features
- Delegation Engine with trust system (`delegation_engine.py`)
- Unified plugin interface (`plugin_contracts.py`)
- Web interface (stub, served by `web/`)
- Context Engine for history-aware suggestions (`context_engine.py`)
- Activity tracking (file-based log in `data/activity/`)
- Browser plugin with search history
- Email plugin with SendGrid delegation
- Diagnostics command (`selfos diagnostics`)
- 10 built-in plugins (calendar, todoist, quick_note, categorize, etc.)

### Infrastructure
- pyproject.toml with dev/test/lint dependencies
- CI: ruff, mypy strict, pytest, architecture validation
- `selfos.yaml` configuration with force_review, trust thresholds, delegation defaults
- Architecture contract v1.0
- Verification harness (`tests/`, `scripts/validate_architecture.py`)

### Bug Fixes (across audit rounds)
- CLI error propagation fixed
- Dead code removed, dead imports cleaned
- ruff/mypy/flake8 to 0 errors
- uuid4 for IDs, proper logging
- Plugin execute signatures unified
- Test coverage for 10 built-in plugins

---

## [0.2.0] — 2026-06-20 — Phase 2: Architecture

- Project flattening: removed `selfos-data/` nesting
- Script-to-plugin migration: `quick_note`, `categorize`
- Delegation rules engine (early version)
- Unified interface for plugins
- Architecture documentation

---

## [0.1.0] — 2026-06-19 — Phase 1: Foundation

- Initial project structure
- Activity log, daily summary, and categorization
- Photo processing pipeline
- GitHub import scripts
- Dashboard generation
- Weekly report generation
- Basic delegation (enable/disable auto mode)

---

## [0.0.1] — Pre-history

- `493e02c` — Initial project brief
- `871600f` — Strategy document
- `ca2ce16` — GitHub delegation update
- Community workflows: import-external, import-logs, process-photos, update-dashboard, weekly-report
