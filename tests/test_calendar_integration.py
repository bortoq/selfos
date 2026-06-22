from __future__ import annotations

import httpx

from selfos.plugins.calendar_integration import GoogleCalendarPlugin


class FakeOAuthManager:
    def get_valid_token(self) -> object:
        return type("Token", (), {"access_token": "calendar-token"})()


def test_calendar_today_and_create_update_delete_and_freebusy() -> None:
    calls: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append((request.method, str(request.url)))
        if request.method == "GET" and request.url.path.endswith("/events"):
            return httpx.Response(
                200,
                json={
                    "items": [
                        {
                            "id": "evt-1",
                            "summary": "Standup",
                            "status": "confirmed",
                            "start": {"dateTime": "2026-06-22T09:00:00Z"},
                            "end": {"dateTime": "2026-06-22T09:30:00Z"},
                            "location": "Meet",
                        }
                    ]
                },
            )
        if request.method == "POST" and request.url.path.endswith("/events"):
            return httpx.Response(200, json={"id": "evt-new"})
        if request.method == "PUT" and request.url.path.endswith("/events/evt-1"):
            return httpx.Response(200, json={"id": "evt-1", "summary": "Updated"})
        if request.method == "DELETE" and request.url.path.endswith("/events/evt-1"):
            return httpx.Response(204)
        if request.method == "POST" and request.url.path.endswith("/freeBusy"):
            return httpx.Response(200, json={"calendars": {"primary": {"busy": []}}})
        raise AssertionError(f"Unexpected request: {request.method} {request.url}")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    plugin = GoogleCalendarPlugin(
        oauth_manager=FakeOAuthManager(),
        http_client=client,
        base_url="https://www.googleapis.com",
    )

    events = plugin.today()
    created = plugin.create_event(
        summary="Deep work",
        start="2026-06-22T10:00:00Z",
        end="2026-06-22T11:00:00Z",
    )
    updated = plugin.update_event("evt-1", summary="Updated")
    deleted = plugin.delete_event("evt-1")
    freebusy = plugin.freebusy("2026-06-22T00:00:00Z", "2026-06-23T00:00:00Z")

    assert events[0]["summary"] == "Standup"
    assert created["id"] == "evt-new"
    assert updated["summary"] == "Updated"
    assert deleted is True
    assert freebusy["calendars"]["primary"]["busy"] == []
    assert any("/freeBusy" in url for _, url in calls)
