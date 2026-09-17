"""Adopt video files already on disk that no Telegram download created.

Each top-level folder becomes a topic under one synthetic "Local Library"
channel; files get negative tg_msg_ids (no real message behind them). Once rows
exist, matching, topic history, rematch and reconcile treat them like any
downloaded item.
"""

import os
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import func, select

from app.db.models import Channel, MediaItem, MediaStatus, Topic
from app.rugby import filing, matcher

VIDEO_EXT = {".mp4", ".mkv", ".avi", ".m4v", ".mov", ".ts", ".webm"}
LOCAL_CHANNEL_TG_ID = -1
_ROOT_FOLDER = "Library"  # topic for files sitting directly in the root


def scan(root: Path, known: set[str]) -> list[Path]:
    """Video files under root that no media row points at (skips .partial)."""
    return sorted(
        p for p in root.rglob("*")
        if p.suffix.lower() in VIDEO_EXT and p.is_file()
        and not any(part.startswith(".") for part in p.relative_to(root).parts)
        and os.path.normpath(p) not in known)


def file_date(path: Path) -> datetime:
    """Date in the filename, else the file's modification time."""
    return (matcher.parse_title_date(path.name.replace("_", " "))
            or datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc))


async def _channel(s) -> Channel:
    ch = (await s.execute(select(Channel).where(
        Channel.tg_id == LOCAL_CHANNEL_TG_ID))).scalar_one_or_none()
    if ch is None:
        ch = Channel(tg_id=LOCAL_CHANNEL_TG_ID, title="Local Library", is_forum=True)
        s.add(ch)
        await s.flush()
    return ch


async def _topic(s, channel_id: int, title: str) -> Topic:
    t = (await s.execute(select(Topic).where(
        Topic.channel_id == channel_id, Topic.title == title))).scalar_one_or_none()
    if t is None:
        low = (await s.execute(select(func.min(Topic.tg_topic_id)).where(
            Topic.channel_id == channel_id))).scalar()
        t = Topic(channel_id=channel_id, title=title,
                  tg_topic_id=min(low or 0, 0) - 1)
        s.add(t)
        await s.flush()
    return t


async def import_library(svc, root: str | None = None, dry_run: bool = False) -> dict:
    """Create media rows for unknown files under root, then match them."""
    base = Path(root or svc.ctx.media_root)
    async with svc.ctx.session() as s:
        known = {os.path.normpath(p) for p in (await s.execute(
            select(MediaItem.local_path).where(MediaItem.local_path.is_not(None))
        )).scalars().all()}
    files = scan(base, known) if base.is_dir() else []
    report = {"dry_run": dry_run, "root": str(base), "found": len(files),
              "files": [str(p.relative_to(base)) for p in files]}
    if dry_run or not files:
        svc.reports["import"] = report
        return report

    new_ids = []
    async with svc.ctx.session() as s:
        ch = await _channel(s)
        low = (await s.execute(select(func.min(MediaItem.tg_msg_id)).where(
            MediaItem.channel_id == ch.id))).scalar()
        next_id = min(low or 0, 0) - 1
        now = datetime.now(timezone.utc)
        for p in files:
            rel = p.relative_to(base).parts
            topic = await _topic(s, ch.id, rel[0] if len(rel) > 1 else _ROOT_FOLDER)
            item = MediaItem(
                channel_id=ch.id, topic_id=topic.id, tg_msg_id=next_id,
                file_name=p.name, size_bytes=p.stat().st_size,
                date_posted=file_date(p), status=MediaStatus.DOWNLOADED,
                local_path=str(p), downloaded_at=now,
                raw={"import_root": str(base)})
            s.add(item)
            await s.flush()
            new_ids.append(item.id)
            next_id -= 1
        await s.commit()

    matched = 0
    for n, mid in enumerate(new_ids):
        filing.progress(svc, "import", n, len(new_ids))
        async with svc.ctx.session() as s:
            item = await s.get(MediaItem, mid)
        try:
            if await svc.match_item(item) == "auto":
                matched += 1
        except Exception as ex:  # noqa: BLE001 - best-effort per item
            await svc.ctx.log("warning", "rugby", f"import match {mid}: {ex}")
    report.update(imported=len(new_ids), matched=matched)
    svc.reports["import"] = report
    await svc.ctx.log("success", "rugby",
                      f"Imported {len(new_ids)} file(s) from {base}; {matched} matched")
    return report
