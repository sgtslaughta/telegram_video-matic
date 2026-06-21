from datetime import datetime, timezone
from typing import TYPE_CHECKING
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
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
            item.downloaded_at = datetime.now(timezone.utc)
        await session.commit()
    return item


async def claim_pending(
    session: AsyncSession,
    limit: int = 10,
) -> list[MediaItem]:
    """
    Atomically claim pending media items: ad-hoc (no subscription) or from
    enabled subscriptions. Flips status pending→queued in a single transaction.
    """
    # Outer join so ad-hoc items (subscription_id IS NULL) are included.
    result = await session.execute(
        select(MediaItem).outerjoin(
            Subscription,
            MediaItem.subscription_id == Subscription.id,
        ).where(
            and_(
                MediaItem.status == MediaStatus.PENDING,
                or_(
                    MediaItem.subscription_id.is_(None),
                    Subscription.enabled.is_(True),
                ),
            )
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
    channel_id: int,
    topic_id: int | None = None,
) -> MediaItem:
    """Insert or update media item from a MediaDTO.

    channel_id/topic_id are DB foreign keys (not the Telegram ids on the DTO).
    """
    return await upsert_from_tg(
        session=session,
        channel_id=channel_id,
        topic_id=topic_id,
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


async def list_downloaded_for_sub(
    session: AsyncSession,
    subscription_id: int,
) -> list[MediaItem]:
    """DOWNLOADED items for one subscription, oldest first (for quota/retention)."""
    result = await session.execute(
        select(MediaItem)
        .where(
            and_(
                MediaItem.subscription_id == subscription_id,
                MediaItem.status == "downloaded",
            )
        )
        .order_by(MediaItem.downloaded_at.asc())
    )
    return result.scalars().all()


async def list_filtered(
    session: AsyncSession,
    status: str | None = None,
    sub_id: int | None = None,
    channel_id: int | None = None,
    topic_id: int | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[MediaItem]:
    """List media with optional filters and pagination."""
    query = select(MediaItem)
    filters = []

    if status is not None:
        filters.append(MediaItem.status == status)
    if sub_id is not None:
        filters.append(MediaItem.subscription_id == sub_id)
    if channel_id is not None:
        filters.append(MediaItem.channel_id == channel_id)
    if topic_id is not None:
        filters.append(MediaItem.topic_id == topic_id)

    if filters:
        query = query.where(and_(*filters))

    query = query.offset(offset).limit(limit)
    result = await session.execute(query)
    return result.scalars().all()
