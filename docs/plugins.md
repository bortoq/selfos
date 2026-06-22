# Self OS Plugins Documentation

## Overview

Self OS supports external integrations through a plugin system.
All plugins inherit from `BaseSelfOSPlugin` and implement the `execute()` method.

Plugins live in `plugins/` and are registered in `src/selfos/plugin_registry.py`.

## Available Built-in Plugins

### 1. Quick Note Plugin (`plugins/quick_note_plugin.py`)
- **Purpose**: Create quick notes with smart tag suggestions
- **Method**: `execute(text: str)`
- **Returns**: suggested tags + category

### 2. Smart Suggestions Plugin (`plugins/smart_suggestions_plugin.py`)
- **Purpose**: Generate proactive suggestions based on context
- **Method**: `execute()`
- **Returns**: list of action suggestions

### 3. Daily Summary Plugin (`plugins/daily_summary_plugin.py`)
- **Purpose**: Generate daily summary of events and activity
- **Method**: `execute(events: list)`
- **Returns**: summary string with statistics

> **Note:** Photo classification (`scripts/photo_trust.py`) exists as a standalone script,
> not a plugin. It uses the trust system via `selfos.trust` for auto-classification.

## How to Add a New Plugin

1. Create a new file in `plugins/`
2. Inherit from `BaseSelfOSPlugin`
3. Implement `execute()` method
4. Register in `src/selfos/plugin_registry.py` via `registry.register("name", PluginClass)` in `_auto_register()`
5. Optionally add CLI integration in `src/selfos/cli.py`

## Trust Integration

New actions from plugins can be tracked using `src/selfos/trust.py`:
- `calendar_import`
- `todoist_import`
- `photo_classification`
- `quick_note`

Trust thresholds are configured in `selfos.yaml`:
```yaml
trust_thresholds:
  photo_classification: 6
  calendar_import: 8
  todoist_import: 8
  quick_note: 5
```

## Plugin Registry

```python
from selfos.plugin_registry import PluginRegistry

# Get a plugin
plugin = PluginRegistry.get_plugin("quick_note")
result = plugin.execute(text="Hello world")
```

## Future Improvements

- Real API integrations (Google Calendar, Todoist)
- External plugin loading
- Plugin lifecycle hooks
- OAuth2 support
