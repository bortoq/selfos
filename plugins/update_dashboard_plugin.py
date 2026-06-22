"""
UpdateDashboardPlugin — плагин для обновления дашборда.

Анализирует события и возвращает статистику + скор.
"""

from collections import defaultdict
from datetime import datetime
from typing import Any

import yaml

from selfos.base_selfos_plugin import BaseSelfOSPlugin
from selfos.config import config_file


class UpdateDashboardPlugin(BaseSelfOSPlugin):
    name = "update_dashboard"
    description = "Updates the Self OS dashboard with latest diagnostics"

    def _load_config(self) -> dict[str, Any]:
        path = config_file()
        if path.exists():
            with open(path) as f:
                return yaml.safe_load(f) or {}
        return {}

    def execute(self, **kwargs: Any) -> dict[str, Any]:
        events = kwargs.get('events', [])
        today = datetime.now().date().isoformat()

        stats: dict[str, Any] = {
            "completed": 0,
            "postponed": 0,
            "cancelled": 0,
            "categories": defaultdict(int),
        }

        for event in events:
            if event.get("timestamp", "").startswith(today):
                cat = event.get("metadata", {}).get("category", "Other")
                stats["categories"][cat] += 1
                title = event.get("title", "").lower()
                if "done" in title:
                    stats["completed"] += 1
                elif "postpone" in title:
                    stats["postponed"] += 1
                elif "cancel" in title:
                    stats["cancelled"] += 1

        total = sum(stats["categories"].values())
        score = min(100, int(stats["completed"] * 10 + total * 2)) if total > 0 else 50

        config = self._load_config()
        thresholds = config.get("trust_thresholds", {})
        force_review = config.get("force_review", {})

        trust = kwargs.get("trust", {})
        actions = []
        for action, threshold in thresholds.items():
            current = trust.get(action, 0)
            is_auto = not force_review.get(action, False) and current >= threshold
            status = "AUTO" if is_auto else "REVIEW"
            actions.append(f"- **{action}**: {status} ({current}/{threshold})")
        suggested_actions = "\n".join(actions) if actions else "No actions configured."

        return {
            "status": "Dashboard updated",
            "events_count": len(events),
            "stats": {
                "completed": stats["completed"],
                "postponed": stats["postponed"],
                "cancelled": stats["cancelled"],
                "categories": dict(stats["categories"]),
            },
            "score": score,
            "suggested_actions": suggested_actions,
        }