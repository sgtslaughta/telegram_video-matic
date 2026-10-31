"""Debounced Jellyfin library refresh after imports and prunes."""
from datetime import datetime, timedelta, timezone
from typing import Awaitable, Callable, Optional

from app.utils.log import log

QUIET = timedelta(seconds=60)


async def httpx_post(url: str, headers: dict) -> None:
    import httpx
    async with httpx.AsyncClient(timeout=15) as c:
        (await c.post(url, headers=headers)).raise_for_status()


class JellyfinRefresher:
    """Marks dirty on download success / prune events; refreshes once the
    burst has been quiet for 60s (8 matches in a round = 1 refresh)."""

    def __init__(self, post: Callable[[str, dict], Awaitable[None]] = httpx_post,
                 clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc)):
        self.post = post
        self.clock = clock
        self.url = ""
        self.api_key = ""
        self.library_id = ""
        self._dirty_at: Optional[datetime] = None

    async def load(self, session_factory) -> None:
        import json
        from app.crypto import decrypt
        from app.db.repositories import settings
        async with session_factory() as s:
            cfg = json.loads(await settings.get(s, "jellyfin", default="{}") or "{}")
        self.url = cfg.get("url", "")
        self.library_id = cfg.get("library_id", "")
        try:
            self.api_key = decrypt(cfg["api_key_enc"]) if cfg.get("api_key_enc") else ""
        except Exception as e:
            log(f"Jellyfin API key undecryptable: {e}", "WARN")
            self.api_key = ""

    def on_event(self, ev) -> None:
        level, kind = str(ev.level), ev.kind
        if (kind == "download" and level == "success") or kind == "prune":
            self._dirty_at = self.clock()

    def endpoint(self) -> str:
        base = self.url.rstrip("/")
        if self.library_id:
            return f"{base}/Items/{self.library_id}/Refresh?Recursive=true"
        return f"{base}/Library/Refresh"

    async def refresh(self) -> None:
        await self.post(self.endpoint(), {"X-Emby-Token": self.api_key})

    async def tick(self) -> None:
        if self._dirty_at is None or not (self.url and self.api_key):
            return
        if self.clock() - self._dirty_at < QUIET:
            return
        self._dirty_at = None
        try:
            await self.refresh()
        except Exception as e:
            log(f"Jellyfin refresh failed: {e}", "WARN")
