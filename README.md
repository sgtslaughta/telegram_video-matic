# Telegram Video-Matic

Self-hosted Telegram media downloader with automatic channel/topic monitoring,
smart naming for Jellyfin/Plex, retry logic, and disk pruning. **One container,
one image, one port.**

## Features

- **Telegram integration:** MTProto user session — browse channels/topics, history, comments, reactions.
- **Subscriptions:** Monitor channels/topics with filter rules (regex, media type, date range, capture frequency).
- **Automatic downloads:** Background sync engine polls subscriptions, downloads matches, retries on failure, resumes from byte offset.
- **Smart naming:** Jellyfin/Plex folder + file naming (rename templates, season/episode detection, optional `.nfo` metadata).
- **Dedup:** Content-hash detection skips re-downloading renamed files.
- **Pruning:** Cleanup by age or disk quota; per-subscription and server-wide.
- **Web UI:** Real-time dashboard — subscription management, manual download, file browser, settings.

## Quick Start

**Prerequisites:** Docker + Docker Compose v2. A Telegram account with API
credentials from <https://my.telegram.org>.

```bash
git clone https://github.com/sgtslaughta/telegram_video-matic.git
cd telegram_video-matic

cp .env.example .env
# Generate a secret key and paste it into .env as TVM_SECRET_KEY:
python -c "import secrets; print(secrets.token_urlsafe(32))"

docker compose up -d
```

Open <http://localhost:8000>, then:

1. **Connect Telegram** — the wizard asks for your phone, the login code
   Telegram sends, and your 2FA password if enabled. The session is encrypted
   with `TVM_SECRET_KEY` and stored in `/data/tvm.sqlite`.
2. **Add a subscription** — pick a channel/topic, set filter rules and
   capture frequency, enable auto-download. The sync engine starts polling.

That's it. Files land in `./media`, named for your Jellyfin/Plex library.

### Run the pre-built image

Tagged releases publish a multi-arch image (amd64 + arm64) to GHCR — skip the
build:

```bash
docker run -d --name tvm -p 8000:8000 \
  -e TVM_SECRET_KEY="$(python -c 'import secrets;print(secrets.token_urlsafe(32))')" \
  -v "$PWD/data:/data" -v "$PWD/media:/media" \
  ghcr.io/sgtslaughta/telegram_video-matic:latest
```

### Managing the stack

```bash
docker compose logs -f tvm   # tail logs
docker compose restart       # restart
docker compose down          # stop (data/ and media/ are preserved)
```

## Configuration

### Volumes

| Mount | Purpose |
|---|---|
| `/data` | SQLite database + encrypted Telethon session |
| `/media` | Downloaded files (map to your Jellyfin/Plex library) |

### Environment Variables

| Variable | Default | Notes |
|---|---|---|
| `TVM_SECRET_KEY` | *(required)* | Encrypts Telegram credentials. Generate: `python -c "import secrets; print(secrets.token_urlsafe(32))"`. |
| `TVM_APP_PASSWORD` | *(unset)* | Web UI password. Unset = open on LAN (trusted networks only). |
| `POLL_INTERVAL_SEC` | `300` | Default poll cadence. Runtime-tunable in Settings. |
| `MAX_CONCURRENT_DOWNLOADS` | `3` | Max parallel downloads. Runtime-tunable. |
| `RETENTION_DAYS` | `90` | Age-based prune threshold. Runtime-tunable. |
| `TZ` | `UTC` | Timezone for schedule evaluation, e.g. `America/New_York`. |
| `PUID` / `PGID` | `1000` | Host uid/gid that owns `./data` + `./media`; the container runs as this so SQLite can write. Find with `id -u`/`id -g` (Unraid often `99`/`100`). |

`DATABASE_URL` and `MEDIA_ROOT` default to the `/data` and `/media` volumes —
change only if you know what you're doing.

## Unraid

1. Apps → search **telegram-video-matic** (or add the template `unraid/tvm.xml`).
2. Set host paths for `/data` (e.g. `/mnt/user/appdata/telegram-video-matic`)
   and `/media` (e.g. `/mnt/user/media`), and a `TVM_SECRET_KEY`.
3. Apply, then open the WebUI and run the Telegram login (see Quick Start).

## Architecture

```
React SPA (static build)
       ↓ REST + WebSocket
  FastAPI app (uvicorn)
  ├─ Telegram service (Telethon user session)
  ├─ Sync engine (background asyncio tasks)
  │  ├─ Poller       — fetch new messages
  │  ├─ Downloader   — concurrent, resumable media DL
  │  ├─ Retryer      — exponential backoff
  │  └─ Pruner       — cleanup by age / disk quota
  └─ SQLite (async, /data volume)
```

One process, one port (8000). No nginx, no supervisor, no extra services.

## Development

```bash
# Backend (Python 3.14)
pip install -r requirements-dev.txt
ruff check app/          # lint
bandit -r app/ -ll       # security
pytest -q tests/         # tests

# Frontend
cd frontend && npm ci && npm run build

# Local container build
docker build -f docker/Dockerfile -t tvm:local .
docker run -e TVM_SECRET_KEY=test -p 8000:8000 tvm:local
```

### CI/CD

`.github/workflows/ci.yml` runs on every push/PR:

- **Backend** — `ruff` lint, `bandit` SAST, `pytest`.
- **Frontend** — `tsc` type check, `vitest`, `vite build`.
- **Security** — `trivy` filesystem scan (dependencies, Dockerfile misconfig, secrets).
- **Docker** — multi-stage build, `trivy` image scan, container smoke test.
- **Release** — on `v*` tags: build multi-arch and push to GHCR.

Cut a release:

```bash
git tag v1.0.0 && git push origin v1.0.0
```

## Troubleshooting

- **Container won't start:** `docker compose logs tvm`. Usually a missing
  `TVM_SECRET_KEY`.
- **Port 8000 in use:** change the `ports:` mapping in `compose.yml` (e.g. `8001:8000`).
- **"attempt to write to a readonly database":** the container's user can't
  write the bind-mounted `./data`. Set `PUID`/`PGID` in `.env` to the owner of
  `./data` (`ls -n data`), then `docker compose up -d`.
- **Telegram login fails / bad session:** delete `data/tvm.sqlite` and re-run
  the wizard (re-encrypts with current `TVM_SECRET_KEY`).
- **Downloads not starting:** check subscription filter rules actually match
  recent messages; watch the dashboard activity feed for poller errors.

## Support

- Issues: <https://github.com/sgtslaughta/telegram_video-matic/issues>
