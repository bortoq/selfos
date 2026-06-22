"""
Self OS Email Module

Provides real email functionality with delegation support.
"""

from .base import EmailMessage, EmailProvider
from .delegation import can_delegate_email, suggest_email_with_trust
from .smtp_provider import SMTPProvider

__all__ = [
    "EmailProvider",
    "EmailMessage", 
    "SMTPProvider",
    "can_delegate_email",
    "suggest_email_with_trust"
]