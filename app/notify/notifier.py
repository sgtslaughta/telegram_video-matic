"""Apprise notifications with spam control.

Events arrive via `on_event` (an events-repo listener) and are batched per
trigger; connection and disk state are sampled by `tick`. Spam control:
- event triggers batch for 2 min into one message per trigger
- state alerts (telegram down, disk low) fire once, then remind at 1h/6h/24h
- telegram down needs 5 min continuous downtime; "reconnected" only if "down" went out
- per-target cap 10/h; overflow folds into the next message as "+N more"
- optional quiet hours hold arrival-type batches; errors pass through
"""
import asyncio
import base64
import json
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Awaitable, Callable, Optional

from app.utils.log import log

TRIGGERS = ("download_complete", "download_failed", "telegram", "unmatched", "disk_low")
_QUIET_HELD = {"download_complete", "unmatched"}
_TITLES = {
    "download_complete": ("Downloaded", "Downloaded {n} videos"),
    "download_failed": ("Download failed", "{n} downloads failed"),
    "unmatched": ("Needs review", "{n} videos need review"),
}
BATCH_WINDOW = timedelta(minutes=2)
DOWN_GRACE = timedelta(minutes=5)
REMINDERS = (timedelta(hours=1), timedelta(hours=6), timedelta(hours=24))
HOURLY_CAP = 10
MAX_LINES = 15


def classify_event(ev) -> Optional[str]:
    """Map an Event row to a notification trigger (or None)."""
    level, kind, msg = str(ev.level), ev.kind, ev.message or ""
    if kind == "download" and level == "success":
        return "download_complete"
    if kind == "download" and level == "error" and msg.startswith("Download failed after"):
        return "download_failed"
    if kind == "rugby" and (msg.startswith("No fixture match") or msg.startswith("Needs review")):
        return "unmatched"
    return None


@dataclass
class Target:
    id: str
    name: str
    url: str  # plaintext in memory only; encrypted at rest
    triggers: list = field(default_factory=list)


@dataclass
class _Alert:
    """A state alert (telegram down / disk low) and its reminder progress."""
    since: datetime
    sent_at: Optional[datetime] = None
    reminders: int = 0


async def apprise_send(url: str, title: str, body: str, attach: Optional[list] = None) -> bool:
    """Send one notification via Apprise (blocking lib → thread)."""
    import apprise

    def _go():
        a = apprise.Apprise()
        a.add(url)
        return a.notify(title=title, body=body, attach=attach or None)

    return bool(await asyncio.to_thread(_go))


