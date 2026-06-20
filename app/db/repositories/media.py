from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.db.models import MediaItem, MediaStatus, Subscription

if TYPE_CHECKING:
    from app.telegram.dtos import MediaDTO


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


async def get_max_tg_msg_id(
    session: AsyncSession,
    channel_id: int,
    topic_id: int | None,
) -> int | None:
    """Get maximum tg_msg_id for a channel+topic to use as since_msg_id."""
    from sqlalchemy import func
    result = await session.execute(
        select(func.max(MediaItem.tg_msg_id)).where(
            and_(
                MediaItem.channel_id == channel_id,
                MediaItem.topic_id == topic_id,
            )
        )
    )
    return result.scalar()


async def get_by_tg_msg_id(
    session: AsyncSession,
    channel_id: int,
    tg_msg_id: int,
) -> MediaItem | None:
    """Get media item by channel and tg_msg_id."""
    result = await session.execute(
        select(MediaItem).where(
            and_(
                MediaItem.channel_id == channel_id,
                MediaItem.tg_msg_id == tg_msg_id,
            )
        )
    )
    return result.scalar_one_or_none()


async def upsert_from_tg_dto(
    session: AsyncSession,
    media_dto: "MediaDTO",
    subscription_id: int | None,
) -> MediaItem:
    """Insert or update media item from a MediaDTO (wrapper for upsert_from_tg)."""
    return await upsert_from_tg(
        session=session,
        channel_id=media_dto.channel_tg_id,
        topic_id=media_dto.topic_tg_id,
        subscription_id=subscription_id,
        tg_msg_id=media_dto.tg_msg_id,
        caption=media_dto.caption,
        file_name=media_dto.file_name,
        mime=media_dto.mime,
        size_bytes=media_dto.size_bytes,
        duration_sec=media_dto.duration_sec,
        date_posted=media_dto.date_posted,
        thumb_b64=media_dto.thumb_b64,
        raw=media_dto.raw,
    )


async def list_by_status(
    session: AsyncSession,
    status: str,
) -> list[MediaItem]:
    """List all media items with a given status."""
    result = await session.execute(
        select(MediaItem).where(MediaItem.status == status)
    )
    return result.scalars().all()


async def set_local_path(
    session: AsyncSession,
    media_id: int,
    local_path: str | None,
) -> MediaItem | None:
    """Set local_path for a media item."""
    item = await session.get(MediaItem, media_id)
    if item:
        item.local_path = local_path
        await session.commit()
    return item


async def list_downloaded_before(
    session: AsyncSession,
    cutoff: datetime,
) -> list[MediaItem]:
    """List DOWNLOADED items with downloaded_at < cutoff."""
    result = await session.execute(
        select(MediaItem).where(
            and_(
                MediaItem.status == "downloaded",
                MediaItem.downloaded_at < cutoff,
            )
        )
    )
    return result.scalars().all()


async def list_downloaded_oldest_first(
    session: AsyncSession,
) -> list[MediaItem]:
    """List all DOWNLOADED items ordered by downloaded_at (oldest first)."""
    result = await session.execute(
        select(MediaItem)
        .where(MediaItem.status == "downloaded")
        .order_by(MediaItem.downloaded_at.asc())
    )
    return result.scalars().all()
