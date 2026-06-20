from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.db.models import MediaItem, MediaStatus, Subscription


async def upsert_from_tg(
    session: AsyncSession,
    channel_id: int,
    topic_id: int | None,
    subscription_id: int | None,
    tg_msg_id: int,
    caption: str | None,
    file_name: str | None,
    mime: str | None,
    size_bytes: int | None,
    duration_sec: int | None,
    date_posted: datetime,
    thumb_b64: str | None,
    raw: dict | None,
) -> MediaItem:
    """Insert or update media item by (channel_id, tg_msg_id)."""
    result = await session.execute(
        select(MediaItem).where(
            and_(
                MediaItem.channel_id == channel_id,
                MediaItem.tg_msg_id == tg_msg_id,
            )
        )
    )
    item = result.scalar_one_or_none()

    if not item:
        item = MediaItem(
            channel_id=channel_id,
            topic_id=topic_id,
            subscription_id=subscription_id,
            tg_msg_id=tg_msg_id,
            caption=caption,
            file_name=file_name,
            mime=mime,
            size_bytes=size_bytes,
            duration_sec=duration_sec,
            date_posted=date_posted,
            thumb_b64=thumb_b64,
            raw=raw,
            status=MediaStatus.PENDING,
        )
        session.add(item)
    else:
        item.caption = caption
        item.file_name = file_name
        item.mime = mime
        item.size_bytes = size_bytes
        item.duration_sec = duration_sec
        item.thumb_b64 = thumb_b64
        item.raw = raw

    await session.commit()
    return item


async def set_status(
    session: AsyncSession,
    media_id: int,
    status: str,
) -> MediaItem | None:
    """Set media status."""
    item = await session.get(MediaItem, media_id)
    if item:
        item.status = status
        if status == MediaStatus.DOWNLOADED:
            item.downloaded_at = datetime.now(datetime.now().astimezone().tzinfo)
        await session.commit()
    return item


async def claim_pending(
    session: AsyncSession,
    limit: int = 10,
) -> list[MediaItem]:
    """
    Atomically claim pending media items from enabled subscriptions.
    Flips status pending→queued in a single transaction.
    """
    # Select pending items from enabled subscriptions
    result = await session.execute(
        select(MediaItem).where(
            and_(
                MediaItem.status == MediaStatus.PENDING,
                MediaItem.subscription_id.isnot(None),
            )
        ).join(
            Subscription,
            MediaItem.subscription_id == Subscription.id,
        ).where(
            Subscription.enabled == True,
        ).limit(limit)
    )
    items = result.scalars().all()

    # Atomically flip to queued
    for item in items:
        item.status = MediaStatus.QUEUED

    await session.commit()
    return items


async def get(session: AsyncSession, media_id: int) -> MediaItem | None:
    """Get media item by ID."""
    return await session.get(MediaItem, media_id)
