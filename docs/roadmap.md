# Self OS Roadmap

**Последнее обновление:** 2026-06-22 (v3 — повторный аудит, 7.9 → 8.5/10)  
**Текущая версия:** 0.7.0 (Phase 5c: Calendar + Todoist + GitHub — завершена)  
**Оценка v2:** 7.9/10 → целевая **8.5/10**

---

## Что изменено во v3 roadmap (относительно v2)

| Пункт аудита v2 | Что сделано |
|---|---|
| Action mapping семантически некорректен | `task_create: None`, `schedule: None` — нет автоматизации, только display/approve |
| `trust × confidence` наивная формула | AND-gate с двумя порогами + пометка «confidence не калибрована» |
| Capability permissions без enforcement | Явно: declaration-only, AST-check при install, enforcement в Phase 8 |
| Google Cloud automation переоценена | Manual setup (5-10 мин), testing mode 7-day limitation, без gcloud CLI |
| VCR secret leakage | filter_headers + pre-commit Bearer token scan |
| Phase 7 concrete tech table | Убрана, заменена на «RFC при старте Phase 7» |
| Migration / CI не описаны | Конкретные примеры миграции + CI changes раздел |

## Что было закрыто в v2 roadmap (относительно v1)

| Пункт аудита v1 | Что сделано |
|---|---|
| Security & Privacy — критические пробелы | Добавлен раздел Security (PII redaction, keyring, prompt injection, sandboxing) |
| LLM ↔ DelegationEngine — нет связи | Добавлен раздел Integration: action mapping, confidence as trust modifier, hybrid flow |
| Sequencing Phase 5→6 спорный | **Пересобрано:** Phase 5a (OAuth+Gmail) → 5b (LLM) → 5c (остальные интеграции) |
| CostGuard слабо технически | tiktoken/price-table/semantic hash + TTL вместо len/4 |
| OAuth2 — клиентский сценарий не описан | Device flow, local HTTP callback, Google app verification, multi-account profiles |
| Метрики успеха не определены | Добавлены KPI для каждой фазы |
| VCR не упомянут | pytest-recording + VCR fixtures для integration tests |
| Production Hardening отсутствует | Отдельная фаза между фичами и 1.0 |
| Сроки оптимистичны ×2-3 | Все оценки удвоены с explicit buffer |
| Слишком много кода | Кодовые скелеты сокращены до интерфейсов |

---

## Общая временная шкала

```
2026-06-22 ─── Phase 4 завершена (0.4.0) ✅
    │
    ├── Phase 5a: OAuth2 Foundation + Gmail          [20 дней, v0.5.0] ✅
    │   └── Ранний риск-discovery по OAuth + первая реальная польза
    │
    ├── Phase 5b: LLM-powered Suggestions            [25 дней, v0.6.0] ✅
    │   └── Unified suggestion pipeline + Ollama default runtime
    │
    ├── Phase 5c: Calendar + Todoist + GitHub         [25 дней, v0.7.0] ✅
    │   └── LLM подсказывает по всем источникам
    │
    ├── Phase 6: Production Hardening                 [20 дней, v0.8.0]
    │   └── Logging, security audit, migration, telemetry, i18n
    │
    └── Phase 7: Web UI                               [10-14 недель, v1.0.0]
```

**Общая длительность (один разработчик):** 5-7 месяцев до 1.0  
**Множитель buffer:** ×2 от naive estimate (уже заложен в цифры выше)

### Почему именно такой порядок (5a → 5b → 5c)

| Порядок | Аргументы за | Аргументы против |
|---|---|---|
| **5a (Gmail) первой** | Самая полезная интеграция; OAuth infrastructure для всех; ранний риск-discovery | LLM не работает — нет данных для анализа |
| **5b (LLM) после 5a** | LLM получает реальные письма (а не моки); prompt-шаблоны калибруются на реальных данных | LLM видит только Gmail + Activity Log — нет Calendar/Tasks |
| **5c (Calendar/Todoist/GitHub) после 5b** | LLM-инфраструктура готова до добавления новых источников | LLM-промпты Phase 5b нужно расширить для новых sources (±1-2 дня) |

