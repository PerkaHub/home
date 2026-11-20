FROM python:3.12.12-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.13.1 /uv /usr/local/bin/uv
WORKDIR /app
ENV PYTHONUNBUFFERED=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never

COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

COPY src/ ./src/
RUN uv sync --locked --no-dev --no-editable \
    && useradd --system --user-group --no-create-home app

ARG APP_VERSION=0.8.0
ENV APP_VERSION=${APP_VERSION} APP_ENV=production HOST=0.0.0.0 PATH="/app/.venv/bin:$PATH"
USER app
EXPOSE 8080
CMD ["python", "-m", "domprozrachno"]
