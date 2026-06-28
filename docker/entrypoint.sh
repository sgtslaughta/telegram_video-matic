#!/bin/sh
# Container entrypoint. When started as root (Unraid default), take ownership of
# the bind-mounted volumes as PUID:PGID and drop privileges via su-exec. When
# already non-root (e.g. compose `user:`), just run — perms are the caller's job.
set -e

if [ "$(id -u)" = "0" ]; then
  PUID="${PUID:-1000}"
  PGID="${PGID:-1000}"
  mkdir -p /data /media
  # /data is small (SQLite) — recurse. /media may be huge — top-level only;
  # new files inherit PUID and existing files keep their owners.
  chown -R "$PUID:$PGID" /data 2>/dev/null || true
  chown "$PUID:$PGID" /media 2>/dev/null || true
  exec su-exec "$PUID:$PGID" "$@"
fi

exec "$@"
