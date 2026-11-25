"""Shared pytest fixtures."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from triagent.api.main import app
from triagent.config import Settings, get_settings


@pytest.fixture
def settings() -> Settings:
    """Settings for tests: never reads a real .env file."""
    return Settings(_env_file=None, env="ci")


@pytest.fixture
def client(settings: Settings) -> Iterator[TestClient]:
    """API test client with test settings injected."""
    app.dependency_overrides[get_settings] = lambda: settings
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
