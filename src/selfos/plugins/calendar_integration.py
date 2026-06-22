from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, cast

import httpx


class GoogleCalendarPlugin:
    def __init__(
        self,
        oauth_manager: Any,
        http_client: httpx.Client | Any | None = None,
        calendar_id: str = "primary",
        base_url: str = "https://www.googleapis.com",
    ) -> None:
        self._oauth_manager = oauth_manager
        self._http = http_client or httpx.Client(timeout=30.0)
        self._calendar_id = calendar_id
        self._base_url = base_url.rstrip("/")

    def list_events(
        self,
        *,
        time_min: str | None = None,
        time_max: str | None = None,
        max_results: int = 10,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {
            "singleEvents": True,
            "orderBy": "startTime",
            "maxResults": max_results,
        }
        if time_min:
            params["timeMin"] = time_min
        if time_max:
            params["timeMax"] = time_max
        payload = self._get(
            f"/calendar/v3/calendars/{self._calendar_id}/events",
            params=params,
        )
        items = payload.get("items", [])
        return [self._normalize_event(item) for item in items if isinstance(item, dict)]

    def today(self) -> list[dict[str, Any]]:
        start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        return self.list_events(time_min=start.isoformat(), time_max=end.isoformat())

    def create_event(
        self,
        *,
        summary: str,
        start: str,
        end: str,
        location: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "summary": summary,
            "start": {"dateTime": start},
            "end": {"dateTime": end},
        }
        if location:
            payload["location"] = location
        result = self._post(
            f"/calendar/v3/calendars/{self._calendar_id}/events",
            json=payload,
        )
        return result

    def update_event(self, event_id: str, **updates: Any) -> dict[str, Any]:
        result = self._put(
            f"/calendar/v3/calendars/{self._calendar_id}/events/{event_id}",
            json=updates,
        )
        return result

    def delete_event(self, event_id: str) -> bool:
        response = self._http.delete(
            f"{self._base_url}/calendar/v3/calendars/{self._calendar_id}/events/{event_id}",
            headers=self._auth_headers(),
        )
        self._raise_for_status(response, "Google Calendar")
        return response.status_code in {200, 204}

    def freebusy(self, time_min: str, time_max: str) -> dict[str, Any]:
        payload = {
            "timeMin": time_min,
            "timeMax": time_max,
            "items": [{"id": self._calendar_id}],
        }
        result = self._post("/calendar/v3/freeBusy", json=payload)
        return result

    def _normalize_event(self, event: dict[str, Any]) -> dict[str, Any]:
        start = event.get("start", {})
        end = event.get("end", {})
        return {
            "id": str(event.get("id", "")),
            "summary": str(event.get("summary", "")),
            "start": str(start.get("dateTime", start.get("date", ""))),
            "end": str(end.get("dateTime", end.get("date", ""))),
            "location": str(event.get("location", "")),
            "status": str(event.get("status", "")),
        }

    def _auth_headers(self) -> dict[str, str]:
        token = self._oauth_manager.get_valid_token()
        return {"Authorization": f"Bearer {token.access_token}"}

    def _get(self, path: str, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
        response = self._http.get(
            f"{self._base_url}{path}",
            headers=self._auth_headers(),
            params=params,
        )
        self._raise_for_status(response, "Google Calendar")
        return cast(dict[str, Any], response.json())

    def _post(self, path: str, *, json: dict[str, Any]) -> dict[str, Any]:
        response = self._http.post(
            f"{self._base_url}{path}",
            headers=self._auth_headers(),
            json=json,
        )
        self._raise_for_status(response, "Google Calendar")
        return cast(dict[str, Any], response.json())

    def _put(self, path: str, *, json: dict[str, Any]) -> dict[str, Any]:
        response = self._http.put(
            f"{self._base_url}{path}",
            headers=self._auth_headers(),
            json=json,
        )
        self._raise_for_status(response, "Google Calendar")
        return cast(dict[str, Any], response.json())

    def _raise_for_status(self, response: httpx.Response, service: str) -> None:
        if response.status_code >= 400:
            raise ValueError(f"{service} API error: {response.status_code} {response.text}")
