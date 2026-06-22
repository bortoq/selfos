# Self OS Roadmap

**Последнее обновление:** 2026-06-22  
**Текущая версия:** 0.4.0 (Phase 4: Platform — завершена)

---

## Phase 5 — LLM-powered Suggestions

**Статус:** Планирование  
**Цель:** Превратить заглушку `SmartSuggestionsPlugin` в интеллектуального ассистента, понимающего контекст пользователя на естественном языке.  
**Время:** 2–3 недели  
**Версия:** 0.5.0

### Архитектурная цель

```
ContextEngine → Context Summary → Provider Abstraction → LLM → Structured Suggestions → User
                                         ↑
                                  Prompt Templates (YAML)
                                         ↑
                                  Cost Guard (tokens/cache)
```

Ключевой принцип: **LLM предлагает, пользователь решает.** Delegation engine может автоматизировать только те действия, которые уже имеют `trust_threshold`.

### Структура файлов

```
src/selfos/
├── llm/
│   ├── __init__.py
│   ├── providers.py          # BaseLLMProvider, OpenAIProvider, AnthropicProvider, OllamaProvider
│   ├── suggestion_engine.py  # SuggestionEngine — основной оркестратор
│   ├── prompts.py            # PromptRenderer — загрузка и рендеринг YAML-шаблонов
│   ├── cost_guard.py         # TokenCounter, DailyLimit, CacheManager
│   └── schemas.py            # Suggestion, SuggestionRequest, SuggestionResponse
├── prompts/
│   ├── suggest_general.yaml   # Общий промпт для suggestions
│   ├── suggest_priority.yaml  # Приоритизация задач
│   ├── suggest_email.yaml     # Анализ писем
│   ├── suggest_schedule.yaml  # Оптимизация расписания
│   └── suggest_summary.yaml   # Дневной саммари
└── ... (существующие модули)

tests/
├── test_llm_providers.py
├── test_suggestion_engine.py
├── test_prompts.py
├── test_cost_guard.py
└── test_llm_e2e.py

docs/
├── llm-configuration.md      # Руководство по настройке LLM-провайдеров
└── prompt-customization.md   # Как создавать свои промпт-шаблоны
```

### Этапы реализации

#### Stage 1 — Provider Abstraction (3 дня)

**Цель:** Базовый интерфейс для работы с любым LLM-провайдером.

**Модуль `providers.py`:**

```python
@dataclass
class LLMResponse:
    content: str
    tokens_used: int
    model: str
    latency_ms: float

class BaseLLMProvider(ABC):
    """Абстрактный базовый класс для LLM-провайдеров."""
    
    name: str
    model: str
    
    @abstractmethod
    def complete(self, prompt: str, *, max_tokens: int = 1000,
                 temperature: float = 0.7) -> LLMResponse:
        """Отправить промпт и получить ответ."""
        ...
    
    @abstractmethod
    def is_available(self) -> bool:
        """Проверить доступность провайдера."""
        ...
    
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Подсчитать количество токенов."""
        ...

class OpenAIProvider(BaseLLMProvider):
    """Провайдер для OpenAI API (GPT-4o, GPT-4o-mini)."""
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model
    
    def complete(self, prompt, *, max_tokens=1000, temperature=0.7):
        import httpx
        response = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
            timeout=30.0,
        )
        data = response.json()
        return LLMResponse(
            content=data["choices"][0]["message"]["content"],
            tokens_used=data["usage"]["total_tokens"],
            model=self.model,
            latency_ms=response.elapsed.total_seconds() * 1000,
        )
    
    def is_available(self):
        return bool(self.api_key)
    
    def count_tokens(self, text):
        # Приближённый подсчёт: ~4 символа на токен
        return len(text) // 4

class AnthropicProvider(BaseLLMProvider):
    """Провайдер для Anthropic API (Claude)."""
    # Аналогичная реализация через httpx

class OllamaProvider(BaseLLMProvider):
    """Провайдер для локальной модели через Ollama."""
    def __init__(self, model: str = "llama3.2", base_url: str = "http://localhost:11434"):
        ...
```

