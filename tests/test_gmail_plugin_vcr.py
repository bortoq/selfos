from __future__ import annotations

import base64
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

pytest.importorskip("pytest_recording")

from selfos.integrations.token_store import OAuthToken
from selfos.plugins.gmail_plugin import GmailPlugin

pytestmark = pytest.mark.vcr(record_mode="once")


class FakeOAuthManager:
    def get_valid_token(self) -> OAuthToken:
        return OAuthToken(access_token="test-token")


class GmailHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        return

    def do_GET(self) -> None:
        if self.path.endswith("/messages?maxResults=1&q=is%3Aunread"):
            return self._json({"resultSizeEstimate": 7, "messages": [{"id": "m1"}]})
        if self.path.endswith("/messages?maxResults=2"):
            return self._json({"messages": [{"id": "m1"}, {"id": "m2"}]})
        if self.path.endswith("/messages/m1"):
            return self._json(
                {
                    "id": "m1",
                    "threadId": "t1",
                    "labelIds": ["UNREAD"],
                    "snippet": "hello",
                    "payload": {
                        "headers": [
                            {"name": "Subject", "value": "Hello"},
                            {"name": "From", "value": "boss@example.com"},
                            {"name": "Date", "value": "Mon, 01 Jan 2026 10:00:00 +0000"},
                        ],
                        "body": {
                            "data": base64.urlsafe_b64encode(b"Message body")
                            .decode("ascii")
                            .rstrip("="),
                        },
                    },
                }
            )
        if self.path.endswith("/messages/m2"):
            return self._json(
                {
                    "id": "m2",
                    "threadId": "t2",
                    "labelIds": [],
                    "snippet": "world",
                    "payload": {
                        "headers": [
                            {"name": "Subject", "value": "World"},
                            {"name": "From", "value": "team@example.com"},
                            {"name": "Date", "value": "Mon, 01 Jan 2026 11:00:00 +0000"},
                        ],
                        "body": {},
                    },
                }
            )
        if self.path.endswith("/labels"):
            return self._json({"labels": [{"name": "INBOX"}, {"name": "STARRED"}]})
        raise AssertionError(f"Unexpected GET path: {self.path}")

    def do_POST(self) -> None:
        if self.path.endswith("/messages/send"):
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            assert "raw" in payload
            return self._json({"id": "sent-1"})
        raise AssertionError(f"Unexpected POST path: {self.path}")

    def _json(self, payload: dict[str, object]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


@pytest.fixture
def gmail_server() -> str:
    server = ThreadingHTTPServer(("127.0.0.1", 0), GmailHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        thread.join(timeout=1)


@pytest.fixture
def vcr_config() -> dict[str, object]:
    return {
        "filter_headers": ["authorization"],
        "decode_compressed_response": True,
    }


def test_gmail_plugin_with_vcr(gmail_server: str) -> None:
    plugin = GmailPlugin(
        oauth_manager=FakeOAuthManager(),
        base_url=gmail_server,
    )

    assert plugin.unread_count() == 7
    messages = plugin.list_messages(max_results=2)
    assert [message["subject"] for message in messages] == ["Hello", "World"]
    assert plugin.list_labels() == ["INBOX", "STARRED"]

    result = plugin.send_message(
        to="user@example.com",
        subject="Hello",
        body="Text body",
    )
    assert result["id"] == "sent-1"
