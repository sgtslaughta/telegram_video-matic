"""Overview + "since your last visit" summary for the dashboard and welcome splash."""
import json
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_app_auth
from app.db.models import Channel, MediaItem, MediaStatus, PollStat, Subscription, Topic
from app.db.repositories import settings
from app.sync import pulse

router = APIRouter(prefix="/api", tags=["overview"], dependencies=[Depends(require_app_auth)])

SPLASH_AFTER = timedelta(hours=6)


async def _scalar(db, sql: str, **params) -> int:
    """Count from an optional (plugin-owned) table; 0 if it doesn't exist."""
    try:
        return int((await db.execute(text(sql), params)).scalar() or 0)
    except Exception:
        await db.rollback()
        return 0


async def _rugby_titles(db, ids: list[int]) -> dict[int, tuple[str, str]]:
    if not ids:
        return {}
    try:
        rows = (await db.execute(text(
            "SELECT m.media_id, m.home_name, m.away_name, m.round, l.name FROM rugby_matches m "
            "LEFT JOIN rugby_leagues l ON l.id = m.league_id "
            f"WHERE m.status IN ('auto','confirmed') AND m.media_id IN ({','.join(str(int(i)) for i in ids)})"
        ))).all()
    except Exception:
        await db.rollback()
        return {}
    out = {}
    for mid, home, away, rnd, league in rows:
        if home and away:
            sub = ", ".join(x for x in (league, f"round {rnd}" if rnd else None) if x)
            out[mid] = (f"{home} vs {away}", sub)
    return out


async def _arrivals(db, since: datetime, limit: int) -> list[dict]:
    items = (await db.execute(
        select(MediaItem).where(MediaItem.status == MediaStatus.DOWNLOADED, MediaItem.downloaded_at >= since)
        .order_by(MediaItem.downloaded_at.desc()).limit(limit)
    )).scalars().all()
    titles = await _rugby_titles(db, [i.id for i in items])
    return [{
        "id": i.id,
        "title": titles.get(i.id, (i.file_name or (i.caption or "")[:80] or f"Message {i.tg_msg_id}", None))[0],
        "subtitle": titles.get(i.id, (None, None))[1],
        "size_bytes": i.size_bytes, "duration_sec": i.duration_sec,
        "at": i.downloaded_at.isoformat() if i.downloaded_at else None,
        "has_thumb": bool(i.thumb_b64),
    } for i in items]


async def _wanted_count(request) -> int:
    """Real Wanted count from the rugby plugin (0 if it's not loaded)."""
    try:
        from app.rugby.wanted import WantedService
        host = getattr(request.app.state, "plugin_host", None)
        entry = next((e for e in getattr(host, "entries", []) if e.name == "rugby" and e.enabled), None)
        if entry is None:
            return 0
        return sum(1 for w in await WantedService(entry.instance.ctx).list_wanted() if w["state"] != "not_found")
    except Exception:
        return 0


async def _attention(db, request=None) -> dict:
    failed = (await db.execute(select(func.count()).where(MediaItem.status == MediaStatus.FAILED))).scalar() or 0
    paused = await settings.get(db, "prune_paused", default="")
    return {
        "failed": failed,
        "needs_review": await _scalar(db, "SELECT count(*) FROM rugby_matches WHERE status = 'needs_review'"),
        "wanted": await _wanted_count(request) if request is not None else 0,
        "cleanup_paused": json.loads(paused) if paused else None,
    }


async def _totals(db, since: datetime) -> dict:
    n, b = (await db.execute(select(func.count(), func.coalesce(func.sum(MediaItem.size_bytes), 0)).where(
        MediaItem.status == MediaStatus.DOWNLOADED, MediaItem.downloaded_at >= since))).one()
    return {"downloaded": n, "bytes": b}