**Модуль `schemas.py`:**

```python
@dataclass
class Suggestion:
    """Единичное предложение для пользователя."""
    title: str                     # Краткое описание
    description: str               # Детали
    action: str                    # Тип действия (email_reply, task_create, note, schedule)
    confidence: float              # 0.0–1.0
    reasoning: str                 # Обоснование (почему это предложение)
    priority: str                  # high / medium / low
    metadata: dict[str, Any]       # Произвольные данные для плагина

@dataclass
class SuggestionRequest:
    """Запрос на генерацию предложений."""
    context: dict[str, Any]        # Контекст из ContextEngine
    prompt_template: str           # Имя шаблона
    max_suggestions: int = 5
    user_preferences: dict[str, Any] | None = None

@dataclass
class SuggestionResponse:
    """Ответ от LLM-движка."""
    suggestions: list[Suggestion]
    tokens_used: int
    model: str
    latency_ms: float
    cached: bool = False
```

**Конфигурация `selfos.yaml`:**

```yaml
llm:
  provider: openai          # openai | anthropic | ollama
  model: gpt-4o-mini
  api_key: ${OPENAI_API_KEY}  # Из переменной окружения
  max_tokens_per_day: 50000
  temperature: 0.7
  cache_ttl_hours: 4
```

**Тесты:** `test_llm_providers.py` — мок-тесты с `unittest.mock.patch` для HTTP-запросов.

---

#### Stage 2 — Prompt System (2 дня)

**Цель:** YAML-шаблоны промптов с версионированием и пользовательской настройкой.

**Модуль `prompts.py`:**

```python
@dataclass
class PromptTemplate:
    """Шаблон промпта с переменными."""
    name: str
    template: str                  # Jinja2-подобный шаблон
    version: str
    description: str
    max_context_tokens: int        # Макс. токенов для контекста

class PromptRenderer:
    """Загрузчик и рендерер промпт-шаблонов."""
    
    def __init__(self, prompts_dir: Path | None = None):
        self.prompts_dir = prompts_dir or Path("prompts")
        self._cache: dict[str, PromptTemplate] = {}
    
    def load(self, name: str) -> PromptTemplate:
        """Загрузить шаблон из YAML-файла."""
        ...
    
    def render(self, name: str, context: dict[str, Any]) -> str:
        """Отрендерить шаблон с подстановкой переменных."""
        template = self.load(name)
        # Подстановка переменных из контекста
        ...
    
    def list_available(self) -> list[str]:
        """Список доступных шаблонов."""
        ...
```

**Пример шаблона `prompts/suggest_general.yaml`:**

```yaml
name: suggest_general
version: "1.0"
description: "Общий промпт для генерации предложений"
max_context_tokens: 3000

template: |
  Ты — ассистент Self OS, персональная операционная система пользователя.
  
  Проанализируй контекст пользователя и предложи до {max_suggestions} действий,
  которые стоит выполнить прямо сейчас.
  
  ## Контекст
  {context_summary}
  
  ## История действий
  {recent_actions}
  
  ## Непрочитанные письма
  {unread_emails}
  
  ## Ближайшие события
  {upcoming_events}
  
  ## Текущие задачи
  {active_tasks}
  
  ## Правила
  - Предлагай только те действия, которые реально можно выполнить
  - Учитывай приоритеты: важные контакты > дедлайны > удобное время
  - Каждое предложение должно содержать: title, action, confidence, reasoning
  - Отвечай строго в JSON-формате
  
  Формат ответа:
  [
    {
      "title": "...",
      "description": "...",
      "action": "email_reply|task_create|note|schedule|categorize",
      "confidence": 0.0-1.0,
      "reasoning": "...",
      "priority": "high|medium|low"
    }
  ]
```

**Пользовательские шаблоны:**

Пользователь может переопределять шаблоны в `~/.selfos/prompts/`. Приоритет: пользовательские > встроенные.

---

