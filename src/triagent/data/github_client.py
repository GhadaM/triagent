"""Typed client for fetching issues from the GitHub REST API."""

from collections.abc import Iterator
from datetime import datetime
from types import TracebackType
from typing import Any, Self

import httpx2
from pydantic import BaseModel, field_validator

API_URL = "https://api.github.com"


class RateLimitError(RuntimeError):
    """Raised when GitHub's rate limit is exhausted. Retry after `reset_at` (Unix time)."""

    def __init__(self, reset_at: int) -> None:
        super().__init__(f"GitHub rate limit exhausted, resets at Unix time {reset_at}")
        self.reset_at = reset_at


class RawIssue(BaseModel):
    """The fields Triagent keeps from a GitHub issue. Usernames are deliberately dropped."""

    number: int
    title: str
    body: str | None = None
    state: str
    state_reason: str | None = None
    labels: list[str]
    comments: int
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None = None

    @field_validator("labels", mode="before")
    @classmethod
    def _label_names(cls, value: list[Any]) -> list[str]:
        """GitHub returns label objects; keep only their names."""
        return [label["name"] if isinstance(label, dict) else str(label) for label in value]


class GitHubClient:
    """Fetches issues for one repository, newest first, following pagination."""

    def __init__(
        self,
        repo: str,
        token: str | None = None,
        *,
        transport: httpx2.BaseTransport | None = None,
        timeout: float = 30.0,
    ) -> None:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "triagent",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self.repo = repo
        self._client = httpx2.Client(
            base_url=API_URL, headers=headers, timeout=timeout, transport=transport
        )

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()

    def iter_issues(
        self,
        *,
        state: str = "all",
        created_after: datetime | None = None,
        max_issues: int | None = None,
    ) -> Iterator[RawIssue]:
        """Yield issues (never pull requests), newest first.

        Stops at the first issue created before `created_after`, or after `max_issues`.
        """
        url: str | None = f"/repos/{self.repo}/issues"
        params: dict[str, str | int] | None = {
            "state": state,
            "sort": "created",
            "direction": "desc",
            "per_page": 100,
        }
        yielded = 0
        while url:
            response = self._get(url, params)
            params = None  # the "next" link already carries the query string
            for item in response.json():
                if "pull_request" in item:  # the issues endpoint also returns PRs
                    continue
                issue = RawIssue.model_validate(item)
                if created_after and issue.created_at < created_after:
                    return
                yield issue
                yielded += 1
                if max_issues is not None and yielded >= max_issues:
                    return
            url = response.links.get("next", {}).get("url")

    def _get(self, url: str, params: dict[str, str | int] | None) -> httpx2.Response:
        response = self._client.get(url, params=params)
        rate_limited = response.status_code in (403, 429)
        if rate_limited and response.headers.get("x-ratelimit-remaining") == "0":
            raise RateLimitError(reset_at=int(response.headers.get("x-ratelimit-reset", "0")))
        response.raise_for_status()
        return response
