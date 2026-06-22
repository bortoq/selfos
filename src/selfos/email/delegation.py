"""
Email Delegation Logic

Интеграция с системой доверия Self OS.
"""

import sys
from pathlib import Path

# Добавляем корневую папку проекта для импорта
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.trust_manager_v2 import can_auto, get_threshold, increase_trust


def can_delegate_email() -> bool:
    """Можно ли автоматически отправлять письма?"""
    return can_auto("email_send")


def suggest_email_with_trust(
    to: str,
    subject: str,
    body: str,
    sender: str = "user"
) -> dict:
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