#### Stage 3 — SuggestionEngine (3 дня)

**Цель:** Оркестратор, связывающий ContextEngine + LLM + Hooks.

**Модуль `suggestion_engine.py`:**

```python
class SuggestionEngine:
    """
    Основной движок генерации предложений.
    
    Архитектура:
      ContextEngine → Context Summary → PromptRenderer → LLM → Parse → Validate → Suggestions
    
    Hook-точки:
      - suggest:before  (модифицировать контекст)
      - suggest:after   (фильтровать/модифицировать результат)
    """
    
    def __init__(
        self,
        provider: BaseLLMProvider,
        prompt_renderer: PromptRenderer,
        cost_guard: CostGuard,
        context_engine: ContextEngine | None = None,
    ):
        self.provider = provider
        self.prompts = prompt_renderer
        self.cost_guard = cost_guard
        self.context_engine = context_engine or ContextEngine()
    
    def get_suggestions(
        self,
        request: SuggestionRequest,
    ) -> SuggestionResponse:
        """
        Основной метод: получить предложения на основе контекста.
        
        1. Собрать контекст из ContextEngine
        2. Проверить кеш (hash контекста)
        3. Проверить дневной лимит токенов
        4. Отрендерить промпт
        5. Отправить в LLM
        6. Распарсить ответ
        7. Валидировать предложения
        8. Сохранить в кеш
        9. Вернуть результат
        """
        # 1. Контекст
        context = self.context_engine.get_summary()
        
        # 2. Кеш
        cache_key = self._hash_context(context, request.prompt_template)
        cached = self.cost_guard.get_cached(cache_key)
        if cached:
            return SuggestionResponse(
                suggestions=cached,
                tokens_used=0,
                model=self.provider.model,
                latency_ms=0,
                cached=True,
            )
        
        # 3. Лимит
        if not self.cost_guard.can_afford(request.max_suggestions * 200):
            return SuggestionResponse(
                suggestions=[],
                tokens_used=0,
                model=self.provider.model,
                latency_ms=0,
            )
        
        # 4–5. Рендер + LLM
        prompt = self.prompts.render(request.prompt_template, {
            "context_summary": context.get("summary", ""),
            "recent_actions": context.get("recent_actions", ""),
            "unread_emails": context.get("unread_emails", ""),
            "upcoming_events": context.get("upcoming_events", ""),
            "active_tasks": context.get("active_tasks", ""),
            "max_suggestions": request.max_suggestions,
        })
        
        response = self.provider.complete(prompt, max_tokens=1500)
        
        # 6–7. Парсинг + валидация
        suggestions = self._parse_suggestions(response.content)
        suggestions = self._validate(suggestions, request.max_suggestions)
        
        # 8. Кеш
        self.cost_guard.store_cache(cache_key, suggestions)
        self.cost_guard.record_usage(response.tokens_used)
        
        return SuggestionResponse(
            suggestions=suggestions,
            tokens_used=response.tokens_used,
            model=response.model,
            latency_ms=response.latency_ms,
        )
    
    def _parse_suggestions(self, raw: str) -> list[Suggestion]:
        """Парсинг JSON-ответа от LLM в список Suggestion."""
        import json
        # Извлечение JSON из ответа (LLM может добавить markdown-обёртку)
        ...
    
    def _validate(self, suggestions: list[Suggestion], 
                  max_count: int) -> list[Suggestion]:
        """Валидация: типы actions, confidence > 0.3, не более max_count."""
        valid_actions = {"email_reply", "task_create", "note", "schedule", 
                        "categorize", "tag_suggest", "summarize"}
        return [
            s for s in suggestions[:max_count]
            if s.action in valid_actions and s.confidence >= 0.3
        ]
```

**Интеграция с hooks.py:**

```python
# В hook_registry — существующая точка suggest:get расширяется:
hook_registry.trigger_before("suggest:get", context=context)

# После LLM:
hook_registry.trigger_after("suggest:get", suggestions=suggestions)
```

**Интеграция с CLI:**

