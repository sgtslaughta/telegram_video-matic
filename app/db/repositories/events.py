from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import Event


async def add(
    session: AsyncSession,
    level: str,
    kind: str,
    message: str,
    subscription_id: int | None = None,
    media_id: int | None = None,
) -> Event:
    """Log an event."""
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
