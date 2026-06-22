from src.selfos.email.service import EmailService


def test_email_service_validation():
    service = EmailService()

    # Пустой получатель
    result = service.send_email("", "Test", "Body")
    assert result["success"] is False
    assert "Invalid recipient" in result["error"]

    # Пустая тема
    result = service.send_email("test@example.com", "", "Body")
    assert result["success"] is False
    assert "Subject cannot be empty" in result["error"]


def test_email_service_suggest():
    service = EmailService()
    result = service.suggest_email("test@example.com", "Meeting", "")
    assert "message" in result
    assert "trust" in result
    assert result["status"] in ["review", "auto"]