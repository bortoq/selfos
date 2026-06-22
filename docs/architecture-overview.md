# Self OS Architecture Overview (Phase 5b)

## Основные компоненты

| Компонент | Назначение | Файл |
|-----------|-----------|------|
| **EventFactory** | Единая фабрика событий | `src/selfos/event_factory.py` |
| **PluginRegistry** | Реестр всех плагинов (built-in + external) | `src/selfos/plugin_registry.py` |
| **PluginManifest** | Манифест плагина (YAML) | `src/selfos/plugin_manifest.py` |
| **PluginMarketplace** | Каталог доступных плагинов | `src/selfos/plugin_marketplace.py` |
| **Plugin SDK** | Утилиты создания/валидации/скаффолдинга плагинов | `src/selfos/plugin_sdk.py` |
| **BaseSelfOSPlugin** | Базовый класс для всех плагинов | `src/selfos/base_selfos_plugin.py` |
| **HookRegistry** | Точки расширения ядра (before/after/instead) | `src/selfos/hooks.py` |
| **DelegationEngine** | Делегирование + кастомные правила | `src/selfos/delegation_engine.py` |
| **Delegation Rules** | Пользовательские правила делегирования | `src/selfos/delegation_rules.py` |
| **ContextEngine** | Анализ паттернов и проактивные предложения | `src/selfos/context_engine.py` |
| **OAuthManager** | OAuth2 browser/device flows | `src/selfos/integrations/oauth_manager.py` |
| **SecureTokenStore** | Profile-aware token storage | `src/selfos/integrations/token_store.py` |
| **RateLimiter** | Persistent rate limiting for integrations | `src/selfos/integrations/rate_limiter.py` |
| **GmailPlugin** | Gmail REST integration | `src/selfos/plugins/gmail_plugin.py` |
| **SuggestionEngine** | Единый pipeline suggestions (`rules` + `llm`) | `src/selfos/llm/suggestion_engine.py` |
| **LLM Providers** | Ollama/OpenAI/Anthropic adapters | `src/selfos/llm/providers.py` |
| **PromptManager** | Built-in and user prompt templates | `src/selfos/llm/prompts.py` |
| **CostGuard** | Daily cost limit + semantic cache key | `src/selfos/llm/cost_guard.py` |
| **UnifiedInterface** | Единая точка входа (CLI / Web / Voice) | `src/selfos/unified_interface.py` |
| **Trust Manager** | Система доверия (счётчики, пороги) | `src/selfos/trust.py` |

## Принципы архитектуры

1. Всё через плагины
2. Всё через `EventFactory`
3. Делегирование через `DelegationEngine` + кастомные правила
4. Пользователь всегда в контроле (Override > Rules > Trust)
5. Activity Log — единственный источник правды
6. Платформа — открыта для расширения через хуки и плагины

## Полная структура

```
src/selfos/
├── __init__.py              # v0.6.0 (Phase 5b)
├── base_selfos_plugin.py    # Базовый класс + on_register()
├── browser.py               # Browser service
├── cli.py                   # CLI (все команды, делегирование в API)
├── config.py                # Пути: data, plugins, rules, trust
├── context_engine.py        # Анализ контекста
├── delegation_engine.py     # Делегирование + кастомные правила
├── delegation_rules.py      # DSL правил делегирования (Phase 4)
├── event_factory.py         # Фабрика событий
├── hooks.py                 # HookRegistry (Phase 4)
├── plugin_contracts.py      # TypedDicts + Protocols
├── plugin_manifest.py       # PluginManifest (Phase 4)
├── plugin_marketplace.py    # Marketplace + install/remove/update (Phase 4)
├── plugin_registry.py       # Реестр плагинов
├── plugin_sdk.py            # SDK для плагинов (Phase 4)
├── integrations/
│   ├── __init__.py
│   ├── oauth_manager.py
│   ├── rate_limiter.py
│   └── token_store.py
├── llm/
│   ├── __init__.py
│   ├── cost_guard.py
│   ├── models.py
│   ├── prompts.py
│   ├── providers.py
│   ├── security.py
│   ├── state.py
│   ├── suggestion_engine.py
│   └── templates/
├── plugins/
│   ├── __init__.py
│   └── gmail_plugin.py
├── scheduler.py             # Планировщик задач
├── trust.py                 # Система доверия
├── unified_interface.py     # Единый интерфейс
└── email/
    ├── __init__.py
    ├── base.py
    ├── delegation.py
    ├── service.py
    └── smtp_provider.py
```

## CLI команды

```
selfos note <text>           # Создать заметку (триггерит хуки)
selfos task <text>           # Создать задачу (триггерит хуки)
selfos status                # Статус системы
selfos suggest               # Проактивные предложения (триггерит хуки)
selfos suggest --llm         # LLM-backed suggestions with rules fallback
selfos config llm            # Конфигурация LLM provider / model
selfos gmail list/read/send  # Gmail integration
selfos plugin setup gmail    # OAuth setup for Gmail
selfos profile create/switch # Профили для интеграций
selfos email send/suggest    # Email операции
selfos schedule task/event/list  # Планировщик
selfos browser open/search/links # Браузер
selfos context summary/patterns/suggest  # Контекст
selfos delegate enable/disable/status    # Переопределения
selfos delegate rule add/list/remove/info # Кастомные правила
selfos plugin list                      # Список плагинов
selfos plugin info <name>               # Информация о плагине
selfos plugin init <name>               # Скаффолдинг плагина
selfos plugin create <name>             # Создать + зарегистрировать
selfos plugin install <name|url>        # Установить из маркетплейса или URL
selfos plugin remove <name>             # Удалить плагин
selfos plugin update [name]             # Проверить/применить обновления
selfos plugin search <query>            # Поиск в маркетплейсе
```

## Порядок принятия решения о делегировании

```
1. Ручные переопределения (overrides) — высший приоритет
2. Пользовательские правила (custom rules) — по приоритету
3. Критические действия (CRITICAL_ACTIONS) — всегда deny
4. Стандартная система доверия (trust.py) — fallback
```
