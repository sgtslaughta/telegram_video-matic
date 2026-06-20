from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import Channel


async def upsert(
    session: AsyncSession,
    tg_id: int,
    title: str,
    username: str | None,
    is_forum: bool,
    photo_b64: str | None,
    raw: dict | None,
) -> Channel:
    """Insert or update channel by tg_id."""
    result = await session.execute(
        select(Channel).where(Channel.tg_id == tg_id)
    )
    channel = result.scalar_one_or_none()

    if not channel:
        channel = Channel(
            tg_id=tg_id,
            title=title,
            username=username,
            is_forum=is_forum,
            photo_b64=photo_b64,
            raw=raw,
        )
        session.add(channel)
    else:
        channel.title = title
        channel.username = username
        channel.is_forum = is_forum
        channel.photo_b64 = photo_b64
        channel.raw = raw

    await session.commit()
    return channel


async def get_by_tg_id(session: AsyncSession, tg_id: int) -> Channel | None:
    """Get channel by Telegram ID."""
    result = await session.execute(
        select(Channel).where(Channel.tg_id == tg_id)
    )
    return result.scalar_one_or_none()
