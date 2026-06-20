# Stage 1: Build frontend SPA
FROM node:20-alpine AS frontend-builder

WORKDIR /workspace

# Copy frontend source
COPY frontend/ ./frontend/

# Install and build
WORKDIR /workspace/frontend
RUN npm ci --prefer-offline --no-audit
RUN npm run build

# Output: /workspace/frontend/dist with built SPA


# Stage 2: Python runtime with backend + built SPA
FROM python:3.12-slim

# Set labels
LABEL maintainer="Telegram Video-Matic"
LABEL description="Self-hosted Telegram media downloader with Jellyfin/Plex naming"

# Non-root user
RUN groupadd -r tvm && useradd -r -g tvm tvm

# Install system dependencies (minimal for SQLite + aiosqlite)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsqlite3-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY app/ ./app/
COPY migrations/ ./migrations/
COPY plugins/ ./plugins/
COPY alembic.ini .

# Copy built frontend from stage 1 to /app/frontend/dist
# (app/main.py expects STATIC_DIR at ../frontend/dist relative to app/main.py)
COPY --from=frontend-builder /workspace/frontend/dist ./frontend/dist

# Create data and media directories with proper ownership
RUN mkdir -p /data /media && chown -R tvm:tvm /app /data /media

# Switch to non-root user
USER tvm

# Expose FastAPI port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Entrypoint: start FastAPI with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
