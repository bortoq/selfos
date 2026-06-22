"""
SMTP Email Provider - Real email sending implementation.
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from .base import EmailMessage


class SMTPProvider:
    """Real SMTP email provider."""

    def __init__(
        self,
        smtp_server: str = None,
        smtp_port: int = 587,
        username: str = None,
        password: str = None,
        use_tls: bool = True
    ):
        self.smtp_server = smtp_server or os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = smtp_port
        self.username = username or os.getenv("SMTP_USERNAME")
        self.password = password or os.getenv("SMTP_PASSWORD")
        self.use_tls = use_tls

    def send(self, message: EmailMessage) -> bool:
        """Send email via SMTP."""
        if not self.username or not self.password:
            print("[ERROR] SMTP credentials not configured")
            return False

        try:
            msg = MIMEMultipart()
            msg["From"] = self.username
            msg["To"] = message.to
            msg["Subject"] = message.subject
            msg.attach(MIMEText(message.body, "plain"))

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)

            print(f"[SUCCESS] Email sent to {message.to}")
            return True

        except Exception as e:
            print(f"[ERROR] Failed to send email: {e}")
            return False

    def fetch_unread(self, limit: int = 10) -> list[EmailMessage]:
        """Not implemented yet (would require IMAP)."""
        print("[INFO] fetch_unread not implemented in SMTPProvider")
        return []