**Альтернатива** (рассмотрена и отклонена): 5a → 5c → 5b (LLM последней).
- Почему отклонена: без LLM, интеграции 5c — просто API wrappers. LLM даёт **смысл** интеграциям.
- Компромисс: Phase 5c.4 «Hooks + LLM Integration» расширяет prompt-шаблоны Phase 5b для новых sources.

---

## Security & Privacy — архитектурные решения

> **Принято до execution.** Эти решения обязательны для Phase 5a.

### S1. PII Redaction

Все данные, отправляемые в LLM (cloud или local), проходят через PII-фильтр **до** формирования промпта.

```python
class PIIRedactor:
    """Маскировка PII перед отправкой в LLM."""
    
    PATTERNS = {
        "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        "phone": r'\b\d{10,13}\b',
        "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
        "ip": r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
    }
    
    def redact(self, text: str) -> tuple[str, dict[str, str]]:
        """
        Заменяет PII на placeholder'ы.
        Возвращает (redacted_text, mapping) где mapping = {placeholder: original}.
        """
        ...
    
    def restore(self, text: str, mapping: dict[str, str]) -> str:
        """Восстанавливает оригинальные данные из LLM-ответа."""
        ...
```

**Принцип:** LLM видит `[EMAIL_1]`, `[PHONE_1]`. Видит структуру, но не сами данные. `restore()` применяется к финальным suggestion'ам.

**Default:** Включено для cloud-провайдеров. Отключаемо для Ollama (local) через конфиг.

### S2. Local-first по умолчанию

```yaml
llm:
  provider: ollama          # По умолчанию — local
  cloud_opt_in: false        # Должен явно включить
```

При первом запуске `selfos suggest --llm`:
1. Проверяется Ollama (localhost:11434).
2. Если недоступен — сообщение: «LLM requires Ollama (local) или cloud provider. Run `selfos config llm --cloud` для настройки.»
3. Cloud-провайдеры требуют **явного opt-in**:
   ```
   selfos config llm --provider openai --api-key $OPENAI_API_KEY --cloud-opt-in
   Warning: This sends your data to OpenAI. Your data will be PII-redacted,
   but email subjects, event titles, and task names will be visible.
   Proceed? [y/N]
   ```

### S3. OAuth Token Encryption

```python
class SecureTokenStore:
    """
    Хранение OAuth-токенов через OS keyring.
    
    Fallback: если keyring недоступен (headless, CI) — 
    encrypted JSON с ключом из переменной окружения.
    """
    
    def __init__(self):
        try:
            import keyring
            self._backend = "keyring"
        except ImportError:
            self._backend = "encrypted_file"
    
    def save(self, provider: str, token: OAuthToken) -> None:
        if self._backend == "keyring":
            keyring.set_password("selfos", provider, json.dumps(token.to_dict()))
        else:
            # Encrypted JSON fallback
            ...
```

**Требования:**
- `keyring` как optional dependency (`[security]` extra)
- macOS: Keychain, Linux: Secret Service (gnome-keyring/kwallet), Windows: Credential Manager
- Headless fallback: `~/.selfos/tokens.enc` + `SELFOS_TOKEN_KEY` env var

### S4. Prompt Injection Mitigation

```python
class PromptSanitizer:
    """Защита от prompt injection в пользовательских данных."""
    
    # Обёртка пользовательских данных — LLM видит их как "внешний контент"
    WRAPPER_OPEN = "<USER_DATA_START>"
    WRAPPER_CLOSE = "<USER_DATA_END>"
    
    # Инструкции в user data — подозрительные паттерны
    SUSPICIOUS_PATTERNS = [
        r'(?i)ignore\s+(previous|all)\s+instructions',
        r'(?i)you\s+are\s+now',
        r'(?i)\[SYSTEM\s+OVERRIDE\]',
        r'(?i)new\s+instructions:',
    ]
    
    def sanitize(self, text: str) -> str:
        """Обернуть пользовательские данные + обнаружить injection."""
        ...
    
    def is_injection_attempt(self, text: str) -> bool:
        """Проверить наличие подозрительных паттернов."""
        ...
```

