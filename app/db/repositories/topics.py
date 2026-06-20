from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import Topic


async def upsert(
    session: AsyncSession,
    channel_id: int,
    tg_topic_id: int,
    title: str,
    raw: dict | None,
) -> Topic:
    """Insert or update topic by (channel_id, tg_topic_id)."""
    result = await session.execute(
        select(Topic).where(
            (Topic.channel_id == channel_id) & (Topic.tg_topic_id == tg_topic_id)
        )
    )
    topic = result.scalar_one_or_none()

    if not topic:
        topic = Topic(
            channel_id=channel_id,
            tg_topic_id=tg_topic_id,
            title=title,
            raw=raw,
        )
        session.add(topic)
    else:
        topic.title = title
        topic.raw = raw

    await session.commit()
    return topic


async def get_or_create_general(
    session: AsyncSession,
    channel_id: int,
) -> Topic:
    """Get or create synthetic 'General' topic for non-forum channels."""
    result = await session.execute(
        select(Topic).where(
            (Topic.channel_id == channel_id) & (Topic.tg_topic_id == 0)
        )
    )
    topic = result.scalar_one_or_none()

    if not topic:
        topic = Topic(
            channel_id=channel_id,
            tg_topic_id=0,
            title="General",
            raw=None,
        )
        session.add(topic)
        await session.commit()

    return topic
