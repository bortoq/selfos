from __future__ import annotations

import base64

import httpx

from selfos.integrations.token_store import OAuthToken
from selfos.plugins.gmail_plugin import GmailPlugin


class FakeOAuthManager:
    def get_valid_token(self) -> OAuthToken:
        return OAuthToken(access_token="test-token")


class FakeHTTPClient:
    def __init__(self) -> None:
        self.sent_payload: str | None = None

    def get(
        self,
        url: str,
        *,
        headers: dict[str, str],
        params: dict[str, object] | None = None,
    ) -> httpx.Response:
        if url.endswith("/messages") and params == {"maxResults": 1, "q": "is:unread"}:
            return httpx.Response(200, json={"resultSizeEstimate": 7, "messages": [{"id": "1"}]})
        if url.endswith("/messages") and params == {"maxResults": 2}:
            return httpx.Response(
                200,
                json={
                    "messages": [
                        {"id": "m1"},
                        {"id": "m2"},
                    ]
                },
            )
        if url.endswith("/messages/m1"):
            return httpx.Response(
                200,
                json={
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
                },
            )
        if url.endswith("/messages/m2"):
            return httpx.Response(
                200,
                json={
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
                },
            )
        if url.endswith("/labels"):
            return httpx.Response(200, json={"labels": [{"name": "INBOX"}, {"name": "STARRED"}]})
        raise AssertionError(f"Unexpected GET: {url} params={params}")

    def post(self, url: str, *, headers: dict[str, str], json: dict[str, str]) -> httpx.Response:
        assert url.endswith("/messages/send")
        self.sent_payload = json["raw"]
        return httpx.Response(200, json={"id": "sent-1"})


def test_gmail_plugin_unread_count_and_listing() -> None:
    plugin = GmailPlugin(
        oauth_manager=FakeOAuthManager(),
        http_client=FakeHTTPClient(),
    )

    assert plugin.unread_count() == 7

    messages = plugin.list_messages(max_results=2)
    assert [message["subject"] for message in messages] == ["Hello", "World"]
    assert messages[0]["body"] == "Message body"


def test_gmail_plugin_lists_labels_and_sends_messages() -> None:
    http_client = FakeHTTPClient()
    plugin = GmailPlugin(
        oauth_manager=FakeOAuthManager(),
        http_client=http_client,
    )

    assert plugin.list_labels() == ["INBOX", "STARRED"]

    result = plugin.send_message(
        to="user@example.com",
        subject="Hello",
        body="Text body",
    )

    assert result["id"] == "sent-1"
    assert http_client.sent_payload is not None