```
selfos suggest                  # Обычные suggestions (rules-based)
selfos suggest --llm            # LLM-powered suggestions
selfos suggest --llm --watch    # Периодические предложения (каждые 30 мин)
selfos suggest --clear-cache    # Очистить кеш LLM
```

---

#### Stage 4 — Cost Guard (2 дня)

**Цель:** Управление расходами на LLM API.

**Модуль `cost_guard.py`:**

```python
class CostGuard:
    """
    Контроль расходов на LLM.
    
    Функции:
    - Дневной лимит токенов
    - Кеширование результатов (hash контекста → suggestions)
    - Логирование использования
    - Предупреждение при приближении к лимиту
    """
    
    def __init__(self, config: dict[str, Any]):
        self.max_tokens_per_day = config.get("max_tokens_per_day", 50000)
        self.cache_ttl_hours = config.get("cache_ttl_hours", 4)
        self.usage_file = config.get("usage_file", "~/.selfos/llm_usage.json")
        self.cache_dir = config.get("cache_dir", "~/.selfos/llm_cache/")
    
    def can_afford(self, estimated_tokens: int) -> bool:
        """Проверить, хватит ли токенов на сегодня."""
        used = self._get_today_usage()
        return (used + estimated_tokens) <= self.max_tokens_per_day
    
    def record_usage(self, tokens: int) -> None:
        """Записать использование токенов."""
        ...
    
    def get_cached(self, cache_key: str) -> list[Suggestion] | None:
        """Получить закешированный результат."""
        ...
    
    def store_cache(self, cache_key: str, suggestions: list[Suggestion]) -> None:
        """Сохранить результат в кеш."""
        ...
    
    def _hash_context(self, context: dict, template: str) -> str:
        """Хеш контекста для кеширования."""
        import hashlib
        content = json.dumps(context, sort_keys=True) + template
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def get_usage_stats(self) -> dict[str, Any]:
        """Статистика использования за сегодня."""
        ...
```

**Конфигурация:**

```yaml
llm:
  max_tokens_per_day: 50000
  cache_ttl_hours: 4
  cost_alert_threshold: 0.8   # Предупреждать при 80% лимита
```

---

#### Stage 5 — CLI Integration + Docs (1 день)

**Добавления в `cli.py`:**

```
selfos suggest                  # Обычные suggestions (rules-based, без LLM)
selfos suggest --llm            # LLM-powered suggestions
selfos suggest --llm --watch    # Периодические предложения
selfos suggest --clear-cache    # Очистить кеш
selfos suggest --stats          # Статистика использования LLM
selfos config llm               # Показать/изменить LLM-конфигурацию
```

**Документация:**

- `docs/llm-configuration.md` — настройка провайдеров, API keys, env vars
- `docs/prompt-customization.md` — создание своих промпт-шаблонов

---

#### Stage 6 — Tests + E2E (3 дня)

| Тест | Что проверяет |
|---|---|
| `test_llm_providers.py` | Mock HTTP, проверка `LLMResponse`, retry logic |
| `test_suggestion_engine.py` | Оркестрация: контекст → промпт → LLM → suggestions |
| `test_prompts.py` | Загрузка YAML, рендеринг шаблонов, fallback |
| `test_cost_guard.py` | Дневной лимит, кеш, логирование |
| `test_llm_e2e.py` | Полный цикл: ContextEngine → SuggestionEngine → CLI |

---

### Итого Phase 5

| Этап | Дни | Модули |
|---|---|---|
| Provider Abstraction | 3 | `providers.py`, `schemas.py` |
| Prompt System | 2 | `prompts.py`, `prompts/*.yaml` |
| SuggestionEngine | 3 | `suggestion_engine.py` |
| Cost Guard | 2 | `cost_guard.py` |
| CLI + Docs | 1 | `cli.py`, docs |
| Tests | 3 | `tests/test_llm_*.py` |
| **Итого** | **14 дней** | |

---

## Phase 6 — Real API Integrations

