#!/usr/bin/env python3
"""
Enable Auto Mode for a specific action type.
Can be triggered manually or via GitHub Issue.
"""

import sys
import yaml
from pathlib import Path

CONFIG_FILE = Path("selfos.yaml")


def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            return yaml.safe_load(f)
    return {}


def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)


def enable_auto(action_type: str):
    config = load_config()
    
    if "force_review" not in config:
        config["force_review"] = {}
    
    config["force_review"][action_type] = False
    
    save_config(config)
    print(f"Auto mode ENABLED for: {action_type}")


def disable_auto(action_type: str):
    config = load_config()
    
    if "force_review" not in config:
        config["force_review"] = {}
    
    config["force_review"][action_type] = True
    
    save_config(config)
    print(f"Auto mode DISABLED for: {action_type} (forced review)")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python enable_auto.py <enable|disable> <action_type>")
        sys.exit(1)
    
    command = sys.argv[1]
    action = sys.argv[2]
    
    if command == "enable":
        enable_auto(action)
    elif command == "disable":
        disable_auto(action)
    else:
        print("Unknown command. Use 'enable' or 'disable'")