**Правила:**
- Промпт-шаблон разделяет «системные инструкции» и «данные пользователя» через `<USER_DATA>` теги
- LLM-ответ парсится через JSON schema validation + confidence cap 0.95 для данных из user context
- При обнаружении injection — логирование + warning пользователю

### S5. Plugin Permissions — Declaration Only (Enforcement в Phase 8)

Community-плагины (установленные через `install_plugin_from_url`) **объявляют** нужные capabilities в `plugin.yaml`:

```yaml
# plugin.yaml — community plugin
name: my-plugin
permissions:
  - notes:read        # Может читать заметки
  - notes:write       # Может писать заметки
  # НЕ может: email:read, calendar:read, tokens:read
```

> **Важно: сейчас permissions — это только декларация.** Нет runtime enforcement.
> Плагин с `import os; os.path.expanduser("~/.selfos/tokens")` обходит ограничение.
>
> **Enforcement (subprocess isolation + IPC) запланирован в Phase 8.**
> До Phase 8 действует policy-based контроль:
> - Community-плагины **всегда** запрашивают `selfos install --trust <plugin>` с явным подтверждением
> - Плагины **не** могут импортировать `selfos.token_store` или `selfos.integrations.token_store` (AST-проверка при install)
> - Рекомендация: «устанавливайте плагины только от доверенных авторов»

---

## LLM ↔ DelegationEngine Integration

> **Архитектурное решение, принятое до execution Phase 5b.**

### Проблема

Сейчас `DelegationEngine` работает с `action_type` (строка: `email_send`, `event_categorization`, `quick_note`).  
LLM возвращает `Suggestion.action` (строка: `email_reply`, `task_create`, `note`).  
Эти два мира **не связаны**.

### Решение: Action Mapping

LLM-действия маппятся на action_type в trust system. **Точная совместимость** — не все LLM-действия имеют аналог.

```python
# Маппинг LLM actions → DelegationEngine action_types
# None = нет прямого аналога → "display_only" (LLM не может auto-execute)
LLM_TO_DELEGATION_MAP: dict[str, str | None] = {
    # ─── Email ───
    "email_reply": "email_send",        # есть trust: email_send
    "email_draft": "email_send",        # draft → тот же trust, что и отправка
    
    # ─── Notes ───
    "note": "quick_note",               # есть trust: quick_note
    
    # ─── No direct equivalent — display only ───
    "task_create": None,                # quick_note ≠ task (разные side effects)
    "schedule": None,                   # event_categorization ≠ event creation
    "categorize": "event_categorization",  # категоризация существующего — ок
    "tag_suggest": None,                # нет action_type для тегов
    "summarize": "daily_summary",       # есть trust: daily_summary
}

# Новые action_type для будущего расширения (Phase 5c+):
# "task_create", "event_create", "email_draft" (отдельно от email_send)
```

**Принцип:** если маппинг = `None`, LLM suggestion показывается пользователю, но **никогда** не auto-execute. Пользователь может approve через `selfos suggest --approve <id>`.

### Confidence → Trust: AND-gate (не произведение)

```python
def evaluate_suggestion(self, suggestion: Suggestion) -> str:
    """
    Решение для LLM-suggestion'а.
    
    Два независимых порога:
      - trust >= TRUST_THRESHOLD   (из delegation engine)
      - confidence >= CONFIDENCE_MIN (от LLM)
    
    Оба должны быть выше порогов → AND-gate.
    
    ⚠️ Confidence НЕ калибрована. LLM выдаёт 0.95 для всего.
       Используется как пользовательский фильтр, не как вероятность.
    """
    delegation_type = LLM_TO_DELEGATION_MAP.get(suggestion.action)
    if delegation_type is None:
        # Неизвестное действие — только показать
        return "display_only"
    
    trust = self.delegation_engine.get_trust(delegation_type)
    confidence = suggestion.confidence
    
    # AND-gate: оба должны пройти
    trust_ok = trust >= TRUST_THRESHOLD
    confidence_ok = confidence >= CONFIDENCE_MIN  # e.g., 0.7
    
    if trust_ok and confidence_ok:
        if trust >= CRITICAL_THRESHOLD:
            return "auto_execute"
        return "queue_for_approval"
    
    # Даже если один высокий — показать пользователю
    return "display_only"
```

