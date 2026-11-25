"""Application settings, loaded from environment variables or a .env file."""

from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed configuration. Secrets use SecretStr so they never leak into logs."""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="TRIAGENT_", extra="ignore")

    env: str = Field(default="dev", description="dev, ci or prod")
    log_level: str = "INFO"

    github_repo: str = Field(default="kubernetes/kubernetes", pattern=r"^[\w.-]+/[\w.-]+$")
    github_token: SecretStr | None = None

    database_url: str = "postgresql://triagent:triagent@localhost:5432/triagent"

    groq_api_key: SecretStr | None = None


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (one per process)."""
    return Settings()
