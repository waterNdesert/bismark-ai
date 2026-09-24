# Use Python 3.12 with uv preinstalled.
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Set working directory
WORKDIR /app
ENV UV_CACHE_DIR=/tmp/uv-cache

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY apps/api/pyproject.toml apps/api/uv.lock ./

# Install dependencies (locked)
RUN uv sync --locked

# Copy the application code
COPY apps/api/app ./app

# Create a non-root user
RUN addgroup --system --gid 1001 appgroup && \
    adduser --system --uid 1001 --ingroup appgroup appuser && \
    mkdir -p "$UV_CACHE_DIR" && \
    chown -R appuser:appgroup "$UV_CACHE_DIR"
USER appuser

# Expose the API port
EXPOSE 8000

# Command to run the application in development
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