### Hybrid Flow (Draft → Approve → Execute)

```
LLM generates suggestion
        ↓
PIIRedactor.sanitize() + PromptInjection check
        ↓
SuggestionEngine.get_suggestions()
        ↓
DelegationEngine.evaluate_suggestion(suggestion)
        ↓
    ┌─── auto_execute (high confidence + high trust)
    ├─── queue_for_approval (medium)
    └─── display_only (low)
```

Для `queue_for_approval`: CLI показывает `selfos suggest --approve <id>` → пользователь подтверждает → DelegationEngine выполняет.

---

## Phase 5a — OAuth2 Foundation + Gmail

**Статус:** Завершено (v0.5.0)  
**Цель:** Реальная интеграция с Gmail. OAuth2 infrastructure для всех будущих интеграций.  
**Время:** 20 дней (10 naive × 2 buffer)  
**Версия:** 0.5.0

### Зачем первой

1. Gmail — самая полезная интеграция для личной почты
2. OAuth2 infrastructure переиспользуется в Phase 5c (Calendar, Todoist, GitHub)
3. Ранний риск-discovery: если OAuth не работает на нужных платформах — узнаём сейчас, а не через 3 месяца

### KPI

| Метрика | Цель |
|---|---|
| `selfos gmail unread_count` | Возвращает реальное количество непрочитанных |
| `selfos gmail list --unread` | Показывает до 10 писем с subject/sender/date |
| OAuth flow | Работает в обычном терминале (browser) И headless (device flow) |
| Тесты | 221+ существующих зелёные + ≥15 новых |

### Этапы

#### 5a.1 — OAuth2 Infrastructure (8 дней)

**Модули:**
- `src/selfos/integrations/oauth_manager.py` — единый менеджер OAuth2
- `src/selfos/integrations/token_store.py` — хранение токенов (keyring + fallback)
- `src/selfos/integrations/rate_limiter.py` — persistent rate limiting

**Решения:**
- **OAuth flow:** Browser-based (`http://localhost:8080/callback`) с fallback на **device flow** для headless сред
- **Token storage:** `keyring` (macOS/Linux/Windows) → encrypted JSON fallback
- **Google App:** Каждый пользователь создаёт **свой Google Cloud Project** вручную (5-10 минут). Инструкция: `docs/setup-google-cloud.md`. Без verification — **testing mode** (refresh tokens живут 7 дней, re-auth раз в неделю). Verification занимает 4-6 недель Google review — **не планируется автоматизировать**.
- **Multi-account:** `~/.selfos/profiles/{name}/tokens/` — профили для personal/work
- **Rate limiter:** Persistent state в `~/.selfos/rate_limits.json`, leaky bucket + Retry-After header

**CLI:**
```
selfos plugin setup gmail              # Browser OAuth flow
selfos plugin setup gmail --headless   # Device flow (SSH, CI)
selfos plugin setup gmail --test       # Тест соединения
selfos profile create work             # Создать профиль
selfos profile switch work             # Переключить профиль
```

#### 5a.2 — Gmail Plugin (7 дней)

**Модуль:** `src/selfos/plugins/gmail_plugin.py`

**Действия:**
- `list` — список писем (query, max_results, unread_only)
- `read` — содержимое письма (message_id)
- `send` — отправка (to, subject, body через `$EDITOR` или `--body`)
- `search` — поиск (Gmail search syntax)
- `unread_count` — количество непрочитанных
- `labels` — список меток

**Хуки:** `email:received`, `email:sent` (для Phase 5b)

**CLI:**
```
selfos gmail list                     # Последние 10 писем
selfos gmail list --unread            # Только непрочитанные
selfos gmail read <message_id>
selfos gmail send --to user@example.com --subject "Hello" --body "Text"
selfos gmail send --to user@example.com --subject "Hello"  # откроет $EDITOR
selfos gmail search "from:boss is:unread"
selfos gmail unread_count
```

