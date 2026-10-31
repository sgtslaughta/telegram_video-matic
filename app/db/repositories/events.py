from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.db.models import Event

# ponytail: look back a short window, not an index scan; repeats interleave
# across subs (sub1 err, sub2 err, ...) so "newest row only" isn't enough.
_COLLAPSE_LOOKBACK = 20
_COLLAPSE_WINDOW = timedelta(hours=1)
_COLLAPSE_LEVELS = {"warning", "error"}


async def add(
    session: AsyncSession,
    level: str,
    kind: str,
    message: str,
    subscription_id: int | None = None,
    media_id: int | None = None,
) -> Event:
    """Log an event. Repeated warnings/errors within an hour bump `count` on the
    existing row instead of flooding the feed."""
    if str(level) in _COLLAPSE_LEVELS:
        recent = (await session.execute(
            select(Event).order_by(desc(Event.id)).limit(_COLLAPSE_LOOKBACK)
        )).scalars().all()
        cutoff = datetime.now(timezone.utc) - _COLLAPSE_WINDOW
        for prev in recent:
            seen = prev.updated_at
            if seen is not None and seen.tzinfo is None:
                seen = seen.replace(tzinfo=timezone.utc)
            if (prev.level, prev.kind, prev.subscription_id, prev.media_id, prev.message) == (
                str(level), kind, subscription_id, media_id, message
            ) and seen and seen >= cutoff:
                prev.count = (prev.count or 1) + 1
                prev.updated_at = datetime.now(timezone.utc)
                await session.commit()
                return prev
    event = Event(
        level=level,
        kind=kind,
        message=message,
        subscription_id=subscription_id,
        media_id=media_id,
    )
    session.add(event)
    await session.commit()
    return event


async def list_by_kind(
    session: AsyncSession,
    kind: str,
) -> list[Event]:
    """List all events with a given kind."""
    result = await session.execute(
        select(Event).where(Event.kind == kind)
    )
    return result.scalars().all()


async def list(
    session: AsyncSession,
    limit: int = 50,
    offset: int = 0,
) -> list[Event]:
    """List events with pagination."""
    # updated_at: a collapsed, still-recurring error floats back to the top.
    stmt = select(Event).order_by(desc(Event.updated_at)).limit(limit).offset(offset)
    result = await session.execute(stmt)
    return result.scalars().all()
