FROM python:3.12-slim

# uv resolves and installs far faster than pip, which matters on every deploy.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# Dependencies first, so a code change does not invalidate the install layer.
COPY pyproject.toml uv.lock* ./
RUN uv sync --no-dev --frozen --no-install-project 2>/dev/null \
    || uv sync --no-dev --no-install-project

COPY . .
RUN uv sync --no-dev 2>/dev/null || true

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

# Migrations run on start rather than at build: the database is not reachable
# while the image is being built, and a container that boots against an
# unmigrated schema fails in a much more confusing way.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