#### 5a.3 — Tests (5 дней)

**Стратегия:** `pytest-recording` (VCR) для HTTP-моков.

```
tests/
├── test_oauth_manager.py          # Unit: mock HTTP, token exchange/refresh
├── test_token_store.py            # Unit: mock keyring, encrypted fallback
├── test_rate_limiter.py           # Unit: persistent state, backoff
├── test_gmail_plugin_vcr.py       # VCR: recorded Gmail API responses
├── test_gmail_e2e.py              # E2E: OAuth → Gmail → suggestions
└── cassettes/                     # VCR fixtures (recorded HTTP exchanges)
    ├── test_gmail_list.yaml
    ├── test_gmail_send.yaml
    └── test_oauth_exchange.yaml
```

**VCR approach:**
1. Один раз записать реальный HTTP-обмен: `pytest --vcr-record=all`
2. В CI: `pytest --vcr-record=none` (только replay)
3. При изменении API: перезаписать cassette

---

## Phase 5b — LLM-powered Suggestions

**Статус:** Завершено (v0.6.0)  
**Цель:** Интеллектуальные предложения на основе реальных данных Gmail + ContextEngine.  
**Время:** 25 дней (14 naive × ~1.8 buffer)  
**Версия:** 0.6.0

### KPI

| Метрика | Цель |
|---|---|
| Latency P95 | < 3 секунды (с Ollama), < 5 секунд (cloud) |
| Accuracy | ≥ 60% suggestions approved via `selfos suggest --approve` (auto-tracked) |
| Cost | < $0.50/день (cloud, при 50000 токенов/день) |
| Prompt injection | 0 successful bypasses в security tests |

### Этапы

#### 5b.1 — Provider Abstraction (5 дней)

**Модуль:** `src/selfos/llm/providers.py`

**Интерфейс:**
```python
class BaseLLMProvider(ABC):
    name: str
    model: str
    
    @abstractmethod
    def complete(self, prompt: str, *, max_tokens: int = 1000,
                 temperature: float = 0.7) -> LLMResponse: ...
    
    @abstractmethod
    def is_available(self) -> bool: ...
    
    @abstractmethod
    def count_tokens(self, text: str) -> int: ...
```

**Провайдеры:** OpenAI (gpt-4o-mini), Anthropic (Claude Sonnet), Ollama (llama3.2, mistral)

**Для OpenAI:** `tiktoken` для точного подсчёта токенов. Для Anthropic: `anthropic-tokenizer`. Для Ollama: token count из response.

**Обработка ошибок:** retry с exponential backoff, context length exceeded → truncate, JSON parse failure → retry с stricter prompt.

#### 5b.2 — Cost Guard (5 дней)

**Модуль:** `src/selfos/llm/cost_guard.py`

**Ключевые изменения (vs v1 roadmap):**

| Было (v1) | Стало (v2) |
|---|---|
| `len(text) // 4` | `tiktoken` / `anthropic-tokenizer` / response token count |
| `max_tokens_per_day: 50000` | `max_cost_usd_per_day: 1.0` + per-model price table |
| SHA-256 hash контекста | Semantic hash (без timestamps) + TTL-кеш (hour buckets) |

**Price table:**
```python
MODEL_PRICES = {
    "gpt-4o":        {"input": 5.0,   "output": 15.0},   # $/1M tokens
    "gpt-4o-mini":   {"input": 0.15,  "output": 0.60},
    "claude-sonnet":  {"input": 3.0,   "output": 15.0},
    "claude-haiku":   {"input": 0.25,  "output": 1.25},
    "llama3.2":       {"input": 0.0,   "output": 0.0},    # local
}
```

**Smart caching:**
```python
def _semantic_key(self, context: dict, template: str) -> str:
    """Хеш без timestamps и порядка ключей."""
    significant = {
        "emails_count": len(context.get("unread_emails", [])),
        "tasks_count": len(context.get("active_tasks", [])),
        "events_count": len(context.get("upcoming_events", [])),
        "hour_bucket": int(time.time()) // 3600,  # ±1 hour granularity
    }
    return hashlib.sha256(
        json.dumps(significant, sort_keys=True).encode()
    ).hexdigest()[:16]
```

