from __future__ import annotations

from typing import Any, cast

import httpx


class GitHubPlugin:
    def __init__(
        self,
        api_token: str,
        http_client: httpx.Client | Any | None = None,
        base_url: str = "https://api.github.com",
    ) -> None:
        self._api_token = api_token
        self._http = http_client or httpx.Client(timeout=30.0)
        self._base_url = base_url.rstrip("/")

    def notifications(self) -> list[dict[str, Any]]:
        payload = cast(list[dict[str, Any]], self._get("/notifications"))
        return [self._normalize_notification(item) for item in payload]

    def issues(self, repo: str, state: str = "open") -> list[dict[str, Any]]:
        payload = cast(
            list[dict[str, Any]],
            self._get(f"/repos/{repo}/issues", params={"state": state}),
        )
        return [self._normalize_issue(item, repo=repo, item_type="issue") for item in payload]

    def pull_requests(self, repo: str, state: str = "open") -> list[dict[str, Any]]:
        payload = cast(
            list[dict[str, Any]],
            self._get(f"/repos/{repo}/pulls", params={"state": state}),
        )
        return [
            self._normalize_issue(item, repo=repo, item_type="pull_request")
            for item in payload
        ]

    def search(self, query: str) -> list[dict[str, Any]]:
        payload = cast(dict[str, Any], self._get("/search/issues", params={"q": query}))
        items = payload.get("items", [])
        return [self._normalize_issue(item, repo="", item_type="search") for item in items]

    def _normalize_notification(self, item: dict[str, Any]) -> dict[str, Any]:
        subject = item.get("subject", {})
        repository = item.get("repository", {})
        return {
            "id": str(item.get("id", "")),
            "title": str(subject.get("title", "")),
            "repository": str(repository.get("full_name", "")),
            "url": str(item.get("url", "")),
            "state": str(item.get("reason", "")),
            "type": str(subject.get("type", "")),
        }

    def _normalize_issue(
        self,
        item: dict[str, Any],
        *,
        repo: str,
        item_type: str,
    ) -> dict[str, Any]:
        return {
            "id": str(item.get("id", "")),
            "title": str(item.get("title", "")),
            "repository": repo,
            "url": str(item.get("html_url", "")),
            "state": str(item.get("state", "")),
            "type": item_type,
        }

    def _get(
        self,
        path: str,
        *,
        params: dict[str, str] | None = None,
    ) -> list[dict[str, Any]] | dict[str, Any]:
        response = self._http.get(
            f"{self._base_url}{path}",
            headers=self._auth_headers(),
            params=params,
        )
        self._raise_for_status(response)
        payload = response.json()
        if isinstance(payload, list):
            return cast(list[dict[str, Any]], payload)
        return cast(dict[str, Any], payload)

    def _auth_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_token}",
            "Accept": "application/vnd.github+json",
        }

    def _raise_for_status(self, response: httpx.Response) -> None:
        if response.status_code >= 400:
            raise ValueError(f"GitHub API error: {response.status_code} {response.text}")
