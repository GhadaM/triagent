"""Tests for typed settings."""

import pytest
from pydantic import ValidationError

from triagent.config import Settings


def test_defaults_target_kubernetes() -> None:
    settings = Settings(_env_file=None)
    assert settings.github_repo == "kubernetes/kubernetes"


def test_secrets_are_masked(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TRIAGENT_GROQ_API_KEY", "super-secret")
    settings = Settings(_env_file=None)

    assert settings.groq_api_key is not None
    assert "super-secret" not in repr(settings)
    assert settings.groq_api_key.get_secret_value() == "super-secret"


def test_invalid_repo_name_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, github_repo="not a repo")
