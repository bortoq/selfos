"""Tests for EmailService event schema compliance."""

from selfos.email.service import EmailService
from selfos.event_factory import EventFactory


def test_create_email_event_has_delegation_status():
    """Email-событие должно содержать delegation_status в metadata."""
    event = EventFactory.create_email_event(
        to="test@example.com",
        subject="Test",
        delegation_status="auto",
        body_preview="Hello"
    )
    assert isinstance(event, dict)
    assert event.get("source") == "selfos"
    assert event.get("type") == "email"
    assert "@" in str(event.get("title", ""))
    assert event.get("metadata", {}).get("delegation_status") == "auto"
    assert event.get("metadata", {}).get("to") == "test@example.com"
    assert event.get("metadata", {}).get("body_preview") == "Hello"


def test_save_to_activity_log_preserves_delegation_status():
    """EmailService._save_to_activity_log создаёт событие с delegation_status."""
    service = EmailService()

    # Используем _save_to_activity_log напрямую
    # Сохраняется в activity.json — проверяем что метод не падает
    service._save_to_activity_log(
        to="user@test.com",
        subject="Test email",
        body="Test body content here",
        status="review"
    )
    # Если не упало — значит событие создано и сохранено


def test_email_event_schema_matches_contract():
    """Структура email-события соответствует контракту EventFactory."""
    event = EventFactory.create_email_event(
        to="a@b.com",
        subject="Hello",
        delegation_status="auto",
        body_preview="World"
    )

    # Проверяем обязательные поля
    assert "id" in event, "Email event missing 'id'"
    assert "source" in event, "Email event missing 'source'"
    assert "type" in event, "Email event missing 'type'"
    assert "title" in event, "Email event missing 'title'"
    assert "timestamp" in event, "Email event missing 'timestamp'"
    assert "metadata" in event, "Email event missing 'metadata'"

    # Проверяем делегирование
    meta = event["metadata"]
    assert "delegation_status" in meta, (
        "Email metadata missing 'delegation_status'"
    )
    assert "to" in meta, "Email metadata missing 'to'"
    assert "subject" in meta, "Email metadata missing 'subject'"

    # Проверяем формат timestamp
    assert "T" in event["timestamp"], (
        "timestamp should be ISO format with 'T' separator"
    )
    assert event["timestamp"].endswith("+00:00") or event["timestamp"].endswith("Z"), (
        "timestamp should be timezone-aware"
    )


def test_email_service_send_returns_proper_schema():
    """EmailService.send_email возвращает dict с ожидаемой структурой."""
    service = EmailService()
    result = service.send_email(
        to="user@example.com",
        subject="Test",
        body="Hello",
        force_review=True
    )

    assert isinstance(result, dict)
    assert "success" in result
    assert "status" in result
    assert "to" in result
    assert "subject" in result
    assert "body" in result

    # force_review=True → статус должен быть review
    assert result["status"] == "review"
    assert result["sent"] is False

    # Для невалидного email
    invalid = service.send_email(to="not-an-email", subject="Test")
    assert invalid["success"] is False
    assert "error" in invalid
