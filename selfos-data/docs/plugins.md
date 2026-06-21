# Self OS Plugins Documentation

## Overview

Self OS supports external integrations through a plugin system.  
All plugins inherit from `BasePlugin` and implement the `fetch()` method (and optionally `push()`).

## Available Plugins

### 1. Calendar Plugin (`calendar_plugin.py`)
- **Service**: Google Calendar (mock implementation)
- **Purpose**: Import calendar events into Activity Log
- **Methods**: `fetch()`
- **Configuration**: `calendar_id`

### 2. Todoist Plugin (`todoist_plugin.py`)
- **Service**: Todoist
- **Purpose**: Import tasks and create new tasks
- **Methods**: `fetch()`, `push()`
- **Configuration**: `project_id` (optional)

### 3. Photo Classifier (`photo_classifier.py`)
- **Purpose**: Classify photos into categories (food, receipt, people, document, other)
- **Integration**: Triggered via GitHub Action when files are added to `media/`

## How to Add a New Plugin

1. Create a new file in `plugins/`
2. Inherit from `BasePlugin`
3. Implement `fetch()` method
4. Optionally implement `push()`
5. Add the plugin to `.github/workflows/import-external.yml`

## Trust Integration

New actions from plugins can be tracked using `trust_manager_v2.py`:
- `calendar_import`
- `todoist_import`
- `photo_classification`

## Future Improvements

- Real API integrations (Google Calendar, Todoist)
- OAuth2 support
- Error handling and retries
- Rate limiting