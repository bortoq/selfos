# Self OS Testing Guide

## Запуск тестов

```bash
# Из корня проекта
PYTHONPATH=/home/user/work/selfos python3 -m pytest tests/ -v

# С coverage
PYTHONPATH=/home/user/work/selfos python3 -m pytest tests/ --cov=src/selfos

# Только smoke-тесты CLI
PYTHONPATH=/home/user/work/selfos python3 -m pytest tests/test_cli_smoke.py -v

# Только trust manager
PYTHONPATH=/home/user/work/selfos python3 -m pytest tests/test_trust_manager.py -v
```

## Структура тестов

| Файл                          | Что тестирует                          |
|-------------------------------|----------------------------------------|
| `test_cli_smoke.py`          | CLI entry points (status, note, task) |
| `test_trust_manager.py`      | Trust counters, thresholds, auto-mode  |
| `test_photo_trust.py`        | Photo classification trust integration |
| `test_task_creation.py`      | Event creation structure               |
| `test_categorize.py`         | Category suggestion logic              |
| `test_plugin_registry.py`    | Plugin loading and execution           |
| `test_scheduler.py`          | Task/event scheduling                  |
| `test_email_service.py`      | Email sending and delegation           |
| ...                          | ...                                    |

## Что тестируется

### CLI (Phase 3)
- `selfos status` — проверка вывода статуса
- `selfos note "text"` — создание заметки через plugin
- `selfos task "title"` — создание задачи через EventFactory
- `selfos suggest` — получение предложений
- `selfos browser links` — список быстрых ссылок
- Обработка отсутствующих/неверных аргументов

### Trust Manager
- Пороги доверия для разных типов действий
- Увеличение счётчика при успешных выполнениях
- Автоматический переход в AUTO-режим при достижении порога
- Принудительный REVIEW через `force_review` в `selfos.yaml`

### EventFactory
- Создание событий с UUID v4 (нет коллизий)
- Валидация source, event_type, title
- Единый формат для всех типов событий

## Изоляция тестов

- Тесты trust_manager используют `tmp_path` + `monkeypatch` — не пишут в реальный `data/trust.json`
- Все тесты независимы и не оставляют побочных эффектов

## CI/CD

- GitHub Actions (`.github/workflows/ci.yml`)
- `pytest` — обязателен (без `|| true`)
- `ruff` — проверка линтинга (0 errors)
- `mypy` — проверка типов (опционально)