async def _hourly_downloads(db, hours: int = 24) -> list[dict]:
    """Downloads + bytes per hour (oldest first) for the stat sparklines."""
    end = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    start = end - timedelta(hours=hours - 1)
    rows = (await db.execute(select(MediaItem.downloaded_at, MediaItem.size_bytes).where(
        MediaItem.status.in_((MediaStatus.DOWNLOADED, MediaStatus.PRUNED)), MediaItem.downloaded_at >= start))).all()
    cells = [{"t": (start + timedelta(hours=i)).isoformat(), "count": 0, "bytes": 0} for i in range(hours)]
    for at, size in rows:
        i = int((at - start).total_seconds() // 3600)
        if 0 <= i < hours:
            cells[i]["count"] += 1
            cells[i]["bytes"] += size or 0
    return cells


def _tg_status(request: Request) -> tuple[str, str | None]:
    st = request.app.state
    client = getattr(getattr(st, "tg_service", None), "client", None)
    eng = getattr(st, "engine", None)
    last = getattr(eng, "last_ok_poll_at", None)
    status = "unconfigured" if client is None else ("connected" if client.is_connected() else "disconnected")
    return status, last.isoformat() if last else None


@router.get("/overview")
async def overview(request: Request, hours: int = Query(24, ge=1, le=192), db: AsyncSession = Depends(get_db)):
    subs = (await db.execute(select(Subscription).order_by(Subscription.id))).scalars().all()
    chans = {c.id: c.title for c in (await db.execute(select(Channel))).scalars()}
    topics = {t.id: t.title for t in (await db.execute(select(Topic))).scalars()}
    series = await pulse.series(db, [s.id for s in subs], hours=hours)
    now = datetime.now(timezone.utc)
    status, last = _tg_status(request)
    return {
        "telegram": {"status": status, "last_ok_poll_at": last},
        "subscriptions": [{
            "id": s.id,
            "name": s.name or topics.get(s.topic_id) or chans.get(s.channel_id) or f"Subscription {s.id}",
            "live": (s.check_frequency or "") == "realtime", "enabled": s.enabled,
            "last_checked_at": s.last_checked_at.isoformat() if s.last_checked_at else None,
            "pulse": series[s.id],
        } for s in subs],
        "recent": await _arrivals(db, now - timedelta(days=30), 8),
        "attention": await _attention(db, request),
        "last_24h": {**await _totals(db, now - timedelta(hours=24)), "series": await _hourly_downloads(db)},
    }


def _incidents(rows, now: datetime) -> list[dict]:
    """Merge consecutive hours with 'down' polls into outage spans."""
    hours = sorted({(r.hour if r.hour.tzinfo else r.hour.replace(tzinfo=timezone.utc)) for r in rows if r.down})
    spans: list[list[datetime]] = []
    for h in hours:
        if spans and h - spans[-1][1] <= timedelta(hours=1):
            spans[-1][1] = h
        else:
            spans.append([h, h])
    current = now.replace(minute=0, second=0, microsecond=0)
    out = []
    for start, end in spans:
        ongoing = end >= current - timedelta(hours=1)
        out.append({"kind": "telegram_down", "started": start.isoformat(),
                    "ended": None if ongoing else (end + timedelta(hours=1)).isoformat(),
                    "hours": int((end - start).total_seconds() // 3600) + 1})
    return out


@router.get("/summary")
async def summary(request: Request, db: AsyncSession = Depends(get_db)):
    """What happened since the last visit; `show` is false if <6h or nothing happened."""
    now = datetime.now(timezone.utc)
    raw = await settings.get(db, "last_visit_at", default="")
    since = datetime.fromisoformat(raw) if raw else now - timedelta(days=7)
    stats = await _totals(db, since)
    arrivals = await _arrivals(db, since, 48)
    groups: dict[str, list] = {}
    for a in arrivals:
        groups.setdefault(a["subtitle"] or "Other videos", []).append(a)
    rows = (await db.execute(select(PollStat).where(PollStat.hour >= since - timedelta(hours=1)))).scalars().all()
    incidents = _incidents(rows, now)
    attention = await _attention(db, request)
    eventful = bool(arrivals or incidents or attention["failed"] or attention["cleanup_paused"])
    return {
        "since": since.isoformat(),
        "show": bool(raw) and now - since >= SPLASH_AFTER and eventful,
        "incidents": incidents,
        "arrivals": [{"group": g, "items": items} for g, items in groups.items()],
        "attention": attention,
        "stats": stats,
    }


@router.post("/summary/seen")
async def seen(db: AsyncSession = Depends(get_db)):
    now = datetime.now(timezone.utc).isoformat()
    await settings.set(db, "last_visit_at", now)
    return {"last_visit_at": now}
