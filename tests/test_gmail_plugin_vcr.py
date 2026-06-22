from __future__ import annotations

import base64
import importlib.util
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import httpx
import pytest

from selfos.integrations.token_store import OAuthToken
from selfos.plugins.gmail_plugin import GmailPlugin

HAS_PYTEST_RECORDING = importlib.util.find_spec("pytest_recording") is not None


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


def _response(payload: dict[str, object]) -> httpx.Response:
    return httpx.Response(200, json=payload)


def _gmail_mock_handler(request: httpx.Request) -> httpx.Response:
    path = request.url.path
    query = request.url.query.decode("utf-8")
    if path.endswith("/messages") and query == "maxResults=1&q=is%3Aunread":
        return _response({"resultSizeEstimate": 7, "messages": [{"id": "m1"}]})
    if path.endswith("/messages") and query == "maxResults=2":
        return _response({"messages": [{"id": "m1"}, {"id": "m2"}]})
    if path.endswith("/messages/m1"):
        return _response(
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
                        "data": (
                            base64.urlsafe_b64encode(b"Message body")
                            .decode("ascii")
                            .rstrip("=")
                        ),
                    },
                },
            }
        )
    if path.endswith("/messages/m2"):
        return _response(
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
    if path.endswith("/labels"):
        return _response({"labels": [{"name": "INBOX"}, {"name": "STARRED"}]})
    if path.endswith("/messages/send") and request.method == "POST":
        payload = json.loads(request.content.decode("utf-8"))
        assert "raw" in payload
        return _response({"id": "sent-1"})
    raise AssertionError(f"Unexpected request: {request.method} {request.url}")


def _assert_gmail_plugin_contract(plugin: GmailPlugin) -> None:
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


@pytest.fixture
def gmail_server() -> str:
    try:
        server = ThreadingHTTPServer(("127.0.0.1", 0), GmailHandler)
    except PermissionError:
        pytest.skip("Local sockets are unavailable in this environment")
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
        "match_on": ["method", "scheme", "host", "path", "query"],
    }


def test_gmail_plugin_with_mock_transport() -> None:
    transport = httpx.MockTransport(_gmail_mock_handler)
    client = httpx.Client(transport=transport, base_url="https://gmail.googleapis.com")
    plugin = GmailPlugin(
        oauth_manager=FakeOAuthManager(),
        http_client=client,
        base_url="https://gmail.googleapis.com",
    )
    _assert_gmail_plugin_contract(plugin)


@pytest.mark.vcr(record_mode="once") if HAS_PYTEST_RECORDING else pytest.mark.skip(
    reason="pytest-recording is not installed"
)
def test_gmail_plugin_with_vcr(gmail_server: str) -> None:
    plugin = GmailPlugin(
        oauth_manager=FakeOAuthManager(),
        base_url=gmail_server,
    )
    _assert_gmail_plugin_contract(plugin)
