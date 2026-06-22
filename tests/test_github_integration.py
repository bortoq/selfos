from __future__ import annotations

import httpx

from selfos.plugins.github_integration import GitHubPlugin


def test_github_notifications_issues_prs_and_search() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if request.method == "GET" and path.endswith("/notifications"):
            return httpx.Response(
                200,
                json=[
                    {
                        "id": "n1",
                        "repository": {"full_name": "bortoq/selfos"},
                        "subject": {"title": "Review PR", "type": "PullRequest"},
                        "reason": "mention",
                        "url": "https://api.github.test/n1",
                    }
                ],
            )
        if request.method == "GET" and path.endswith("/repos/bortoq/selfos/issues"):
            return httpx.Response(
                200,
                json=[
                    {
                        "id": 1,
                        "title": "Bug",
                        "state": "open",
                        "html_url": "https://github.com/bortoq/selfos/issues/1",
                    }
                ],
            )
        if request.method == "GET" and path.endswith("/repos/bortoq/selfos/pulls"):
            return httpx.Response(
                200,
                json=[
                    {
                        "id": 2,
                        "title": "PR",
                        "state": "open",
                        "html_url": "https://github.com/bortoq/selfos/pull/2",
                    }
                ],
            )
        if request.method == "GET" and path.endswith("/search/issues"):
            return httpx.Response(
                200,
                json={
                    "items": [
                        {
                            "id": 3,
                            "title": "Search result",
                            "state": "open",
                            "html_url": "https://github.com/bortoq/selfos/issues/3",
                        }
                    ]
                },
            )
        raise AssertionError(f"Unexpected request: {request.method} {request.url}")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    plugin = GitHubPlugin(api_token="github-token", http_client=client, base_url="https://api.github.com")

    notifications = plugin.notifications()
    issues = plugin.issues("bortoq/selfos")
    prs = plugin.pull_requests("bortoq/selfos")
    search = plugin.search("repo:bortoq/selfos is:open")

    assert notifications[0]["title"] == "Review PR"
    assert issues[0]["title"] == "Bug"
    assert prs[0]["title"] == "PR"
    assert search[0]["title"] == "Search result"
