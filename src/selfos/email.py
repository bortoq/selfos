"""
Email Module for Self OS (Phase 3)

Provides email functionality with delegation support.
This is a prototype. In real usage it would integrate with IMAP/SMTP or Gmail API.
"""

from typing import List, Dict, Any
from datetime import datetime


def suggest_email_reply(subject: str, sender: str, body: str) -> str:
    """
    Suggests a reply based on the incoming email.
    This is a simple rule-based version. Later can be replaced with LLM.
    """
    body_lower = body.lower()

    if "meeting" in body_lower or "call" in body_lower:
        return f"Hi {sender.split('@')[0]},\n\nThanks for your email. I'm available for the meeting. Please let me know a convenient time.\n\nBest regards"
    elif "question" in body_lower or "?" in body:
        return f"Hi {sender.split('@')[0]},\n\nThank you for your question. I'll get back to you shortly with the details.\n\nBest regards"
    else:
        return f"Hi {sender.split('@')[0]},\n\nThanks for reaching out. I'll review this and respond soon.\n\nBest regards"


def create_email_event(to: str, subject: str, body: str, delegated: bool = True) -> Dict[str, Any]:
    """Create an email event for Activity Log"""
    return {
        "id": f"email-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "timestamp": datetime.now().isoformat() + "Z",
        "source": "selfos",
        "type": "email",
        "title": f"Email to {to}: {subject}",
        "metadata": {
            "to": to,
            "subject": subject,
            "body": body,
            "delegated": delegated
        }
    }


def send_email(to: str, subject: str, body: str, auto_send: bool = False) -> Dict[str, Any]:
    """
    Send an email (or prepare it for review).
    """
    if auto_send:
        print(f"[AUTO] Email sent to {to}")
    else:
        print(f"[REVIEW] Prepared email to {to} with subject: {subject}")

    event = create_email_event(to, subject, body, delegated=not auto_send)
    return event