**Статус:** Планирование (после Phase 5)  
**Цель:** Заменить заглушки на реальные API: Gmail, Google Calendar, Todoist, GitHub.  
**Время:** 3–4 недели  
**Версия:** 0.6.0

### Архитектурная цель

```
External API ←→ OAuth2 Manager ←→ Plugin ←→ Delegation Engine ←→ User
                    ↑
              Token Store (~/.selfos/tokens/)
                    ↑
              Rate Limiter
```

Ключевой принцип: **Каждая интеграция — отдельный плагин с единым контрактом.** OAuth2, rate limiting, error handling — в общем ядре, не в плагинах.

### Структура файлов

```
src/selfos/
├── integrations/
│   ├── __init__.py
│   ├── oauth_manager.py        # Единый менеджер OAuth2 токенов
│   ├── token_store.py          # Хранение токенов (~/.selfos/tokens/)
│   ├── rate_limiter.py         # Rate limiting для всех API
│   └── base_integration.py     # Базовый класс для интеграций
├── plugins/
│   ├── gmail_plugin.py         # Gmail: чтение, поиск, отправка
│   ├── google_calendar_plugin.py  # Google Calendar: события, напоминания
│   ├── todoist_plugin.py       # Todoist: задачи, проекты, метки
│   └── github_plugin.py        # GitHub: issues, PR, уведомления
└── ...

tests/
├── test_oauth_manager.py
├── test_token_store.py
├── test_rate_limiter.py
├── test_gmail_plugin.py
├── test_google_calendar_plugin.py
├── test_todoist_plugin.py
├── test_github_plugin.py
└── test_integrations_e2e.py

docs/
├── integrations-setup.md       # Настройка каждой интеграции
├── oauth-configuration.md      # OAuth2 flow, API keys
└── api-reference.md            # Справочник по всем интеграциям
```

### Этапы реализации

#### Stage 1 — OAuth2 Infrastructure (4 дня)

**Цель:** Единая система управления OAuth2 токенами для всех провайдеров.

**Модуль `oauth_manager.py`:**

```python
@dataclass
class OAuthCredentials:
    """OAuth2 credentials для одного провайдера."""
    provider: str                # google | todoist | github
    client_id: str
    client_secret: str
    redirect_uri: str = "http://localhost:8080/callback"
    
    # Scopes
    scopes: list[str] = field(default_factory=list)

class OAuthManager:
    """
    Единый менеджер OAuth2 для всех интеграций.
    
    Поддерживает:
    - Authorization Code flow (Google, GitHub)
    - Device flow (GitHub CLI)
    - Token refresh
    - Multi-account
    """
    
    def __init__(self, token_store: TokenStore):
        self.token_store = token_store
        self._credentials: dict[str, OAuthCredentials] = {}
    
    def register_provider(self, provider: str, credentials: OAuthCredentials):
        """Зарегистрировать OAuth-провайдера."""
        ...
    
    def get_authorization_url(self, provider: str) -> str:
        """Получить URL для авторизации."""
        ...
    
    def exchange_code(self, provider: str, code: str) -> OAuthToken:
        """Обменять authorization code на токен."""
        ...
    
    def get_valid_token(self, provider: str) -> OAuthToken:
        """Получить валидный токен (с автоматическим refresh)."""
        token = self.token_store.get(provider)
        if token and token.is_expired:
            token = self._refresh_token(provider, token)
        return token
    
    def _refresh_token(self, provider: str, token: OAuthToken) -> OAuthToken:
        """Обновить токен через refresh_token."""
        ...
```

**Модуль `token_store.py`:**

```python
class TokenStore:
    """
    Хранение OAuth-токенов в ~/.selfos/tokens/
    
    Формат: ~/.selfos/tokens/{provider}.json
    """
    
    def __init__(self, tokens_dir: Path | None = None):
        self.tokens_dir = tokens_dir or Path("~/.selfos/tokens").expanduser()
        self.tokens_dir.mkdir(parents=True, exist_ok=True)
    
    def get(self, provider: str) -> OAuthToken | None:
        """Получить токен провайдера."""
        ...
    
    def save(self, provider: str, token: OAuthToken) -> None:
        """Сохранить токен."""
        ...
    
    def delete(self, provider: str) -> None:
        """Удалить токен."""
        ...
    
    def list_providers(self) -> list[str]:
        """Список авторизованных провайдеров."""
        ...
```