#### 5b.3 — Prompt System (4 дней)

**Модуль:** `src/selfos/llm/prompts.py`

**Шаблоны** (уменьшено с v1: 3 вместо 5):

| Шаблон | Назначение |
|---|---|
| `suggest_general.yaml` | Общий анализ контекста |
| `suggest_email.yaml` | Приоритизация и ответы на письма |
| `suggest_summary.yaml` | Дневной саммари |

Пользовательские шаблоны: `~/.selfos/prompts/` с приоритетом над встроенными.

**Prompt injection mitigation** (из раздела Security):
- `<USER_DATA_START>` / `<USER_DATA_END>` обёртки
- `PromptSanitizer` для проверки suspicious patterns
- Confidence cap 0.95 для suggestions из user data

#### 5b.4 — SuggestionEngine (5 дней)

**Модуль:** `src/selfos/llm/suggestion_engine.py`

**Оркестрация:**
```
ContextEngine.get_summary()
    → PIIRedactor.redact() (для cloud)
    → PromptRenderer.render()
    → LLM.complete()
    → PIIRedactor.restore() (для cloud)
    → JSON parse + schema validation
    → PromptInjection check
    → DelegationEngine.evaluate_suggestion() (из раздела Integration)
    → Cache + usage logging
    → return SuggestionResponse
```

**Интеграция с hooks:** `suggest:before` (modify context), `suggest:after` (filter results)

#### 5b.5 — CLI + Rating (2 дня)

```
selfos suggest                  # Rules-based (без LLM)
selfos suggest --llm            # LLM-powered
selfos suggest --llm --provider ollama  # Явный выбор провайдера
selfos suggest --approve <id>   # Подтвердить suggestion для execution
selfos suggest --rate <id> <1-5># Оценить полезность (для KPI)
selfos suggest --stats          # Статистика: cost, accuracy, latency
selfos suggest --clear-cache    # Очистить кеш
selfos config llm               # Настройка провайдера
```

#### 5b.6 — Tests (4 дня)

- Unit: providers (mock HTTP), cost_guard, prompts
- Integration: suggestion engine (mock LLM responses)
- Security: prompt injection attempts (10+ сценариев)
- E2E: ContextEngine → LLM → suggestions → approval flow

---

## Phase 5c — Calendar + Todoist + GitHub

**Статус:** Завершено (v0.7.0)  
**Цель:** Остальные интеграции. LLM suggestions теперь работают со всеми источниками.  
**Время:** 25 дней (17 naive × ~1.5 buffer)  
**Версия:** 0.7.0

### KPI

| Метрика | Цель |
|---|---|
| `selfos calendar today` | Показывает реальные события на сегодня |
| `selfos todoist list` | Показывает реальные задачи |
| `selfos github notifications` | Показывает реальные уведомления |
| LLM suggestions | Учитывают email + calendar + tasks одновременно |

### Этапы

#### 5c.1 — Google Calendar (7 дней)

- `list` (time_min/max), `today`, `create`, `update`, `delete`, `freebusy`
- OAuth: тот же Google Cloud Project, дополнительный scope `calendar.events`
- VCR fixtures для Calendar API

#### 5c.2 — Todoist (5 дней)

- `list` (project/label filter), `create` (content, due, priority), `complete`, `projects`, `labels`
- Auth: Todoist API token (без OAuth, простой API key)
- Обновление существующего `todoist_plugin.py` (заглушка → реальный API)

#### 5c.3 — GitHub (5 дней)

- `notifications`, `issues` (repo, state), `prs` (repo, state), `search`
- Auth: GitHub Personal Access Token + OAuth (для полного доступа)
- Device flow для CLI (GitHub supports `urn:ietf:wg:oauth:2.0:oob`)

#### 5c.4 — Hooks + LLM Integration (3 дня)

Новые hook-точки:
- `email:received`, `email:sent`
- `calendar:event_created`, `calendar:event_updated`
- `task:created`, `task:completed`
- `github:notification`, `github:issue`

