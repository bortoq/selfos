"""
Base classes for email functionality.
"""

from dataclasses import dataclass
from typing import Protocol, Optional
from datetime import datetime


@dataclass
class EmailMessage:
    to: str
    subject: str
    body: str
    from_email: Optional[str] = None


class EmailProvider(Protocol):
    """Interface for email providers (SMTP, Gmail, etc.)"""

    def send(self, message: EmailMessage) -> bool:
        """Send an email. Returns True if successful."""
        ...

    def fetch_unread(self, limit: int = 10) -> list[EmailMessage]:
        """Fetch unread emails."""
        ...