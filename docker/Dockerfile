# syntax=docker/dockerfile:1

# ---------------------------------------------------------------------------
# Stage 1 — build the frontend SPA
# ---------------------------------------------------------------------------
FROM node:24-alpine AS frontend
WORKDIR /build

# Install deps first (cached unless lockfile changes), then build.
COPY frontend/package*.json ./
RUN npm ci --prefer-offline --no-audit --fund=false
COPY frontend/ ./
RUN npm run build
# Output: /build/dist

# ---------------------------------------------------------------------------
# Stage 2 — build Python dependencies into an isolated venv
# Build toolchain lives only here; the runtime image stays slim.
# (cargo/openssl/libffi cover any sdist fallback for cryptography/pydantic-core
#  if a musllinux wheel is unavailable for the target Python.)
# ---------------------------------------------------------------------------
FROM python:3.14-alpine AS pydeps
RUN apk add --no-cache build-base libffi-dev openssl-dev cargo
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ---------------------------------------------------------------------------
# Stage 3 — runtime
# ---------------------------------------------------------------------------
FROM python:3.14-alpine AS runtime
LABEL org.opencontainers.image.title="Telegram Video-Matic" \
      org.opencontainers.image.description="Self-hosted Telegram media downloader with Jellyfin/Plex naming" \
      org.opencontainers.image.source="https://github.com/sgtslaughta/telegram_video-matic"

# Runtime shared libs (cffi loads libffi.so; cryptography's wheel bundles OpenSSL).
# su-exec drops root → PUID:PGID in the entrypoint (Unraid bind-mount ownership).
# libgcc: cryptg's compiled .so links _Unwind_* from libgcc_s.so.1 — without it
# the import fails at runtime and Telethon silently falls back to pure-Python AES.
RUN apk add --no-cache libffi su-exec libgcc

# Bring in the prebuilt virtualenv.
COPY --from=pydeps /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DATABASE_URL="sqlite+aiosqlite:////data/tvm.sqlite" \
    MEDIA_ROOT="/media"

WORKDIR /app
COPY app/ ./app/
COPY migrations/ ./migrations/
COPY plugins/ ./plugins/
COPY alembic.ini .
COPY --from=frontend /build/dist ./frontend/dist

# Data + media volume mountpoints; runtime ownership is set by the entrypoint.
RUN mkdir -p /data /media
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

# Healthcheck via stdlib (no curl in the image).
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/api/health').getcode()==200 else 1)"

# Entrypoint chowns volumes to PUID:PGID and drops root, then runs the app
# (which preflights env/data-dir and emits clear errors, no traceback).
ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "-m", "app"]
