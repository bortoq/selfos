# Activity Event Schema

## Event

```json
{
  "id": "string (unique)",
  "timestamp": "string (ISO 8601)",
  "source": "github | calendar | notes",
  "type": "commit | issue | pr | event | task | note",
  "title": "string",
  "metadata": {
    "repo": "string (optional)",
    "url": "string (optional)",
    "category": "string (optional)"
  }
}
```

## Примеры

### GitHub Commit
```json
{
  "id": "github-commit-abc123",
  "timestamp": "2025-06-21T10:30:00Z",
  "source": "github",
  "type": "commit",
  "title": "Fix delegation engine",
  "metadata": {
    "repo": "bortoq/selfos",
    "url": "https://github.com/bortoq/selfos/commit/abc123"
  }
}
```

### Calendar Event
```json
{
  "id": "calendar-event-456",
  "timestamp": "2025-06-21T14:00:00Z",
  "source": "calendar",
  "type": "event",
  "title": "Team meeting",
  "metadata": {
    "category": "Work"
  }
}
```