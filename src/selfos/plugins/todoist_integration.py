from __future__ import annotations

from typing import Any, cast

import httpx


class TodoistPluginClient:
    def __init__(
        self,
        api_token: str,
        http_client: httpx.Client | Any | None = None,
        base_url: str = "https://api.todoist.com/rest/v2",
    ) -> None:
        self._api_token = api_token
        self._http = http_client or httpx.Client(timeout=30.0)
        self._base_url = base_url.rstrip("/")

    def list_tasks(
        self,
        *,
        project_id: str | None = None,
        label: str | None = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, str] = {}
        if project_id:
            params["project_id"] = project_id
        if label:
            params["label"] = label
        response = self._http.get(
            f"{self._base_url}/tasks",
            headers=self._auth_headers(),
            params=params or None,
        )
        self._raise_for_status(response)
        items = response.json()
        return cast(list[dict[str, Any]], items)

    def create_task(
        self,
        *,
        content: str,
        due: str | None = None,
        priority: int = 1,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"content": content, "priority": priority}
        if due:
            payload["due_string"] = due
        response = self._http.post(
            f"{self._base_url}/tasks",
            headers=self._auth_headers(),
            json=payload,
        )
        self._raise_for_status(response)
        return cast(dict[str, Any], response.json())

    def complete_task(self, task_id: str) -> bool:
        response = self._http.post(
            f"{self._base_url}/tasks/{task_id}/close",
            headers=self._auth_headers(),
        )
        self._raise_for_status(response)
        return response.status_code in {200, 204}

    def list_projects(self) -> list[dict[str, Any]]:
        response = self._http.get(
            f"{self._base_url}/projects",
            headers=self._auth_headers(),
        )
        self._raise_for_status(response)
        return cast(list[dict[str, Any]], response.json())

    def list_labels(self) -> list[dict[str, Any]]:
        response = self._http.get(
            f"{self._base_url}/labels",
            headers=self._auth_headers(),
        )
        self._raise_for_status(response)
        return cast(list[dict[str, Any]], response.json())

    def _auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._api_token}"}

    def _raise_for_status(self, response: httpx.Response) -> None:
        if response.status_code >= 400:
            raise ValueError(f"Todoist API error: {response.status_code} {response.text}")
