from sqlalchemy.ext.asyncio import AsyncSession
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