**Модуль `rate_limiter.py`:**

```python
class RateLimiter:
    """
    Rate limiting для API-запросов.
    
    Поддерживает:
    - Requests per minute
    - Requests per day
    - Auto-retry with backoff
    """
    
    def __init__(self, config: dict[str, Any]):
        self.limits = config  # {"google": {"rpm": 60, "rpd": 100000}, ...}
        self._counters: dict[str, list[float]] = {}
    
    def can_request(self, provider: str) -> bool:
        """Можно ли делать запрос к провайдеру."""
        ...
    
    def record_request(self, provider: str) -> None:
        """Запросить запрос."""
        ...
    
    def wait_if_needed(self, provider: str) -> float:
        """Подождать, если нужно. Вернуть время ожидания."""
        ...
```

---

#### Stage 2 — Gmail Integration (5 дней)

**Плагин `gmail_plugin.py`:**

```python
class GmailPlugin(BaseSelfOSPlugin):
    """Интеграция с Gmail через Google API."""
    
    name = "gmail"
    description = "Read, search, and send emails via Gmail"
    version = "1.0.0"
    
    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self.oauth = OAuthManager(TokenStore())
        self.rate_limiter = RateLimiter(config.get("rate_limits", {}))
    
    def execute(self, **kwargs):
        action = kwargs.get("action", "list")
        
        if action == "list":
            return self._list_emails(
                query=kwargs.get("query", ""),
                max_results=kwargs.get("max_results", 10),
            )
        elif action == "read":
            return self._read_email(message_id=kwargs["message_id"])
        elif action == "send":
            return self._send_email(
                to=kwargs["to"],
                subject=kwargs["subject"],
                body=kwargs["body"],
            )
        elif action == "search":
            return self._search_emails(query=kwargs["query"])
        elif action == "unread_count":
            return self._unread_count()
    
    def _list_emails(self, query: str, max_results: int) -> dict:
        """Получить список писем."""
        token = self.oauth.get_valid_token("google")
        # Google Gmail API v1
        ...
    
    def _send_email(self, to: str, subject: str, body: str) -> dict:
        """Отправить письмо."""
        ...
    
    def _on_register(self, hook_registry):
        """Подписка на хуки."""
        hook_registry.subscribe(
            "email:send", self.name, self._before_send, hook_type="before"
        )
```

**Настройка через CLI:**

```
selfos plugin setup gmail       # OAuth2 flow: откроет браузер
selfos plugin setup gmail --test # Тест соединения
selfos gmail list               # Список писем
selfos gmail list --unread      # Только непрочитанные
selfos gmail search "from:boss"
selfos gmail send --to user@example.com --subject "Hello"
```

**Конфигурация `selfos.yaml`:**

```yaml
integrations:
  gmail:
    enabled: true
    check_interval_minutes: 15
    auto_categorize: true
    rate_limits:
      rpm: 250
      rpd: 1000000
```

---

#### Stage 3 — Google Calendar Integration (4 дня)

**Плагин `google_calendar_plugin.py`:**