LLM suggestions теперь учитывают все источники одновременно.

#### 5c.5 — Tests (5 дней)

VCR fixtures для каждой интеграции. E2E: OAuth → API → Plugin → LLM → suggestions.

---

## Phase 6 — Production Hardening

**Статус:** Планирование (после Phase 5c)  
**Цель:** Сделать продукт готовым для незнакомого пользователя.  
**Время:** 20 дней (10 naive × 2 buffer)  
**Версия:** 0.8.0

### Этапы

#### 6.1 — Logging Strategy (4 дня)

- Structured JSON logs (`structlog`)
- Levels: DEBUG (dev), INFO (prod), WARNING (LLM cost), ERROR (failures)
- Rotation: daily, max 7 days
- Location: `~/.selfos/logs/`
- LLM audit log: что именно ушло в LLM (PII-safe)

#### 6.2 — Migration & Deprecation (4 дня)

- Plugin manifest versioning: `min_selfos_version` field
- Migration scripts: `selfos migrate --from 0.7 --to 0.8`
- Deprecation policy: API N deprecated в N+1, removed в N+2
- Breaking change policy: documented in CHANGELOG.md

**Конкретные примеры миграции:**

| Версия | Что меняется | Миграция |
|---|---|---|
| v0.5.0 (Phase 5a) | `~/.selfos/tokens/` → `~/.selfos/profiles/default/tokens/` | Авто: при первом запуске создать `profiles/default/` и переместить токены |
| v0.7.0 (Phase 5c) | `rules.yaml` добавлены новые condition types | Авто: новые поля с default values, старый формат валиден |
| v0.8.0 (Phase 6) | Структура логов `~/.selfos/logs/` | Авто: создать директорию, старые логи не трогать |

**Формат `selfos.yaml` — stable:** изменения только через deprecated warnings в N, removal в N+1.
**Persistent state (~/.selfos/data/):** JSON-формат, всегда backwards-compatible. Breaking changes — только через migration script.

#### 6.3 — Telemetry & Error Tracking (4 дня)

**Реальность:** «Sentry-like» требует central infrastructure. Self OS — self-hosted проект.

**Решения:**
- **Opt-in only** — по умолчанию выключено (`selfos config --telemetry off`)
- **Backend:** Self-hosted Sentry (Docker compose) ИЛИ отправка в `https://telemetry.selfos.dev` (если foundation существует)
- **Данные:** error type, stack trace (без local paths — sanitize `/Users/john/...` → `/Users/.../`), OS, Python version
- **Never:** PII, tokens, email content, plugin data
- **Retention:** 30 дней, auto-delete
- **Privacy policy:** обязательна, если есть central endpoint (GDPR compliance)
- **Headless:** если нет central endpoint — локальный JSON-лог ошибок в `~/.selfos/errors/`

**Минимальная реализация (Phase 6):** локальный error log + opt-in structured error reporting.

#### 6.4 — i18n Foundation (4 дня)

- Message catalog (`src/selfos/i18n/messages.yaml`)
- CLI: `selfos config --lang en|ru`
- Default: English
- Russian as first translation target

#### 6.5 — Security Audit (4 дня)

- Third-party review (или self-audit по checklist OWASP)
- Pen-test: prompt injection, token theft, plugin sandboxing
- Documentation: `docs/security.md`

---

## Phase 7 — Web UI

**Статус:** Планирование (после Phase 6)  
**Цель:** Веб-интерфейс для не-технических пользователей.  
**Время:** 14 недель (7 naive weeks × 2 buffer). Определение — после Phase 6, когда будет ясен scope.
**Версия:** 1.0.0

### Архитектурные решения

> **Не приняты до execution.** Технологический стек будет определён при старте Phase 7 на основе опыта Phase 5-6.
> RFC-документ: `docs/rfc/phase7-web-ui.md` (будет создан по завершении Phase 6).

### KPI

| Метрика | Цель |
|---|---|
| Dashboard load | < 2 секунды |
| Suggestions | Отображаются в real-time через SSE |
| Mobile | Responsive (не native) |
| Setup time | < 5 минут от clone до running |

