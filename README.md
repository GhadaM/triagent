# Triagent

LLM-powered triage for GitHub issues: label prediction, duplicate detection and drafted responses, engineered as a production ML system.

> AI Engineering capstone

## Quickstart

Requirements: Python 3.12, [uv](https://docs.astral.sh/uv/), Docker.

```bash
cp .env.example .env             # add your GitHub token
uv sync                          # install dependencies
uv run pre-commit install        # install git hooks
uv run pytest                    # run the tests
uv run uvicorn triagent.api.main:app --reload   # API docs at http://localhost:8000/docs
```
