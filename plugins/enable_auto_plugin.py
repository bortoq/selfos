"""
EnableAutoPlugin — плагин для управления auto-режимом.

Читает и пишет selfos.yaml через selfos.config.
"""

from typing import Any

import yaml

from selfos.base_selfos_plugin import BaseSelfOSPlugin
from selfos.config import config_file


class EnableAutoPlugin(BaseSelfOSPlugin):
    name = "enable_auto"
    description = "Enables or disables auto mode for actions"

    def _load_config(self) -> dict[str, Any]:
        path = config_file()
        if path.exists():
            with open(path) as f:
                return yaml.safe_load(f) or {}
        return {}

    def _save_config(self, config: dict[str, Any]) -> None:
        path = config_file()
        with open(path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

    def execute(self, **kwargs: Any) -> dict[str, Any]:
        action = kwargs.get('action', '')
        enable = kwargs.get('enable', True)
        status = "enabled" if enable else "disabled"

        config = self._load_config()
        if "force_review" not in config:
            config["force_review"] = {}
        config["force_review"][action] = not enable
        self._save_config(config)

        return {
            "action": action,
            "status": status,
            "message": f"Auto mode for {action} is now {status}",
            "config_updated": True
        }