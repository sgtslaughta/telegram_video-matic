"""Retention: decide what to delete, then delete it safely.

Rules:
- Age counts from the content's date (content_date, e.g. the fixture date),
  falling back to date_posted — never from when the file was downloaded.
- A subscription's retention_days replaces the global value for its items.
- Items or subscriptions pinned with `keep` are never pruned.
- Only tracked DOWNLOADED items are touched; untracked files never are.
- More than `cap` deletions in one run pauses and asks for confirmation.
"""
import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import EventLevel, MediaItem, MediaStatus, Subscription
from app.db.repositories import events, settings

PRUNE_CAP = 50


@dataclass
class Prune:
    item: MediaItem
    reason: str  # age | quota | disk


def _utc(dt: Optional[datetime]) -> Optional[datetime]:
    return dt.replace(tzinfo=timezone.utc) if dt is not None and dt.tzinfo is None else dt


def age_date(item: MediaItem) -> datetime:
    return _utc(item.content_date or item.date_posted)


async def _int_setting(s: AsyncSession, key: str, default: int) -> int:
    try:
        return int(await settings.get(s, key, default=str(default)) or default)
    except (TypeError, ValueError):
        return default


async def plan(s: AsyncSession, now: datetime, *, disk_used: int, disk_total: int,
               global_days: Optional[int] = None, disk_pct_limit: Optional[int] = None) -> list[Prune]:
    """Everything that should be deleted at `now`, oldest content first per rule."""
    if global_days is None:
        global_days = await _int_setting(s, "retention_days", 90)
    if disk_pct_limit is None:
        disk_pct_limit = await _int_setting(s, "retention_disk_pct", 80)
    subs = {sub.id: sub for sub in (await s.execute(select(Subscription))).scalars()}
    items = (await s.execute(
        select(MediaItem).where(MediaItem.status == MediaStatus.DOWNLOADED)
    )).scalars().all()
    candidates = sorted(
        (i for i in items if not i.keep and not getattr(subs.get(i.subscription_id), "keep", False)),
        key=age_date,
    )
    chosen: dict[int, Prune] = {}

    for i in candidates:
        sub = subs.get(i.subscription_id)
        days = (sub.retention_days if sub and sub.retention_days else None) or global_days
        if days and age_date(i) < now - timedelta(days=days):
            chosen[i.id] = Prune(i, "age")

    for sub in subs.values():
        if not sub.max_total_gb:
            continue
        mine = [i for i in candidates if i.subscription_id == sub.id and i.id not in chosen]
        total = sum(i.size_bytes or 0 for i in mine)
        for i in mine:
            if total <= sub.max_total_gb * 1024 ** 3:
                break
            chosen[i.id] = Prune(i, "quota")
            total -= i.size_bytes or 0

    if disk_total and disk_pct_limit:
        used = disk_used - sum(p.item.size_bytes or 0 for p in chosen.values())
        for i in candidates:
            if 100 * used / disk_total < disk_pct_limit:
                break
            if i.id in chosen:
                continue
            chosen[i.id] = Prune(i, "disk")
            used -= i.size_bytes or 0

    return list(chosen.values())


_REASON_TEXT = {"age": "older than the retention period", "quota": "over the subscription's size limit",
                "disk": "disk usage above the limit"}


async def apply(s: AsyncSession, prunes: list[Prune], *, confirmed: bool = False,
                cap: int = PRUNE_CAP) -> dict:
    """Delete files and mark items PRUNED. Over `cap` → pause unless confirmed."""
    if not prunes:
        return {"pruned": 0, "paused": False}
    if len(prunes) > cap and not confirmed:
        gb = sum(p.item.size_bytes or 0 for p in prunes) / 1e9
        await settings.set(s, "prune_paused", json.dumps({"count": len(prunes), "gb": round(gb, 1)}))
        await events.add(s, level=EventLevel.WARNING, kind="prune",
                         message=f"Cleanup paused: {len(prunes)} files ({gb:.1f} GB) would be deleted. "
                                 "Review and confirm in Storage.")
        return {"pruned": 0, "paused": True}
    for p in prunes:
        if p.item.local_path:
            Path(p.item.local_path).unlink(missing_ok=True)
        p.item.local_path = None
        p.item.status = MediaStatus.PRUNED
        await events.add(s, level=EventLevel.INFO, kind="prune", media_id=p.item.id,
                         subscription_id=p.item.subscription_id,
                         message=f"Deleted ({_REASON_TEXT[p.reason]})")
    await settings.set(s, "prune_paused", "")
    await s.commit()
    return {"pruned": len(prunes), "paused": False}


def disk(media_root: str) -> tuple[int, int]:
    try:
        u = shutil.disk_usage(media_root)
        return u.used, u.total
    except OSError:
        return 0, 0


async def run(s: AsyncSession, media_root: str, *, confirmed: bool = False) -> dict:
    used, total = disk(media_root)
    return await apply(s, await plan(s, datetime.now(timezone.utc), disk_used=used, disk_total=total),
                       confirmed=confirmed)


async def preview(s: AsyncSession, now: datetime, days: int = 7, media_root: str = "") -> dict:
    """What age/quota rules will delete within `days` (disk pressure excluded: unpredictable)."""
    future = await plan(s, now + timedelta(days=days), disk_used=0, disk_total=0)
    items = sorted(future, key=lambda p: age_date(p.item))
    return {
        "days": days,
        "count": len(items),
        "bytes": sum(p.item.size_bytes or 0 for p in items),
        "items": [{"id": p.item.id, "file_name": p.item.file_name, "reason": p.reason,
                   "size_bytes": p.item.size_bytes, "content_date": age_date(p.item).isoformat()}
                  for p in items],
    }
