"""Fetch a sample of recent issues into a JSONL file for exploration.

Usage: uv run python scripts/fetch_sample.py --days 365 --out data/raw/issues_sample.jsonl
"""

import argparse
from datetime import UTC, datetime, timedelta
from pathlib import Path

from triagent.config import get_settings
from triagent.data.github_client import GitHubClient, RateLimitError


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=int, default=365, help="Only issues created in this window")
    parser.add_argument("--max-issues", type=int, default=None, help="Optional cap")
    parser.add_argument("--out", type=Path, default=Path("data/raw/issues_sample.jsonl"))
    args = parser.parse_args()

    settings = get_settings()
    token = settings.github_token.get_secret_value() if settings.github_token else None
    created_after = datetime.now(UTC) - timedelta(days=args.days)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with GitHubClient(settings.github_repo, token) as client, args.out.open("w") as file:
        issues = client.iter_issues(created_after=created_after, max_issues=args.max_issues)
        try:
            for issue in issues:
                # Written as we go, so a rate-limited run still keeps its data.
                file.write(issue.model_dump_json() + "\n")
                count += 1
                if count % 500 == 0:
                    print(f"  {count} issues so far (latest: {issue.created_at:%Y-%m-%d})")
        except RateLimitError as error:
            reset = datetime.fromtimestamp(error.reset_at, UTC)
            print(f"Rate limit hit after {count} issues; resets at {reset:%H:%M} UTC.")

    print(f"Saved {count} issues from {settings.github_repo} to {args.out}")


if __name__ == "__main__":
    main()
