"""
Gmail plugin backed by the Gmail REST API.
"""

from __future__ import annotations

import base64
from email.message import EmailMessage
from typing import Any, cast

import httpx


class GmailPlugin:
    """Small Gmail API wrapper for CLI and future hooks."""

    def __init__(
        self,
        oauth_manager: Any,
        http_client: httpx.Client | Any | None = None,
        user_id: str = "me",
        base_url: str = "https://gmail.googleapis.com",
    ) -> None:
        self._oauth_manager = oauth_manager
        self._http = http_client or httpx.Client(timeout=30.0)
        self._user_id = user_id
        self._base_url = base_url.rstrip("/")

    def fetch(self) -> list[dict[str, Any]]:
        return self.list_messages(unread_only=True)

    def unread_count(self) -> int:
        response = self._get(
            f"/gmail/v1/users/{self._user_id}/messages",
            params={"maxResults": 1, "q": "is:unread"},
        )
        return int(response.get("resultSizeEstimate", 0))

    def list_messages(
        self,
        *,
        query: str | None = None,
        max_results: int = 10,
        unread_only: bool = False,
    ) -> list[dict[str, Any]]:
        query_value = self._build_query(query=query, unread_only=unread_only)
        params: dict[str, Any] = {"maxResults": max_results}
        if query_value:
            params["q"] = query_value
        response = self._get(f"/gmail/v1/users/{self._user_id}/messages", params=params)
        messages = response.get("messages", [])
        return [self.read_message(item["id"]) for item in messages]

    def search_messages(self, query: str, *, max_results: int = 10) -> list[dict[str, Any]]:
        return self.list_messages(query=query, max_results=max_results)

    def read_message(self, message_id: str) -> dict[str, Any]:
        response = self._get(f"/gmail/v1/users/{self._user_id}/messages/{message_id}")
        payload = response.get("payload", {})
        headers = self._header_map(payload.get("headers", []))
        return {
            "id": response.get("id", message_id),
            "thread_id": response.get("threadId"),
            "labels": response.get("labelIds", []),
            "subject": headers.get("subject", ""),
            "from": headers.get("from", ""),
            "date": headers.get("date", ""),
            "snippet": response.get("snippet", ""),
            "body": self._extract_body(payload),
        }

    def send_message(self, *, to: str, subject: str, body: str) -> dict[str, Any]:
        message = EmailMessage()
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode("ascii").rstrip("=")
        return self._post(
            f"/gmail/v1/users/{self._user_id}/messages/send",
            json={"raw": raw},
        )

    def list_labels(self) -> list[str]:
        response = self._get(f"/gmail/v1/users/{self._user_id}/labels")
        labels = response.get("labels", [])
        return [str(label.get("name", "")) for label in labels]

    def _auth_headers(self) -> dict[str, str]:
        token = self._oauth_manager.get_valid_token()
        return {"Authorization": f"Bearer {token.access_token}"}

    def _get(self, path: str, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
        response = self._http.get(
            f"{self._base_url}{path}",
            headers=self._auth_headers(),
            params=params,
        )
        self._raise_for_status(response)
        return cast(dict[str, Any], response.json())

    def _post(self, path: str, *, json: dict[str, str]) -> dict[str, Any]:
        response = self._http.post(
            f"{self._base_url}{path}",
            headers=self._auth_headers(),
            json=json,
        )
        self._raise_for_status(response)
        return cast(dict[str, Any], response.json())

    def _raise_for_status(self, response: httpx.Response) -> None:
        if response.status_code >= 400:
            raise ValueError(f"Gmail API error: {response.status_code} {response.text}")

    def _build_query(self, *, query: str | None, unread_only: bool) -> str | None:
        query_parts: list[str] = []
        if query:
            query_parts.append(query)
        if unread_only:
            query_parts.append("is:unread")
        if not query_parts:
            return None
        return " ".join(query_parts)

    def _header_map(self, headers: list[dict[str, str]]) -> dict[str, str]:
        return {
            str(item.get("name", "")).lower(): str(item.get("value", ""))
            for item in headers
        }

    def _extract_body(self, payload: dict[str, Any]) -> str:
        body = payload.get("body", {})
        data = body.get("data")
        if isinstance(data, str) and data:
            return self._decode_body(data)

        parts = payload.get("parts", [])
        for part in parts:
            part_body = part.get("body", {})
            part_data = part_body.get("data")
            if isinstance(part_data, str) and part_data:
                return self._decode_body(part_data)
        return ""

    def _decode_body(self, data: str) -> str:
        padding = "=" * (-len(data) % 4)
        decoded = base64.urlsafe_b64decode(data + padding)
        return decoded.decode("utf-8", errors="replace")
