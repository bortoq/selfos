"""
SmartSuggestionsPlugin — плагин для генерации умных предложений.
"""

from typing import Any

from selfos.base_selfos_plugin import BaseSelfOSPlugin
from selfos.llm.suggestion_engine import SuggestionEngine


class SmartSuggestionsPlugin(BaseSelfOSPlugin):
    name = "smart_suggestions"
    description = "Generates smart proactive suggestions based on activity"

    def execute(self, **kwargs: Any) -> dict[str, Any]:
        recent_events = kwargs.get("recent_events") or []
        if recent_events:
            suggestions = self._generate_legacy_suggestions(recent_events)
            return {"suggestions": suggestions}

        engine = SuggestionEngine()
        response = engine.get_suggestions(mode="rules")
        suggestions = [item["summary"] for item in response["suggestions"]]
        return {
            "suggestions": suggestions
        }

    def _generate_legacy_suggestions(self, events: list[dict[str, Any]]) -> list[str]:
        suggestions: list[str] = []
        has_meeting = any("meeting" in str(e).lower() for e in events)
        has_work = any("phase" in str(e).lower() or "plugin" in str(e).lower() for e in events)

        if has_meeting:
            suggestions.append("Consider blocking focus time after the meeting")
        if has_work:
            suggestions.append("You have active work tasks — schedule deep work")
        if not suggestions:
            suggestions.append("Your activity looks balanced today")
        return suggestions
