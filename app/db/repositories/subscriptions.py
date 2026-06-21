from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import Subscription, SubMode, FilterMode


async def create(
    session: AsyncSession,
    channel_id: int,
    topic_id: int | None,
    storage_path: str,
    rename_template: str,
    enabled: bool = True,
    mode: str = SubMode.IMMEDIATE,
    filter_regex: str | None = None,
    filter_mode: str = FilterMode.INCLUDE,
    min_size_mb: int | None = None,
    max_size_mb: int | None = None,
    date_from=None,
    date_to=None,
    season_detection: bool = True,
    retention_days: int | None = None,
    retention_disk_pct: int | None = None,
) -> Subscription:
    """Create a new subscription."""
    sub = Subscription(
        channel_id=channel_id,
        topic_id=topic_id,
        storage_path=storage_path,
        rename_template=rename_template,
        enabled=enabled,
        mode=mode,
        filter_regex=filter_regex,
        filter_mode=filter_mode,
        min_size_mb=min_size_mb,
        max_size_mb=max_size_mb,
        date_from=date_from,
        date_to=date_to,
        season_detection=season_detection,
        retention_days=retention_days,
        retention_disk_pct=retention_disk_pct,
    )
    session.add(sub)
    await session.commit()
    return sub


async def list(
    session: AsyncSession,
    channel_id: int | None = None,
    enabled_only: bool = False,
) -> list[Subscription]:
    """List subscriptions, optionally filtered by channel and enabled."""
    query = select(Subscription)

    if channel_id is not None:
        query = query.where(Subscription.channel_id == channel_id)

    if enabled_only:
        query = query.where(Subscription.enabled.is_(True))

    result = await session.execute(query)
    return result.scalars().all()


async def get(session: AsyncSession, sub_id: int) -> Subscription | None:
    """Get subscription by ID."""
    result = await session.execute(
        select(Subscription).where(Subscription.id == sub_id)
    )
    return result.scalar_one_or_none()


async def update(
    session: AsyncSession,
    sub_id: int,
    **kwargs,
) -> Subscription | None:
    """Update subscription fields."""
    sub = await get(session, sub_id)
    if not sub:
        return None

    for key, value in kwargs.items():
        if hasattr(sub, key):
            setattr(sub, key, value)

    await session.commit()
    return sub


async def delete(session: AsyncSession, sub_id: int) -> None:
    """Delete subscription by ID."""
    sub = await get(session, sub_id)
    if sub:
        await session.delete(sub)
        await session.commit()


async def get_by_channel_topic(
    session: AsyncSession,
    channel_id: int,
    topic_id: int | None,
) -> Subscription | None:
    """Get subscription by (channel_id, topic_id) for duplicate detection."""
    result = await session.execute(
        select(Subscription).where(
            (Subscription.channel_id == channel_id)
            & (Subscription.topic_id == topic_id)
        )
    )
    return result.scalar_one_or_none()
