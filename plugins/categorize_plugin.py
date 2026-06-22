"""
CategorizePlugin — плагин для категоризации событий.

Переведён из scripts/categorize.py в соответствии с Architecture Contract.
"""

import re
from typing import Any

from src.selfos.base_selfos_plugin import BaseSelfOSPlugin

RULES = [
    (r"(meeting|standup|call|sync)", "Work"),
    (r"(gym|run|sport|health|doctor)", "Health"),
    (r"(buy|shop|payment|invoice|salary)", "Finance"),
    (r"(family|friend|birthday|vacation)", "Personal"),
]


def suggest_category(title: str) -> str:
    """Предлагает категорию на основе заголовка"""
    title_lower = title.lower()
    for pattern, category in RULES:
        if re.search(pattern, title_lower):
            return category
    return "Other"


class CategorizePlugin(BaseSelfOSPlugin):
    """
    Плагин для автоматической категоризации событий.
    """

    name = "categorize"
    description = "Suggests category for events (Work, Personal, Health, Finance, Other)"

    def __init__(self, config: dict[str, Any] = None):
        super().__init__(config)

    def execute(self, title: str, **kwargs) -> dict[str, Any]:
        """
        Предлагает категорию для события.
        """
        category = suggest_category(title)

        return {
            "title": title,
            "suggested_category": category,
            "status": "suggested"
        }
