"""Tests for the GitHub client, using a fake transport instead of the real API."""

from datetime import UTC, datetime
from typing import Any

import httpx2
import pytest

from triagent.data.github_client import GitHubClient, RateLimitError


def make_issue(number: int, created: str, **extra: Any) -> dict[str, Any]:
    return {
        "number": number,
        "title": f"Issue {number}",
        "body": "Something is broken",
        "state": "closed",
        "state_reason": "completed",
        "labels": [{"name": "kind/bug"}, {"name": "sig/node"}],
        "comments": 2,
        "created_at": created,
        "updated_at": created,
        "closed_at": created,
        **extra,
    }


def paged_transport(pages: list[list[dict[str, Any]]]) -> httpx2.MockTransport:
    """Serve `pages` one after another, with GitHub-style Link headers."""

    def handler(request: httpx2.Request) -> httpx2.Response:
        page = int(request.url.params.get("page", "1"))
        headers = {}
        if page < len(pages):
            next_url = f"https://api.github.com/repos/o/r/issues?page={page + 1}"
            headers["link"] = f'<{next_url}>; rel="next"'
        return httpx2.Response(200, json=pages[page - 1], headers=headers)

    return httpx2.MockTransport(handler)


def test_follows_pagination_and_skips_pull_requests() -> None:
    pages = [
        [
            make_issue(3, "2026-11-03T00:00:00Z"),
            make_issue(2, "2026-11-02T00:00:00Z", pull_request={}),
        ],
        [make_issue(1, "2026-11-01T00:00:00Z")],
    ]
    with GitHubClient("o/r", transport=paged_transport(pages)) as client:
        issues = list(client.iter_issues())

    assert [issue.number for issue in issues] == [3, 1]
    assert issues[0].labels == ["kind/bug", "sig/node"]


def test_stops_at_created_after() -> None:
    pages = [[make_issue(2, "2026-11-02T00:00:00Z"), make_issue(1, "2026-10-01T00:00:00Z")]]
    cutoff = datetime(2026, 11, 1, tzinfo=UTC)
    with GitHubClient("o/r", transport=paged_transport(pages)) as client:
        issues = list(client.iter_issues(created_after=cutoff))

    assert [issue.number for issue in issues] == [2]


def test_stops_at_max_issues() -> None:
    pages = [[make_issue(n, "2026-11-01T00:00:00Z") for n in range(5, 0, -1)]]
    with GitHubClient("o/r", transport=paged_transport(pages)) as client:
        issues = list(client.iter_issues(max_issues=2))

    assert len(issues) == 2


def test_raises_rate_limit_error_with_reset_time() -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        headers = {"x-ratelimit-remaining": "0", "x-ratelimit-reset": "1800000000"}
        return httpx2.Response(403, headers=headers, json={"message": "rate limited"})

    client = GitHubClient("o/r", transport=httpx2.MockTransport(handler))
    with client, pytest.raises(RateLimitError) as error:
        list(client.iter_issues())

    assert error.value.reset_at == 1800000000


def test_sends_token_as_bearer_header() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx2.Request) -> httpx2.Response:
        seen["auth"] = request.headers.get("authorization", "")
        return httpx2.Response(200, json=[])

    with GitHubClient("o/r", token="abc", transport=httpx2.MockTransport(handler)) as client:
        list(client.iter_issues())

    assert seen["auth"] == "Bearer abc"
