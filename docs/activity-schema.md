# Activity Event Schema

## Event (текущий формат, Phase 3)

```json
{
  "id": "string (UUID v4)",
  "timestamp": "string (ISO 8601 UTC)",
  "source": "selfos | github | calendar | email",
  "type": "task | note | email | event | commit | issue",
  "title": "string",
  "metadata": {
    "project": "string (optional)",
    "priority": "integer (optional)",
    "tags": ["string"] (optional),
    "category": "string (optional)",
    "url": "string (optional)",
    "repo": "string (optional)"
  }
}
```

## Примеры

### Task (через EventFactory)
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "timestamp": "2026-06-22T10:30:00+00:00",
  "source": "selfos",
  "type": "task",
  "title": "Finish documentation",
  "metadata": {
    "project": "Self OS",
    "priority": 1,
    "created_via": "selfos"
  }
}
```

### Note
```json
{
  "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "timestamp": "2026-06-22T12:00:00+00:00",
  "source": "selfos",
  "type": "note",
  "title": "Meeting notes",
  "metadata": {
    "tags": ["meeting", "work"],
    "category": "Work"
  }
}
```

### Email
```json
{
  "id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
  "timestamp": "2026-06-22T14:00:00+00:00",
  "source": "selfos",
  "type": "email",
  "title": "Email to user@example.com: Project Update",
  "metadata": {
    "to": "user@example.com",
    "subject": "Project Update",
    "delegation_status": "auto"
  }
}
```

## Создание событий

Все события должны создаваться через `EventFactory.create_event()`:

```python
from src.selfos.event_factory import EventFactory

event = EventFactory.create_event(
    source="selfos",
    event_type="task",
    title="My task",
    metadata={"priority": 2}
)
```

## Хранение

События сохраняются в `data/activity/YYYY-MM-DD.json` через `save_event()`.
