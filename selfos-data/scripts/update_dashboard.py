#!/usr/bin/env python3
"""
Updates README.md with daily diagnostics from Activity Log
"""

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

DATA_DIR = Path("data/activity")
README_PATH = Path("README.md")


def load_events():
    events = []
    for file in DATA_DIR.glob("*.json"):
        with open(file) as f:
            events.extend(json.load(f))
    return events


def calculate_stats(events):
    today = datetime.now().date().isoformat()

    stats = {
        "completed": 0,
        "postponed": 0,
        "cancelled": 0,
        "categories": defaultdict(int)
    }

    for event in events:
        if event.get("timestamp", "").startswith(today):
            cat = event.get("metadata", {}).get("category", "Other")
            stats["categories"][cat] += 1

            # Simple heuristic for demo
            if "done" in event.get("title", "").lower():
                stats["completed"] += 1
            elif "postpone" in event.get("title", "").lower():
                stats["postponed"] += 1
            elif "cancel" in event.get("title", "").lower():
                stats["cancelled"] += 1

    return stats


def generate_score(stats):
    total = sum(stats["categories"].values())
    if total == 0:
        return 50
    score = min(100, int(stats["completed"] * 10 + total * 2))
    return min(score, 100)


def update_readme(stats, score):
    content = f"""# Self OS

**Статус:** Phase 0 (MVP)

## Диагностика

**Сегодня**

- Выполнено: {stats['completed']}
- Отложено: {stats['postponed']}
- Отменено: {stats['cancelled']}

**Распределение по категориям**
"""

    for cat, count in sorted(stats["categories"].items()):
        content += f"- {cat}: {count}\n"

    content += f"""
**Life Management Score:** {score} / 100

---

*Данные обновляются автоматически через GitHub Actions*

## Как использовать

1. Подключи источники данных
2. Разрешай предложения системы в Issues
3. После 10 принятых предложений одного типа можно включить auto-режим

---

*Self OS — агрегатор взаимодействий и инструмент делегирования*
"""

    with open(README_PATH, 'w') as f:
        f.write(content)

    print("README.md updated with diagnostics.")


if __name__ == "__main__":
    events = load_events()
    stats = calculate_stats(events)
    score = generate_score(stats)
    update_readme(stats, score)