```python
class GoogleCalendarPlugin(BaseSelfOSPlugin):
    """Интеграция с Google Calendar."""
    
    name = "google_calendar"
    description = "Manage calendar events via Google Calendar API"
    version = "1.0.0"
    
    def execute(self, **kwargs):
        action = kwargs.get("action", "list")
        
        if action == "list":
            return self._list_events(
                time_min=kwargs.get("time_min"),
                time_max=kwargs.get("time_max"),
                max_results=kwargs.get("max_results", 10),
            )
        elif action == "create":
            return self._create_event(
                summary=kwargs["summary"],
                start=kwargs["start"],
                end=kwargs["end"],
                description=kwargs.get("description", ""),
            )
        elif action == "update":
            return self._update_event(event_id=kwargs["event_id"], **kwargs)
        elif action == "delete":
            return self._delete_event(event_id=kwargs["event_id"])
        elif action == "today":
            return self._today_events()
        elif action == "freebusy":
            return self._freebusy(
                time_min=kwargs["time_min"],
                time_max=kwargs["time_max"],
            )
    
    def _today_events(self) -> dict:
        """События на сегодня."""
        ...
    
    def _freebusy(self, time_min: str, time_max: str) -> dict:
        """Проверка занятости."""
        ...
```

**CLI:**

```
selfos calendar list                    # Список событий
selfos calendar today                   # События на сегодня
selfos calendar create --summary "Meeting" --start "2026-06-23T10:00" --end "2026-06-23T11:00"
selfos calendar freebusy --start "2026-06-23T09:00" --end "2026-06-23T18:00"
```

---

#### Stage 4 — Todoist Integration (3 дня)

**Плагин `todoist_plugin.py` (обновление существующего):**

Текущий `todoist_plugin.py` — заглушка. Обновляем на реальный API:

```python
class TodoistPlugin(BaseSelfOSPlugin):
    """Интеграция с Todoist REST API v2."""
    
    name = "todoist"
    description = "Manage tasks via Todoist API"
    version = "2.0.0"
    
    def execute(self, **kwargs):
        action = kwargs.get("action", "list")
        
        if action == "list":
            return self._list_tasks(
                project_id=kwargs.get("project_id"),
                label=kwargs.get("label"),
            )
        elif action == "create":
            return self._create_task(
                content=kwargs["content"],
                project_id=kwargs.get("project_id"),
                due_string=kwargs.get("due"),
                priority=kwargs.get("priority", 1),
            )
        elif action == "complete":
            return self._complete_task(task_id=kwargs["task_id"])
        elif action == "projects":
            return self._list_projects()
        elif action == "labels":
            return self._list_labels()
    
    def _list_tasks(self, project_id=None, label=None) -> dict:
        """Получить список задач."""
        token = self.config.get("api_token")  # Todoist API token
        # Todoist REST API v2
        ...
```

**CLI:**

```
selfos todoist list                     # Все задачи
selfos todoist list --project inbox     # Задачи в проекте
selfos todoist create "Buy groceries" --due tomorrow --priority 2
selfos todoist complete <task_id>
selfos todoist projects                 # Список проектов
```

---

#### Stage 5 — GitHub Integration (3 дня)

**Плагин `github_plugin.py`:**

```python
class GitHubPlugin(BaseSelfOSPlugin):
    """Интеграция с GitHub API."""
    
    name = "github"
    description = "Monitor repos, issues, and PRs via GitHub API"
    version = "1.0.0"
    
    def execute(self, **kwargs):
        action = kwargs.get("action", "notifications")
        
        if action == "notifications":
            return self._get_notifications()
        elif action == "issues":
            return self._list_issues(
                repo=kwargs.get("repo"),
                state=kwargs.get("state", "open"),
            )
        elif action == "prs":
            return self._list_prs(
                repo=kwargs.get("repo"),
                state=kwargs.get("state", "open"),
            )
        elif action == "search":
            return self._search_code(query=kwargs["query"])
    
    def _get_notifications(self) -> dict:
        """Непрочитанные уведомления."""
        ...
```

**CLI:**

```
selfos github notifications          # Уведомления
selfos github issues --repo user/repo
selfos github prs --repo user/repo --state open
selfos github search "TODO in:file"
```

---

#### Stage 6 — Hooks Integration (2 дня)

**Расширение hook-точек для интеграций:**

```python
# Новые hook-точки:
"email:received"     # Новое письмо (Gmail)
"email:sent"         # Письмо отправлено
"calendar:event"     # Новое/изменённое событие (Calendar)
"task:created"       # Задача создана (Todoist)
"task:completed"     # Задача завершена
"github:notification"# GitHub уведомление
"github:issue"       # GitHub issue
```

