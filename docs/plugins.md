# Self OS Plugins Documentation

## Overview

Self OS supports external integrations through a plugin system.
All plugins inherit from `BasePlugin` and implement the `execute()` method.

Plugins are registered in `src/selfos/plugin_registry.py` via `@PluginRegistry.register()`.

## Available Built-in Plugins

### 1. Quick Note Plugin (`src/selfos/plugins/quick_note_plugin.py`)
- **Purpose**: Create quick notes with smart tag suggestions
- **Method**: `execute(text: str)`
- **Returns**: suggested tags + category

### 2. Smart Suggestions Plugin (`src/selfos/plugins/smart_suggestions_plugin.py`)
- **Purpose**: Generate proactive suggestions based on context
- **Method**: `execute()`
- **Returns**: list of action suggestions

### 3. Photo Classifier (`scripts/photo_trust.py`)
- **Purpose**: Classify photos into categories (food, receipt, people, document, other)
- **Integration**: Trust-based auto-classification support

## How to Add a New Plugin

1. Create a new file in `src/selfos/plugins/`
2. Inherit from `BasePlugin`
3. Implement `execute()` method
4. Decorate with `@PluginRegistry.register("plugin_name")`
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
from src.selfos.plugin_registry import PluginRegistry

# Get a plugin
plugin = PluginRegistry.get_plugin("quick_note")
result = plugin.execute(text="Hello world")
```

## Future Improvements

- Real API integrations (Google Calendar, Todoist)
- External plugin loading
- Plugin lifecycle hooks
- OAuth2 support
