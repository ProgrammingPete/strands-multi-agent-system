# Dockerfile for Canvalo Backend (FastAPI + Strands Agents)
# Requirements: 1.1, 1.2, 1.4, 1.5

# Use Python 3.13 slim image (matches .python-version)
FROM python:3.13-slim AS base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    # uv configuration
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser

# Set working directory
WORKDIR /app

# Copy dependency files first for better layer caching
COPY pyproject.toml uv.lock* ./

# Install dependencies using uv
RUN uv sync --frozen --no-dev --no-install-project

# Copy application code
COPY backend/ ./backend/
COPY agents/ ./agents/
COPY utils/ ./utils/

# Change ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose the application port (default 8000)
EXPOSE 8000

# Health check endpoint (Requirements 1.4)
# Check /health endpoint responds within 5 seconds
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${API_PORT:-8000}/health || exit 1

# Set default environment variables
ENV API_HOST=0.0.0.0 \
    API_PORT=8000 \
    ENVIRONMENT=production

# Graceful shutdown handling (Requirements 1.5)
# uvicorn handles SIGTERM gracefully by default
STOPSIGNAL SIGTERM

# Run the FastAPI application with uvicorn
CMD ["uv", "run", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