class Notifier:
    def __init__(self, session_factory, send: Callable[..., Awaitable[bool]] = apprise_send,
                 clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
                 quiet: Optional[tuple] = None, disk_low_pct: int = 95, tz=None):
        self.session_factory = session_factory
        self.send = send
        self.clock = clock
        self.quiet = quiet  # (start_hour, end_hour) local, or None
        self.disk_low_pct = disk_low_pct
        self.tz = tz  # None = server local time (TZ env)
        self.public_url = ""
        self.targets: list[Target] = []
        self._batches: dict[str, list] = {}  # trigger -> [first_at, [lines]]
        self._sent: dict[str, list] = {}  # target id -> send timestamps (last hour)
        self._overflow: dict[str, int] = {}
        self._down: Optional[_Alert] = None
        self._disk: Optional[_Alert] = None

    # ---- config ------------------------------------------------------------
    async def load(self) -> None:
        """Read targets + options from the settings table."""
        from app.crypto import decrypt
        from app.db.repositories import settings
        async with self.session_factory() as s:
            raw = await settings.get(s, "notify_targets", default="[]")
            opts = json.loads(await settings.get(s, "notify_options", default="{}") or "{}")
        targets = []
        for t in json.loads(raw or "[]"):
            try:
                url = decrypt(t["url_enc"])
            except Exception as e:  # key rotated / corrupt row: skip, don't crash
                log(f"Notify target {t.get('name')} undecryptable: {e}", "WARN")
                continue
            targets.append(Target(id=t["id"], name=t["name"], url=url, triggers=t.get("triggers", [])))
        self.targets = targets
        q = opts.get("quiet") or {}
        self.quiet = (int(q["start"]), int(q["end"])) if q.get("enabled") else None
        self.disk_low_pct = int(opts.get("disk_low_pct", 95))
        self.public_url = (opts.get("public_url") or "").rstrip("/")

    # ---- inputs ------------------------------------------------------------
    def on_event(self, ev) -> None:
        trigger = classify_event(ev)
        if not trigger or not self._wanted(trigger):
            return
        batch = self._batches.setdefault(trigger, [self.clock(), []])
        batch[1].append((ev.message, ev.media_id))

    async def tick(self, connected: Optional[bool], disk_pct: Optional[float]) -> None:
        now = self.clock()
        await self._flush_batches(now)
        if connected is not None:
            await self._telegram(now, connected)
        if disk_pct is not None:
            await self._disk_check(now, disk_pct)

    # ---- internals ---------------------------------------------------------
    def _wanted(self, trigger: str) -> bool:
        return any(trigger in t.triggers for t in self.targets)

    def _in_quiet(self, now: datetime) -> bool:
        if not self.quiet:
            return False
        h = now.astimezone(self.tz).hour
        start, end = self.quiet
        return start <= h < end if start < end else (h >= start or h < end)

    async def _flush_batches(self, now: datetime) -> None:
        for trigger, (first_at, lines) in list(self._batches.items()):
            if now - first_at < BATCH_WINDOW:
                continue
            if trigger in _QUIET_HELD and self._in_quiet(now):
                continue  # held → flushes as one morning digest
            del self._batches[trigger]
            one, many = _TITLES[trigger]
            title = one if len(lines) == 1 else many.format(n=len(lines))
            text, attach = await self._render(lines[:MAX_LINES], with_thumb=trigger == "download_complete")
            if len(lines) > MAX_LINES:
                text += f"\n…and {len(lines) - MAX_LINES} more"
            await self._dispatch(trigger, title, text, now, attach)

    async def _render(self, lines: list, with_thumb: bool) -> tuple[str, Optional[list]]:
        """Lines → body text; enrich with size/duration/link and attach the first thumbnail."""
        items = {}
        ids = [mid for _, mid in lines if mid]
        if ids and self.session_factory is not None:
            try:
                from sqlalchemy import select
                from app.db.models import MediaItem
                async with self.session_factory() as s:
                    rows = (await s.execute(select(MediaItem).where(MediaItem.id.in_(ids)))).scalars().all()
                items = {m.id: m for m in rows}
            except Exception as e:
                log(f"Notify enrich failed: {e}", "WARN")
        out, attach = [], None
        for msg, mid in lines:
            m = items.get(mid)
            bits = [msg]
            if m and m.size_bytes:
                bits.append(f"{m.size_bytes / 1e9:.1f} GB")
            if m and m.duration_sec:
                bits.append(f"{int(m.duration_sec) // 3600}h {int(m.duration_sec) % 3600 // 60:02d}m")
            line = ", ".join(bits)
            if self.public_url and mid:
                line += f"\n  {self.public_url}/media/{mid}"
            out.append(line)
            if with_thumb and attach is None and m and m.thumb_b64:
                try:
                    f = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
                    f.write(base64.b64decode(m.thumb_b64))
                    f.close()
                    attach = [f.name]
                except Exception:  # nosec B110 — thumbnail is optional garnish
                    attach = None
        return "\n".join(out), attach

    async def _telegram(self, now: datetime, connected: bool) -> None:
        if connected:
            if self._down and self._down.sent_at:
                mins = int((now - self._down.since).total_seconds() // 60)
                await self._dispatch("telegram", "Telegram reconnected",
                                     f"Sync resumed after {mins} min offline.", now)
            self._down = None
            return
        if self._down is None:
            self._down = _Alert(since=now)
        if now - self._down.since >= DOWN_GRACE:
            await self._alert(self._down, "telegram", "Telegram disconnected",
                              "Sync is paused; reconnecting automatically.", now)

    async def _disk_check(self, now: datetime, pct: float) -> None:
        if pct < self.disk_low_pct:
            self._disk = None
            return
        if self._disk is None:
            self._disk = _Alert(since=now)
        await self._alert(self._disk, "disk_low", "Disk space low",
                          f"Media disk is {pct:.0f}% full (threshold {self.disk_low_pct}%).", now)

    async def _alert(self, a: _Alert, trigger: str, title: str, body: str, now: datetime) -> None:
        """Send once, then remind at REMINDERS offsets from the first send."""
        if a.sent_at is None:
            a.sent_at = now
            await self._dispatch(trigger, title, body, now)
        elif a.reminders < len(REMINDERS) and now - a.sent_at >= REMINDERS[a.reminders]:
            a.reminders += 1
            await self._dispatch(trigger, f"Still: {title.lower()}", body, now)

    async def _dispatch(self, trigger: str, title: str, body: str, now: datetime,
                        attach: Optional[list] = None) -> None:
        for t in self.targets:
            if trigger not in t.triggers:
                continue
            sent = [ts for ts in self._sent.get(t.id, []) if now - ts < timedelta(hours=1)]
            if len(sent) >= HOURLY_CAP:
                self._overflow[t.id] = self._overflow.get(t.id, 0) + 1
                self._sent[t.id] = sent
                continue
            extra = self._overflow.pop(t.id, 0)
            text = body + (f"\n\n+{extra} more held back by the hourly limit" if extra else "")
            try:
                ok = await self.send(t.url, title, text, attach)
            except Exception as e:
                ok = False
                log(f"Notify {t.name} failed: {e}", "WARN")
            if ok:
                sent.append(now)
            self._sent[t.id] = sent
        for path in attach or []:
            Path(path).unlink(missing_ok=True)


async def run_loop(state, notifier: "Notifier", jellyfin, media_root: str,
                   stop: asyncio.Event, interval: float = 30) -> None:
    """Background loop: sample Telegram + disk state, flush notifications,
    run debounced Jellyfin refresh. Runs until `stop` is set."""
    import shutil
    while not stop.is_set():
        try:
            tg = getattr(state, "tg_service", None)
            client = getattr(tg, "client", None)
            # None = not logged in yet: don't alert on a connection never made.
            has_session = bool(getattr(getattr(tg, "account", None), "session_enc", None))
            connected = client.is_connected() if client and has_session else None
            try:
                u = shutil.disk_usage(media_root)
                disk = 100 * u.used / u.total
            except OSError:
                disk = None
            await notifier.tick(connected, disk)
            await jellyfin.tick()
        except Exception as e:
            log(f"Notifier tick failed: {e}", "WARN")
        try:
            await asyncio.wait_for(stop.wait(), timeout=interval)
        except asyncio.TimeoutError:
            pass


def target_public(t: dict) -> dict:
    """Settings-row target → API shape with the URL masked."""
    scheme = (t.get("scheme") or "").strip()
    return {"id": t["id"], "name": t["name"], "triggers": t.get("triggers", []),
            "url_masked": f"{scheme}://••••" if scheme else "••••"}

