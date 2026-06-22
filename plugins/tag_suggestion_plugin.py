"""
TagSuggestionPlugin — плагин для предложения тегов к событиям.
"""

import re
from typing import Any

from selfos.base_selfos_plugin import BaseSelfOSPlugin


class TagSuggestionPlugin(BaseSelfOSPlugin):
    name = "tag_suggestion"
    description = "Suggests relevant tags for events"

    TAG_RULES = [
        (r"(urgent|asap|deadline)", ["urgent"]),
        (r"(meeting|call|sync)", ["meeting"]),
        (r"(bug|fix|error)", ["bug"]),
        (r"(feature|implement|add)", ["feature"]),
        (r"(review|pr|pull request)", ["review"]),
        (r"(personal|family|friend)", ["personal"]),
    ]

    def execute(self, title: str, **kwargs) -> dict[str, Any]:
        tags = self._suggest_tags(title)
        return {
            "title": title,
            "suggested_tags": tags
        }

    def _suggest_tags(self, title: str) -> list[str]:
        tags = set()
        title_lower = title.lower()
        for pattern, tag_list in self.TAG_RULES:
            if re.search(pattern, title_lower):
                tags.update(tag_list)
        return list(tags) if tags else ["general"]