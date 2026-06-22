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
├── event_factory.py
├── plugin_registry.py
├── delegation_engine.py
├── context_engine.py
├── unified_interface.py
├── scheduler.py
├── browser.py
└── email/
    ├── base.py
    ├── smtp_provider.py
    ├── delegation.py
    └── service.py
```