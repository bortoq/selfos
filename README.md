# Self OS

**Self OS** — личная операционная система, выступающая в роли посредника между пользователем и его цифровыми инструментами.

## Цель проекта

Self OS помогает пользователю:

- Агрегировать данные из разных приложений в единый Activity Log
- Постепенно делегировать рутинные задачи системе через механизм доверия
- Снижать когнитивную нагрузку
- Полностью владеть своими данными

## Основные принципы

- **Посредничество** — Self OS не дублирует функционал внешних программ
- **Плагины** — все интеграции происходят только через плагины
- **Делегирование по доверию** — автоматизация возможна только при достаточном уровне доверия
- **Единый интерфейс** — пользователь взаимодействует со всеми программами через Self OS
- **Activity Log** — единый источник правды

## Текущий статус

**Phase 5c завершена**: поверх завершённых Phase 5a/5b добавлены Calendar, Todoist и GitHub integrations, а `SuggestionEngine` теперь собирает multi-source context.

- Полноценная работа с почтой + делегирование
- Gmail OAuth + Gmail CLI integration
- Google Calendar CLI integration
- Todoist CLI integration
- GitHub notifications/issues/PR CLI integration
- Встроенный планировщик задач и событий
- Браузерная навигация и быстрый доступ
- Context Engine с проактивными предложениями
- Unified `SuggestionEngine` (`rules` + `llm`) с email/calendar/tasks/github context
- Ollama по умолчанию, OpenAI/Anthropic через explicit cloud opt-in
- Глубокое делегирование (Zero-input delegation)
- Единый интерфейс (CLI + заготовка Web)

## Быстрый старт

```bash
# Установка
pip install -e ".[dev]"

# Основные команды
selfos status
selfos note "Текст заметки"
selfos task "Название задачи" --priority 1
selfos email send user@example.com "Тема" "Текст письма" --auto
selfos schedule list tasks
selfos context suggest
selfos suggest --llm
selfos gmail unread_count
selfos calendar today
selfos todoist list
selfos github notifications
selfos delegate status email_send
```

## Документация

- [User Guide](docs/user-guide.md)
- [Architecture Overview](docs/architecture-overview.md)
- [Architecture Contract](docs/architecture-contract.md)
- [Compliance Report](docs/compliance-report.md)

## Архитектура

Self OS построен на следующих ключевых компонентах:

- `EventFactory` — единая фабрика событий
- `PluginRegistry` — реестр плагинов
- `DelegationEngine` — глубокое делегирование
- `ContextEngine` — анализ паттернов и проактивные предложения
- `UnifiedInterface` — единая точка входа
- `OAuthManager` / `SecureTokenStore` — foundation для внешних интеграций
- `SuggestionEngine` — единый pipeline suggestions с multi-source context

## Лицензия

MIT License — см. [LICENSE](LICENSE)
