"""
EmailService - Единая точка входа для работы с почтой в Self OS.

Объединяет:
- Отправку писем
- Делегирование (на основе доверия)
- Сохранение событий в Activity Log
- Предложение текста письма
"""


from scripts.create_task import create_task_event
from scripts.create_task import save_event as save_activity_event

from .base import EmailMessage
from .delegation import suggest_email_with_trust
from .smtp_provider import SMTPProvider


class EmailService:
    """
    Высокоуровневый сервис для работы с email в Self OS.
    Рекомендуется использовать именно его.
    """

    def __init__(self, provider: SMTPProvider | None = None):
        self.provider = provider or SMTPProvider()

    def send_email(
        self,
        to: str,
        subject: str,
        body: str = "",
        force_review: bool = False
    ) -> dict:
        """
        Отправляет письмо с учётом делегирования.

        Returns:
            dict с результатом операции
        """
        # Валидация
        if not to or "@" not in to:
            return {"success": False, "error": "Invalid recipient email"}
        if not subject:
            return {"success": False, "error": "Subject cannot be empty"}

        # Получаем предложение и статус делегирования
        suggestion = suggest_email_with_trust(to, subject, body)

        final_body = suggestion["message"]["body"]
        status = suggestion["status"]

        # Если пользователь принудительно хочет review
        if force_review:
            status = "review"

        result = {
            "success": True,
            "status": status,
            "to": to,
            "subject": subject,
            "body": final_body,
            "trust": suggestion["trust"]
        }

        # Сохраняем событие в Activity Log
        self._save_to_activity_log(to, subject, final_body, status)

        # Отправляем, если auto
        if status == "auto":
            msg = EmailMessage(to=to, subject=subject, body=final_body)
            sent = self.provider.send(msg)
            result["sent"] = sent
        else:
            result["sent"] = False
            result["message"] = "Email is in REVIEW mode. Use force_review=False to send."

        return result

    def _save_to_activity_log(self, to: str, subject: str, body: str, status: str):
        """Сохраняет email-событие в Activity Log"""
        event = create_task_event(
            title=f"Email to {to}: {subject}",
            project="Email",
            priority=2
        )
        # Переопределяем тип события
        event["type"] = "email"
        event["metadata"]["email_status"] = status
        event["metadata"]["body_preview"] = body[:100]

        save_activity_event(event)

    def suggest_email(self, to: str, subject: str, body: str = "") -> dict:
        """Только предлагает текст письма без отправки"""
        return suggest_email_with_trust(to, subject, body)