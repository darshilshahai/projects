# Multi-stage Dockerfile for FastAPI Backend Engine

# --- Stage 1: Builder ---
FROM python:3.12-slim AS builder

WORKDIR /build

# Install system dependencies needed for compiling python extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies into a wheels directory
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# --- Stage 2: Final Runtime ---
FROM python:3.12-slim AS runner

WORKDIR /app

# Install minimal runtime system libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security compliance
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/sh -m appuser

# Copy installed Python site-packages from builder
COPY --from=builder /install /usr/local

# Copy application source code, migration assets, and startup script
COPY app /app/app
COPY alembic /app/alembic
COPY alembic.ini /app/alembic.ini
COPY start.sh /app/start.sh

# Set executable permission and non-root ownership
RUN chmod +x /app/start.sh && \
    chown -R appuser:appgroup /app

# Environment defaults
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

# Switch to non-root user
USER appuser

EXPOSE 8000

# Health check pinging /api/v1/health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Production server command with automatic migration execution
CMD ["/app/start.sh"]
