FROM python:3.12-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files and install
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Copy agent source
COPY agent/ ./agent/

# Run uvicorn from repo root; agent/ is a package relative to /app
CMD ["uv", "run", "uvicorn", "agent.main:app", "--host", "0.0.0.0", "--port", "8080"]
