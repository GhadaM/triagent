# ---- Build stage: install locked dependencies into a virtualenv ----
FROM python:3.12-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

RUN pip install --no-cache-dir uv

WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --locked --no-dev --no-install-project

COPY src ./src
RUN uv sync --locked --no-dev

# ---- Runtime stage: slim image, non-root user ----
FROM python:3.12-slim AS runtime

RUN useradd --create-home --uid 1000 triagent
WORKDIR /app
COPY --from=builder --chown=triagent:triagent /app /app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

USER triagent
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "triagent.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
