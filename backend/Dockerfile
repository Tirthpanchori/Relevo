FROM python:3.13-slim-bookworm@sha256:a1165e272e578941b84abc79e4ab38a0305cd12803a5c4247979ac7655f4d641 AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"
WORKDIR /app
RUN pip install --no-cache-dir uv==0.13.1
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --locked --no-dev --no-install-project
COPY backend/ ./
RUN uv sync --locked --no-dev --no-editable \
    && useradd --create-home --uid 10001 relevo \
    && chown relevo:relevo /app

FROM base AS runtime
USER relevo
EXPOSE 8000
CMD ["uvicorn", "relevo.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]

FROM base AS test
RUN uv sync --locked --no-editable
USER relevo
CMD ["pytest"]
