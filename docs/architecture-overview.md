# Self OS Architecture Overview (Phase 3)

## Основные компоненты

- **EventFactory** — единая фабрика событий
- **PluginRegistry** — реестр всех плагинов
- **DelegationEngine** — глубокое делегирование и Zero-input delegation
- **ContextEngine** — анализ паттернов и проактивные предложения
- **UnifiedInterface** — единая точка входа (CLI / Web / Voice)
- **EmailService** — работа с почтой + делегирование

## Принципы архитектуры

1. Всё через плагины
2. Всё через `EventFactory`
3. Делегирование только через `DelegationEngine`
4. Пользователь всегда в контроле
5. Activity Log — единственный источник правды

## Текущая структура

```
src/selfos/
├── __init__.py
├── __main__.py
├── activity.py
├── base_selfos_plugin.py
├── browser.py
├── cli.py
├── config.py
├── context_engine.py
├── delegation_engine.py
├── event_factory.py
├── plugin_registry.py
├── scheduler.py
├── trust.py
├── unified_interface.py
└── email/
    ├── __init__.py
    ├── base.py
    ├── delegation.py
    ├── service.py
    └── smtp_provider.py
```