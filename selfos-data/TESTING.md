# Phase 1 Testing Guide

## Цель Phase 1
Проверить работу нескольких типов делегируемых действий, механики доверия и auto-режима.

## Что тестировать

### 1. Несколько типов действий одновременно
- Убедись, что в `selfos.yaml` настроены разные пороги для:
  - `event_categorization`
  - `daily_summary`
  - `tag_suggestion`

### 2. Механика доверия
- Проверь, что trust counter увеличивается при принятии предложений.
- Проверь работу скрипта `trust_manager.py` (сброс счётчика).

### 3. Auto-режим
- Используй `enable_auto.py` для включения/выключения auto-режима.
- Проверь `auto_categorize.py` — работает ли автоматическая категоризация при достижении порога.

### 4. Дашборд
- Запусти `update_dashboard_v2.py`
- Убедись, что в `README.md` отображаются:
  - Диагностика
  - Секция **Suggested Actions & Trust Levels**
  - Текущий статус каждого действия (AUTO / REVIEW)

### 5. Еженедельный отчёт
- Запусти `weekly_report.py`
- Убедись, что Action `weekly-report.yml` создаёт Issue с отчётом.

## Рекомендуемый порядок тестирования

1. Сделай несколько событий в `data/activity/`
2. Запусти `categorize-events.yml` (Review mode)
3. Прими 3–5 предложений категорий
4. Запусти `update_dashboard_v2.py` и проверь README
5. Включи auto-режим для `event_categorization`
6. Запусти `auto_categorize.py`
7. Сгенерируй Weekly Report

## Завершение Phase 1
После успешного прохождения всех проверок Phase 1 считается завершённой.