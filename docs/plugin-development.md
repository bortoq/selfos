# Plugin Development Guide

## Overview

Self OS plugins are Python classes that inherit from `BaseSelfOSPlugin`.
They can extend Self OS in multiple ways:

- **Commands**: Execute custom logic via `execute()`
- **Hooks**: Subscribe to core events (before/after actions)
- **Protocols**: Implement typed contracts for known plugin types

## Quick Start

### 1. Scaffold a plugin

```bash
selfos plugin init my-plugin --author "Your Name" --description "Does something useful"
```

This creates:

```
my-plugin/
├── plugin.yaml          # Plugin manifest
├── __init__.py          # Package init
└── my_plugin.py         # Plugin implementation
```

### 2. Implement the plugin

Edit `my_plugin.py`:

```python
"""
my-plugin — a plugin for Self OS.
"""

from selfos.base_selfos_plugin import BaseSelfOSPlugin


class MyPluginPlugin(BaseSelfOSPlugin):
    name = "my-plugin"
    description = "Does something useful"
    version = "0.1.0"
    author = "Your Name"
    dependencies: list[str] = []
    protocol = ""

    def execute(self, **kwargs):
        """
        Main plugin logic. Called when the plugin is invoked.
        """
        # Your code here
        return {"result": "ok"}
```

### 3. Register and test

```bash
selfos plugin create my-plugin  # Creates + registers immediately
selfos plugin list              # Verify it's registered
```

## Plugin Manifest

Each plugin requires a `plugin.yaml` file:

```yaml
name: my-plugin
version: 1.0.0
description: My awesome plugin
entry_point: my_plugin:MyPluginPlugin
author: Your Name
protocol: ""
dependencies: []
config: {}
```

| Field | Required | Description |
|-------|----------|-------------|
| `name` | ✅ | Unique plugin name (`^[a-zA-Z0-9_-]+$`) |
| `version` | ✅ | Semantic version |
| `description` | ✅ | Short description |
| `entry_point` | ✅ | `module.path:ClassName` |
| `author` | ❌ | Author name |
| `protocol` | ❌ | Protocol to implement |
| `dependencies` | ❌ | List of pip dependencies |

## Hooks System (Phase 4)

Plugins can subscribe to core events using the `on_register()` method:

```python
class MyPlugin(BaseSelfOSPlugin):
    def on_register(self, hook_registry):
        hook_registry.subscribe("note:create", self.name, self.before_note, hook_type="before")
        hook_registry.subscribe("note:create", self.name, self.after_note, hook_type="after")

    def before_note(self, **context):
        """Called before a note is created. Can modify context."""
        text = context.get("text", "")
        context["text"] = f"[{self.name}] {text}"
        return context

    def after_note(self, result, **context):
        """Called after a note is created. Can modify result."""
        result["processed_by"] = self.name
        return result
```

### Hook Types

| Type | Purpose | Return |
|------|---------|--------|
| `before` | Modify context before operation | Updated context dict |
| `after` | Modify result after operation | Updated result |
| `instead` | Replace operation entirely | Any result (or None to skip) |

### Available Hook Points

| Hook Point | Triggered By | Context |
|------------|-------------|---------|
| `note:create` | `selfos note` | `text` |
| `task:create` | `selfos task` | `title`, `project`, `priority` |
| `email:send` | `selfos email send` | `to`, `subject`, `body` |
| `suggest:get` | `selfos suggest` | (none) |
| `schedule:task` | `selfos schedule task` | `title`, `due`, `priority` |
| `schedule:event` | `selfos schedule event` | `title`, `time`, `duration` |
| `browser:open` | `selfos browser open` | `name` |
| `browser:search` | `selfos browser search` | `query` |
| `context:summary` | `selfos context summary` | (none) |
| `delegate:check` | `selfos delegate status` | `action_type` |
| `plugin:install` | `selfos plugin install` | `name` |
| `plugin:remove` | `selfos plugin remove` | `name` |

### Example: Hook that logs all notes

```python
class NoteLogger(BaseSelfOSPlugin):
    name = "note-logger"
    description = "Logs all notes to a file"

    def on_register(self, hook_registry):
        hook_registry.subscribe("note:create", self.name, self.log_note, hook_type="after")

    def log_note(self, result, **context):
        with open("/tmp/notes.log", "a") as f:
            f.write(f"Note: {context.get('text')}\n")
        return result
```

## Protocols

Protocols provide type-safe contracts for plugins:

```python
from selfos.plugin_contracts import NotingPlugin

class MyNotePlugin(BaseSelfOSPlugin):
    protocol = "NotingPlugin"

    def execute(self, text: str, **kwargs) -> dict:
        # IDE knows text is required
        return {"result": f"Noted: {text}"}

# Runtime check
assert isinstance(plugin, NotingPlugin)
```

Available protocols: `NotingPlugin`, `CategorizerPlugin`, `SummarizerPlugin`, `SmartSuggestPlugin`.

## Plugin SDK

For simple plugins, use the SDK factory:

```python
from selfos.plugin_sdk import create_plugin

def my_handler(text: str, **kwargs) -> dict:
    return {"result": f"Hello {text}"}

MyPlugin = create_plugin("greeter", my_handler,
    description="Greets the user",
    protocol="NotingPlugin",
)
```

## Publishing to Marketplace

To share your plugin with the community:

1. Ensure your plugin has a valid `plugin.yaml`
2. Add it to `docs/plugin-marketplace.yaml` in the Self OS repo
3. Or publish it in a Git repository and share the URL:

```bash
selfos plugin install https://github.com/username/my-plugin
```

## Best Practices

1. **Error handling**: Always catch exceptions in `execute()` and return a dict with `success: bool`
2. **Isolation**: Don't use global state; use instance attributes
3. **Testing**: Write tests that create isolated `PluginRegistry` instances
4. **Versioning**: Follow semantic versioning for your plugin
5. **Hooks**: Keep hook handlers fast; don't block the main thread
