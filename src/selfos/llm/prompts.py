from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from selfos.config import prompts_dir


class PromptManager:
    VALID_ACTIONS = [
        "email_reply",
        "task_create",
        "note",
        "review_context",
        "review_schedule",
    ]

    def __init__(self, user_dir: Path | None = None) -> None:
        self._user_dir = user_dir or prompts_dir()
        self._builtin_dir = Path(__file__).with_name("templates")

    def load_template(self, name: str) -> dict[str, str]:
        file_name = f"{name}.yaml"
        for directory in (self._user_dir, self._builtin_dir):
            path = directory / file_name
            if path.exists():
                with open(path, encoding="utf-8") as handle:
                    raw = yaml.safe_load(handle) or {}
                if isinstance(raw, dict):
                    return {
                        "system": str(raw.get("system", "")),
                        "user_template": str(raw.get("user_template", "")),
                    }
        raise FileNotFoundError(f"Prompt template not found: {name}")

    def render(self, name: str, context: dict[str, Any]) -> str:
        template = self.load_template(name)
        context_json = json.dumps(context, ensure_ascii=False, indent=2, sort_keys=True)
        return (
            f"{template['system']}\n\n" + template["user_template"].format(
                context_json=context_json,
                valid_actions_json=json.dumps(self.VALID_ACTIONS, ensure_ascii=False),
            )
        )
