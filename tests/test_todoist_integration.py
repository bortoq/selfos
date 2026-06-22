from __future__ import annotations

import httpx

from selfos.plugins.todoist_integration import TodoistPluginClient


def test_todoist_list_create_complete_projects_and_labels() -> None:
    calls: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append((request.method, str(request.url)))
        if request.method == "GET" and request.url.path.endswith("/tasks"):
            return httpx.Response(
                200,
                json=[{"id": "t1", "content": "Ship Phase 5c", "priority": 4, "labels": []}],
            )
        if request.method == "POST" and request.url.path.endswith("/tasks"):
            return httpx.Response(200, json={"id": "t2", "content": "Write docs"})
        if request.method == "POST" and request.url.path.endswith("/tasks/t1/close"):
            return httpx.Response(204)
        if request.method == "GET" and request.url.path.endswith("/projects"):
            return httpx.Response(200, json=[{"id": "p1", "name": "Self OS"}])
        if request.method == "GET" and request.url.path.endswith("/labels"):
            return httpx.Response(200, json=[{"name": "urgent"}])
        raise AssertionError(f"Unexpected request: {request.method} {request.url}")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    plugin = TodoistPluginClient(api_token="todoist-token", http_client=client, base_url="https://api.todoist.com/rest/v2")

    tasks = plugin.list_tasks()
    created = plugin.create_task(content="Write docs")
    completed = plugin.complete_task("t1")
    projects = plugin.list_projects()
    labels = plugin.list_labels()

    assert tasks[0]["content"] == "Ship Phase 5c"
    assert created["id"] == "t2"
    assert completed is True
    assert projects == [{"id": "p1", "name": "Self OS"}]
    assert labels == [{"name": "urgent"}]
    assert any(url.endswith("/tasks/t1/close") for _, url in calls)
