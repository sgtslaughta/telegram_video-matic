# Telegram Video-Matic

Self-hosted Telegram media downloader with automatic channel/topic monitoring,
smart naming for Jellyfin/Plex, retry logic, and disk pruning. One container,
one image, one port.

## Features

- **Telegram integration:** MTProto user session (channel/topic browse, history, comments, reactions).
- **Subscriptions:** Define channels/topics to monitor with filter rules (keyword, media type, date range).
- **Automatic downloads:** Background sync engine polls subscriptions, downloads matching media, retries on failure.
- **Smart naming:** Jellyfin/Plex-friendly folder structure and file naming (rename templates, season/episode detection).
- **Drift reconciliation:** Detect and recover from missed messages due to Telegram timeline limits.
- **Pruning:** Automatic cleanup by age or disk percentage; user-tunable.
- **Web UI:** Real-time dashboard with subscription management, manual download, file browser, and settings.
- **Plugin framework:** Hook-based extensibility for metadata providers and post-download actions.

## Quick Start

### Prerequisites

- Docker and Docker Compose
- ~2 GB disk for app + database
- Additional disk for `/media` (depends on download volume)

### Installation

1. **Clone and navigate:**
   ```bash
   git clone https://github.com/your-username/telegram-video-matic.git
   cd telegram-video-matic
   ```

2. **Create environment file:**
   ```bash
   cp .env.example .env
   ```
   Edit `.env`:
   - Set `TVM_SECRET_KEY` to a strong random value:
     ```bash
     python -c "import secrets; print(secrets.token_urlsafe(32))"
     ```
   - (Optional) Set `TVM_APP_PASSWORD` for web UI login.
   - (Optional) Adjust `POLL_INTERVAL_SEC`, `MAX_CONCURRENT_DOWNLOADS`, `TZ`.

3. **Start the app:**
   ```bash
   docker-compose up -d
   ```

4. **First run — Telegram login:**
   - Open http://localhost:8000 in your browser.
   - Follow the "Connect Telegram" wizard:
     - Provide your phone number.
     - Enter the code Telegram sends.
     - Enter password if 2FA is enabled.
   - Session is encrypted with `TVM_SECRET_KEY` and stored in `/data/tvm.sqlite`.

5. **Add subscriptions:**
   - Dashboard → Subscriptions tab.
   - Click "Add Subscription," select channel/topic.
   - Define rules: filter keywords, media types, date range.
   - Toggle auto-download on; sync engine starts polling.

### Volumes

| Mount | Purpose | Example |
|---|---|---|
| `/data` | SQLite database + Telethon session artifacts | `./data:/data` |
| `/media` | Downloaded files (user maps to Jellyfin/Plex library) | `./media:/media` |

### Environment Variables

| Variable | Default | Notes |
|---|---|---|
| `TVM_SECRET_KEY` | *(required)* | Encryption key for Telegram credentials. Generate with `python -c "import secrets; print(secrets.token_urlsafe(32))"`. |
| `TVM_APP_PASSWORD` | *(unset)* | Web UI password. If unset, app is open on LAN (not recommended for untrusted networks). |
| `DATABASE_URL` | `sqlite+aiosqlite:////data/tvm.sqlite` | SQLite connection string. Change only if you know what you're doing. |
| `MEDIA_ROOT` | `/media` | Media download root. Usually matches the `/media` volume mount. |
| `POLL_INTERVAL_SEC` | `300` | Default poll cadence (seconds). Runtime-tunable via Settings. |
| `MAX_CONCURRENT_DOWNLOADS` | `3` | Max parallel downloads. Runtime-tunable via Settings. |
| `TZ` | `UTC` | Timezone for schedule-day evaluation. Examples: `America/New_York`, `Europe/London`. |
| `LOG_LEVEL` | `INFO` | Logging level. Options: `DEBUG`, `INFO`, `WARNING`, `ERROR`. |

### Stopping and Logs

```bash
# View logs
docker-compose logs -f tvm

# Stop the app
docker-compose stop

# Restart
docker-compose restart

# Full teardown (keep /data and /media volumes)
docker-compose down
```

## Unraid Installation

1. **Add Community-Apps source:**
   - Apps → App Store → Community-Apps.
   - Click the search icon, paste repo URL (if configured).
   - Search "telegram-video-matic".

2. **Install:**
   - Click "Install."
   - Fill in:
     - **Host path for `/data`:** (e.g., `/mnt/user/appdata/telegram-video-matic`)
     - **Host path for `/media`:** (e.g., `/mnt/user/media`)
     - **TVM_SECRET_KEY:** (required; generate as above)
     - **TVM_APP_PASSWORD:** (optional)
     - **Other env vars:** (poll interval, concurrency, timezone)
   - Click "Apply."

3. **WebUI:**
   - Docker tab → telegram-video-matic → "WebUI" button (or http://your-unraid-ip:8000).
   - Follow first-run Telegram login (see Quick Start above).

## Architecture

```
React SPA (built to static/)
       ↓ REST + WebSocket
  FastAPI app (uvicorn)
  ├─ Telegram service (Telethon user session)
  ├─ Sync engine (background asyncio task)
  │  ├─ Poller (fetch new messages)
  │  ├─ Downloader (concurrent media DL)
  │  ├─ Retryer (exponential backoff)
  │  └─ Pruner (cleanup by age/disk)
  ├─ Plugin host (hook dispatch)
  └─ SQLite database (async, /data volume)
```

**One process, one port (8000).** No nginx, no supervisor, no separate services.

## Development

### Backend Tests

```bash
pip install -r requirements.txt
pytest -q tests/
```

### Frontend Build

```bash
cd frontend
npm ci
npm run build
```

### Local Docker Build

```bash
docker build -t tvm:local .
docker run -e TVM_SECRET_KEY=test-key -p 8000:8000 tvm:local
# Open http://localhost:8000
```

### CI/CD

GitHub Actions pipeline runs on each push:
- Backend: `ruff` lint + `pytest` tests.
- Frontend: `tsc --noEmit` type check + `vitest` tests + `npm run build`.
- Docker: Multi-stage build.
- Smoke test: Container start + health check.

See `.github/workflows/ci.yml` for details.

## Troubleshooting

### Container won't start

- **Check logs:** `docker-compose logs tvm`
- **TVM_SECRET_KEY missing:** Set in `.env` or via `-e` flag.
- **Port 8000 in use:** Change `ports:` in `docker-compose.yml` (e.g., `8001:8000`).

### No Telegram session

- **Delete `/data/tvm.sqlite`** and restart; re-login on the wizard.
- **Check logs** for encryption errors (bad TVM_SECRET_KEY).

### Downloads not starting

- **Verify subscription rules:** Ensure rules match messages in the channel.
- **Check sync engine logs:** Look for poller errors or download queue status via the API.

## Contributing

Contributions welcome! Please:
1. Fork the repo.
2. Create a branch for your feature/bugfix.
3. Ensure tests pass and linting is clean.
4. Submit a PR with a clear description.

## License

[Your license here, e.g., MIT]

## Support

- Issues: https://github.com/your-username/telegram-video-matic/issues
- Discussions: https://github.com/your-username/telegram-video-matic/discussions

---

**Last updated:** 2026-06-20
