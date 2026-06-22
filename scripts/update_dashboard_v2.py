#!/usr/bin/env python3
"""
Enhanced Dashboard Updater for Phase 1
Updates README.md with diagnostics + Suggested Actions + Trust levels.
"""

import json
import yaml
from pathlib import Path
from collections import defaultdict
from datetime import datetime

DATA_DIR = Path("data/activity")
README_PATH = Path("README.md")
CONFIG_FILE = Path("selfos.yaml")
TRUST_FILE = Path("data/trust.json")


def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            return yaml.safe_load(f)
    return {}


def load_trust():
    if TRUST_FILE.exists():
        with open(TRUST_FILE, 'r') as f:
            return json.load(f)
    return {}


def load_events():
    events = []
    for file in DATA_DIR.glob("*.json"):
        with open(file, 'r') as f:
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

            title = event.get("title", "").lower()
            if "done" in title:
                stats["completed"] += 1
            elif "postpone" in title:
                stats["postponed"] += 1
            elif "cancel" in title:
                stats["cancelled"] += 1

    return stats


def generate_score(stats):
    total = sum(stats["categories"].values())
    if total == 0:
        return 50
    score = min(100, int((stats["completed"] * 10 + total * 2)))
    return min(score, 100)


def get_suggested_actions(trust, config):
    actions = []
    thresholds = config.get("trust_thresholds", {})
    force_review = config.get("force_review", {})

    for action, threshold in thresholds.items():
        current = trust.get(action, 0)
        is_auto = not force_review.get(action, False) and current >= threshold

        status = "AUTO" if is_auto else "REVIEW"
        progress = f"{current}/{threshold}"

        actions.append(f"- **{action}**: {status} ({progress})")

    return "\n".join(actions) if actions else "No actions configured."


def update_readme(stats, score, suggested_actions):
    content = f"""# Self OS

**Статус:** Phase 1

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

## Suggested Actions & Trust Levels

{suggested_actions}

---

*Self OS — агрегатор взаимодействий и инструмент делегирования*

*Данные обновляются автоматически через GitHub Actions*
"""

    with open(README_PATH, 'w') as f:
        f.write(content)

    print("README.md updated with Suggested Actions and Trust Levels.")


if __name__ == "__main__":
    events = load_events()
    stats = calculate_stats(events)
    score = generate_score(stats)

    config = load_config()
    trust = load_trust()
    suggested = get_suggested_actions(trust, config)

    update_readme(stats, score, suggested)