"""Hourly poll outcome counters per subscription (the overview "sync pulse").

One row per (subscription, hour): ~170 rows/sub/week. Kept 8 days."""
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import PollStat

STATES = ("ok", "error", "down")
KEEP = timedelta(days=8)


def _hour(dt: datetime) -> datetime:
    return dt.astimezone(timezone.utc).replace(minute=0, second=0, microsecond=0)


async def record(s: AsyncSession, subscription_id: int, state: str, queued: int = 0,
                 now: Optional[datetime] = None) -> None:
    hour = _hour(now or datetime.now(timezone.utc))
    row = (await s.execute(select(PollStat).where(
        PollStat.subscription_id == subscription_id, PollStat.hour == hour))).scalar_one_or_none()
    if row is None:
        row = PollStat(subscription_id=subscription_id, hour=hour, ok=0, error=0, down=0, queued=0)
        s.add(row)
    setattr(row, state, (getattr(row, state) or 0) + 1)
    row.queued = (row.queued or 0) + queued
    await s.commit()


async def series(s: AsyncSession, sub_ids: list[int], hours: int = 24,
                 now: Optional[datetime] = None) -> dict[int, list[dict]]:
    """Per subscription: `hours` consecutive hourly cells, oldest first, gaps zero-filled."""
    end = _hour(now or datetime.now(timezone.utc))
    start = end - timedelta(hours=hours - 1)
    rows = (await s.execute(select(PollStat).where(
        PollStat.subscription_id.in_(sub_ids), PollStat.hour >= start))).scalars().all()
    by = {}
    for r in rows:
        h = r.hour if r.hour.tzinfo else r.hour.replace(tzinfo=timezone.utc)
        by[(r.subscription_id, h)] = r
    out = {}
    for sid in sub_ids:
        cells = []
        for i in range(hours):
            h = start + timedelta(hours=i)
            r = by.get((sid, h))
            cells.append({"t": h.isoformat(), "ok": r.ok if r else 0, "error": r.error if r else 0,
                          "down": r.down if r else 0, "queued": r.queued if r else 0})
        out[sid] = cells
    return out


async def prune(s: AsyncSession, now: Optional[datetime] = None) -> None:
    await s.execute(delete(PollStat).where(PollStat.hour < _hour(now or datetime.now(timezone.utc)) - KEEP))
    await s.commit()
