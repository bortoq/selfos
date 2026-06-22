# Self OS User Guide (Phase 3)

## Основные команды

### Базовые команды

```bash
selfos status                 # Показать статус системы
selfos suggest                # Получить умные предложения
selfos note "Текст заметки"   # Создать заметку с делегированием
selfos task "Название задачи" # Создать задачу
```

### Email

```bash
selfos email send user@example.com "Тема" "Текст письма"
selfos email send user@example.com "Тема" "Текст" --auto   # Автоматическая отправка
selfos email suggest                                       # Интерактивное предложение
```

### Планировщик

```bash
selfos schedule task "Сделать отчёт" --due 2025-07-01 --priority 1
selfos schedule event "Встреча" "2025-06-25T10:00:00Z" --duration 60
selfos schedule list tasks
selfos schedule list events
```

### Браузер и быстрый доступ

```bash
selfos browser open gmail
selfos browser search "self os"
selfos browser links --category productivity
```

### Контекст и делегирование

```bash
selfos context summary
selfos context patterns
selfos context suggest

selfos delegate enable email_send
selfos delegate disable photo_classification
selfos delegate status email_send
```

## Система делегирования

Self OS использует уровни доверия для автоматического выполнения действий.

- При низком доверии — действие требует подтверждения (REVIEW)
- При высоком доверии — действие выполняется автоматически (AUTO)

Вы можете вручную управлять делегированием через команду `delegate`.

## Activity Log

Все действия сохраняются в `data/activity/`. Это единый источник правды системы.

---

Self OS — ваш личный посредник между вами и цифровыми инструментами.