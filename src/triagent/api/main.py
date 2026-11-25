"""FastAPI application entry point."""

from typing import Annotated

from fastapi import Depends, FastAPI

from triagent import __version__
from triagent.api.schemas import HealthResponse
from triagent.config import Settings, get_settings

app = FastAPI(
    title="Triagent",
    version=__version__,
    description="LLM-powered GitHub issue triage.",
)


@app.get("/health", response_model=HealthResponse, tags=["ops"])
def health(settings: Annotated[Settings, Depends(get_settings)]) -> HealthResponse:
    """Liveness probe used by Docker, CI and monitoring."""
    return HealthResponse(status="ok", version=__version__, env=settings.env)