**Пример использования в `SuggestionEngine`:**

```python
# LLM может предлагать действия на основе интеграций:
# "У вас 3 непрочитанных письма от важных контактов. Ответить?"
# "Meeting через 2 часа. Начать подготовку?"
```

---

#### Stage 7 — Tests + E2E (5 дней)

| Тест | Что проверяет |
|---|---|
| `test_oauth_manager.py` | Authorization URL, code exchange, token refresh |
| `test_token_store.py` | Save/load/delete/list, expiry handling |
| `test_rate_limiter.py` | Rate limiting, backoff, multi-provider |
| `test_gmail_plugin.py` | Mock Gmail API, CRUD operations |
| `test_google_calendar_plugin.py` | Mock Calendar API, events CRUD |
| `test_todoist_plugin.py` | Mock Todoist API, tasks CRUD |
| `test_github_plugin.py` | Mock GitHub API, notifications/issues/PRs |
| `test_integrations_e2e.py` | Полный цикл: OAuth → API → Plugin → Suggestion |

---

### Итого Phase 6

| Этап | Дни | Модули |
|---|---|---|
| OAuth2 Infrastructure | 4 | `oauth_manager.py`, `token_store.py`, `rate_limiter.py` |
| Gmail Integration | 5 | `gmail_plugin.py` |
| Google Calendar | 4 | `google_calendar_plugin.py` |
| Todoist Integration | 3 | `todoist_plugin.py` (обновление) |
| GitHub Integration | 3 | `github_plugin.py` |
| Hooks Integration | 2 | Новые hook-точки |
| Tests + E2E | 5 | `tests/test_integrations_*.py` |
| **Итого** | **26 дней** | |

---

## Общая временная шкала

```
2026-06-22 ─── Phase 4 завершена (0.4.0) ✅
    │
    ├── Phase 5: LLM-powered Suggestions (14 дней)
    │   Week 1: Provider Abstraction + Prompt System + SuggestionEngine
    │   Week 2: Cost Guard + CLI + Tests
    │   └── 0.5.0 release
    │
    ├── Phase 6: Real API Integrations (26 дней)
    │   Week 3: OAuth2 Infrastructure
    │   Week 4–5: Gmail + Calendar + Todoist
    │   Week 6: GitHub + Hooks + Tests
    │   └── 0.6.0 release
    │
    └── Phase 7: Web UI (после Phase 6, ~6 недель)
        └── 1.0.0 release
```

---

## Зависимости Phase 5

| Зависимость | Нужна для | Статус |
|---|---|---|
| `httpx` | HTTP-запросы к LLM API | ✅ В pyproject.toml |
| `pyyaml` | YAML-шаблоны промптов | ✅ В pyproject.toml |
| `openai` (опционально) | OpenAI SDK | ⚠️ Добавить в `[dev]` |
| `anthropic` (опционально) | Anthropic SDK | ⚠️ Добавить в `[dev]` |
| `ContextEngine` | Контекст для LLM | ✅ Существует |
| `HookRegistry` | Интеграция с hooks | ✅ Существует |
| `CostGuard` | Контроль расходов | 🔨 Реализовать |

## Зависимости Phase 6

| Зависимость | Нужна для | Статус |
|---|---|---|
| `google-api-python-client` | Gmail + Calendar API | ⚠️ Добавить в pyproject.toml |
| `google-auth-oauthlib` | OAuth2 для Google | ⚠️ Добавить в pyproject.toml |
| `todoist-api-python` (опционально) | Todoist SDK | ⚠️ Добавить в `[dev]` |
| `PyGithub` (опционально) | GitHub SDK | ⚠️ Добавить в `[dev]` |
| `OAuthManager` | Токены | 🔨 Реализовать в Phase 6 |
| `TokenStore` | Хранение | 🔨 Реализовать в Phase 6 |
| `RateLimiter` | Rate limiting | 🔨 Реализовать в Phase 6 |
