import pytest
from src.selfos.email.base import EmailMessage
from src.selfos.email.smtp_provider import SMTPProvider


def test_email_message_creation():
    msg = EmailMessage(to="test@example.com", subject="Test", body="Hello")
    assert msg.to == "test@example.com"
    assert msg.subject == "Test"


def test_smtp_provider_initialization():
    provider = SMTPProvider()
    assert provider.smtp_server == "smtp.gmail.com"  # default
    assert provider.use_tls is True