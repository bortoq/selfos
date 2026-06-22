"""
AutoCategorizePlugin — плагин для автоматической категоризации.
"""

from typing import Any

from selfos.base_selfos_plugin import BaseSelfOSPlugin


class AutoCategorizePlugin(BaseSelfOSPlugin):
    name = "auto_categorize"
    description = "Automatically categorizes events when trust is high"

    def execute(self, **kwargs: Any) -> dict[str, Any]:
        title = kwargs['title']
        # Простая логика (в будущем можно улучшить)
        category = "Work" if any(x in title.lower() for x in ["meeting", "call"]) else "Other"
        return {
            "title": title,
            "category": category,
            "status": "auto"
        }