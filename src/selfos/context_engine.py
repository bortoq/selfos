"""
Context Engine for Self OS (Phase 3)

Анализирует историю активности пользователя и выявляет паттерны.
Предоставляет проактивные (контекстные) предложения.
"""

import json
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


class ContextEngine:
    """
    Анализирует Activity Log и формирует контекстные инсайты.
    """

    def __init__(self, data_dir: str = "data/activity") -> None:
        self.data_dir = Path(data_dir)
        self.events: list[dict[str, Any]] = []
        self._load_events()

    def _load_events(self, days: int = 30) -> None:
        """Загружает события за последние N дней"""
        self.events = []
        today = datetime.now().date()

        for i in range(days):
            day = today - timedelta(days=i)
            file = self.data_dir / f"{day.isoformat()}.json"
            if file.exists():
                with open(file) as f:
                    self.events.extend(json.load(f))

    def get_patterns(self) -> dict[str, Any]:
        """Выявляет основные паттерны поведения"""
        if not self.events:
            return {"message": "Недостаточно данных для анализа"}

        # Анализ по категориям
        category_count: dict[str, int] = defaultdict(int)
        late_work_count = 0
        health_events = 0

        for event in self.events:
            cat = event.get("metadata", {}).get("category", "Other")
            category_count[cat] += 1

            # Анализ поздней работы
            try:
                hour = int(event["timestamp"][11:13])
                if cat == "Work" and hour >= 20:
                    late_work_count += 1
            except Exception:
                pass

            if cat == "Health":
                health_events += 1

        total = len(self.events)

        patterns = {
            "total_events": total,
            "top_categories": sorted(category_count.items(), key=lambda x: -x[1])[:3],
            "late_work_ratio": round(late_work_count / total, 2) if total > 0 else 0,
            "health_activity": health_events,
        }

        return patterns

    def get_proactive_suggestions(self) -> list[str]:
        """Генерирует проактивные предложения на основе контекста"""
        patterns = self.get_patterns()
        suggestions = []

        # Паттерн: много работы поздно вечером
        if patterns.get("late_work_ratio", 0) > 0.15:
            suggestions.append(
                "Вы часто работаете после 20:00. Рекомендуется выделять буферное время вечером."
            )

        # Паттерн: мало внимания здоровью
        if patterns.get("health_activity", 0) < 3:
            suggestions.append(
                "В последние недели мало событий в категории Health."
            " Возможно, стоит запланировать прогулки или спорт."
            )

        # Паттерн: доминирование одной категории
        top_cats = patterns.get("top_categories", [])
        if top_cats and top_cats[0][1] / patterns["total_events"] > 0.6:
            suggestions.append(
                f"Большинство событий ({top_cats[0][0]}) доминирует."
            f" Рассмотрите баланс между категориями."
            )

        if not suggestions:
            suggestions.append("Ваша активность выглядит сбалансированной.")

        return suggestions

    def get_context_summary(self) -> str:
        """Возвращает краткую сводку контекста"""
        patterns = self.get_patterns()
        return (
            f"Проанализировано {patterns.get('total_events', 0)} событий. "
            f"Основные категории: {patterns.get('top_categories', [])[:2]}."
        )