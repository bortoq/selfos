"""
Email Delegation Logic

Интеграция с системой доверия Self OS.
"""

from selfos.trust import can_auto, get_threshold, increase_trust


def can_delegate_email() -> bool:
    """Можно ли автоматически отправлять письма?"""
    return can_auto("email_send")


from typing import Any


def suggest_email_with_trust(
    to: str,
    subject: str,
    body: str,
    sender: str = "user"
) -> dict[str, Any]:
    """
    Предлагает текст письма и проверяет уровень доверия.
    """
    # Простая логика предложения (в будущем можно заменить на LLM)
    if not body or len(body.strip()) < 15:
        suggested_body = f"Hi,\n\nRegarding your message about: {subject}\n\nBest regards"
    else:
        suggested_body = body

    action_type = "email_send"
    current_trust = increase_trust(action_type)
    threshold = get_threshold(action_type)
    auto_mode = can_delegate_email()

    return {
        "message": {
            "to": to,
            "subject": subject,
            "body": suggested_body
        },
        "trust": {
            "current": current_trust,
            "threshold": threshold,
            "can_auto": auto_mode
        },
        "status": "auto" if auto_mode else "review"
    }