### Замечание по 1.0

**1.0 = Phase 6 (Production Hardening) завершена.** Web UI — это **bonus** для 1.0, но не requirement. Логика: после Phase 6 продукт уже usable через CLI. Web UI — это accessibility layer, не core feature.

---

## Тестовая стратегия

### Unit Tests (все фазы)

Существующие 212 тестов + новые для каждого модуля. ruff + mypy чистые.

### Integration Tests (Phase 5a+)

**VCR (pytest-recording)** для HTTP-моков:

```bash
# Запись cassette (только локально, с реальными API keys)
pytest tests/ --vcr-record=all

# Replay в CI ( без API keys)
pytest tests/ --vcr-record=none
```

**Cassettes** хранятся в `tests/cassettes/` и коммитятся в git.

**Секретная санитизация (обязательна до записи первой cassette):**

```toml
# pyproject.toml
[tool.vcr]
record_mode = "none"  # в CI
filter_headers = ["authorization", "cookie", "x-api-key"]
# Тело ответа: фильтрация email-адресов и PII через custom hook
```

- Запись cassette **только локально** с реальными API keys (никогда в CI)
- Pre-commit hook: `grep -rE 'Bearer [A-Za-z0-9._-]{20,}' tests/cassettes/` — блокирует коммит с токенами
- При обнаружении secrets в diff → автоматический `git reset` + warning

### Security Tests (Phase 5b+)

- Prompt injection: 10+ сценариев (system override, instruction leaking, JSON injection)
- PII redaction: email, phone, SSN detection + restore accuracy
- Token encryption: keyring availability, fallback behavior

### E2E Tests (все фазы)

Полные сценарии:
1. OAuth → Gmail → unread_count → LLM suggestion → approval → email sent
2. OAuth → Calendar → create event → LLM schedule optimization
3. Plugin install from URL → sandboxing verification

---

## CI/CD Changes для Phase 5+

Текущий CI: ruff + mypy + pytest. После Phase 5a нужны дополнительные этапы:

| Этап | Когда | Что делает |
|---|---|---|
| **VCR replay** | Phase 5a+ | `pytest --vcr-record=none` — replay against cassettes (без API keys) |
| **Secret scan** | Phase 5a+ | Pre-commit + CI: `grep -rE 'Bearer \|token\|api_key' tests/cassettes/` |
| **Security tests** | Phase 5b+ | Prompt injection, PII redaction — отдельный stage, может быть медленным |
| **Cross-platform** | Phase 5a+ | keyring backend: macOS (Keychain), Linux (Secret Service), headless fallback |
| **LLM tests** | Phase 5b+ | Требуют API keys → только в nightly builds, не в каждом PR |

**Nightly builds** (добавить в `.github/workflows/ci.yml`):
- Запись VCR cassettes против реальных API (раз в неделю)
- Security scan (prompt injection test suite)
- Cost tracking (сколько токенов за день в nightly)

---

## Dependencies

### Phase 5a

| Пакет | Зачем | Тип |
|---|---|---|
| `httpx` | HTTP для OAuth + Gmail API | runtime |
| `keyring` | Secure token storage | optional `[security]` |
| `google-api-python-client` | Gmail API | runtime |
| `google-auth-oauthlib` | OAuth2 flow | runtime |
| `pytest-recording` | VCR tests | dev |

### Phase 5b

| Пакет | Зачем | Тип |
|---|---|---|
| `tiktoken` | Точный подсчёт токенов (OpenAI) | optional |
| `anthropic` | Anthropic SDK (опционально) | optional |
| `ollama` | Ollama SDK (опционально) | optional |

### Phase 5c

| Пакет | Зачем | Тип |
|---|---|---|
| `google-api-python-client` | Calendar API (тот же что Gmail) | runtime |
| `PyGithub` (опционально) | GitHub SDK | optional |

### Phase 7

| Пакет | Зачем | Тип |
|---|---|---|
| `fastapi` | Web backend | runtime |
| `uvicorn` | ASGI server | runtime |
| `jinja2` | Templates | runtime |
| `python-jose` | JWT auth | runtime |
