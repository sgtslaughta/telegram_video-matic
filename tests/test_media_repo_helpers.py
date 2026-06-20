"""Tests for new media repository helper functions."""
import pytest
import pytest_asyncio
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.models import (
    Base, Channel, Subscription, MediaItem, MediaStatus,
    SubMode, FilterMode
)
from app.db.repositories import media


@pytest_asyncio.fixture
async def session_factory():
    """In-memory SQLite session factory for tests."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    yield factory
    await engine.dispose()


@pytest_asyncio.fixture
async def session(session_factory):
    """Single session for fixtures."""
    async with session_factory() as s:
        yield s


@pytest_asyncio.fixture
async def channel(session):
    """Create a test channel."""
    ch = Channel(
        tg_id=111,
        title="Test Channel",
        is_forum=False,
        photo_b64=None,
    )
    session.add(ch)
    await session.commit()
    await session.refresh(ch)
    return ch


@pytest_asyncio.fixture
async def subscription(session, channel):
    """Create a test subscription."""
    sub = Subscription(
        channel_id=channel.id,
        topic_id=None,
        storage_path="/tmp/test",
        rename_template="{original}",
        enabled=True,
        mode=SubMode.IMMEDIATE,
        filter_regex=None,
        filter_mode=FilterMode.INCLUDE,
    )
    session.add(sub)
    await session.commit()
    await session.refresh(sub)
    return sub


@pytest.mark.asyncio
async def test_list_by_status(session, channel, subscription):
    """list_by_status returns items with matching status."""
    # Create items with different statuses
    pending = MediaItem(
        channel_id=channel.id,
        subscription_id=subscription.id,
        tg_msg_id=1001,
        file_name="file1.mp4",
        status=MediaStatus.PENDING,
        date_posted=datetime.now(timezone.utc),
    )
    downloaded = MediaItem(
        channel_id=channel.id,
        subscription_id=subscription.id,
        tg_msg_id=1002,
        file_name="file2.mp4",
        status=MediaStatus.DOWNLOADED,
        date_posted=datetime.now(timezone.utc),
    )
    skipped = MediaItem(
        channel_id=channel.id,
        subscription_id=subscription.id,
        tg_msg_id=1003,
        file_name="file3.mp4",
        status=MediaStatus.SKIPPED,
        date_posted=datetime.now(timezone.utc),
    )

    session.add_all([pending, downloaded, skipped])
    await session.commit()

    # Query for DOWNLOADED items
    result = await media.list_by_status(session, MediaStatus.DOWNLOADED)
    assert len(result) == 1
    assert result[0].tg_msg_id == 1002


@pytest.mark.asyncio
async def test_set_local_path(session, channel, subscription):
    """set_local_path updates the local_path field."""
    item = MediaItem(
        channel_id=channel.id,
        subscription_id=subscription.id,
        tg_msg_id=2001,
        file_name="file.mp4",
        status=MediaStatus.DOWNLOADED,
        date_posted=datetime.now(timezone.utc),
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)

    # Set local path
    await media.set_local_path(session, item.id, "/path/to/file.mp4")

    # Verify
    updated = await media.get(session, item.id)
    assert updated.local_path == "/path/to/file.mp4"

    # Clear local path
    await media.set_local_path(session, item.id, None)
    updated = await media.get(session, item.id)
    assert updated.local_path is None


@pytest.mark.asyncio
async def test_list_downloaded_before(session, channel, subscription):
    """list_downloaded_before returns DOWNLOADED items with downloaded_at < cutoff."""
    old_date = datetime.now(timezone.utc) - timedelta(days=100)
    new_date = datetime.now(timezone.utc)

    old_item = MediaItem(
        channel_id=channel.id,
        subscription_id=subscription.id,
        tg_msg_id=3001,
        file_name="old.mp4",
        status=MediaStatus.DOWNLOADED,
        date_posted=datetime.now(timezone.utc),
        downloaded_at=old_date,
    )
    new_item = MediaItem(
        channel_id=channel.id,
        subscription_id=subscription.id,
        tg_msg_id=3002,
        file_name="new.mp4",
        status=MediaStatus.DOWNLOADED,
        date_posted=datetime.now(timezone.utc),
        downloaded_at=new_date,
    )
    pending_item = MediaItem(
        channel_id=channel.id,
        subscription_id=subscription.id,
        tg_msg_id=3003,
        file_name="pending.mp4",
        status=MediaStatus.PENDING,
        date_posted=datetime.now(timezone.utc),
        downloaded_at=old_date,
    )

    session.add_all([old_item, new_item, pending_item])
    await session.commit()

    # Query for items before 50 days ago
    cutoff = datetime.now(timezone.utc) - timedelta(days=50)
    result = await media.list_downloaded_before(session, cutoff)

    # Should only return old_item (DOWNLOADED and before cutoff)
    assert len(result) == 1
    assert result[0].tg_msg_id == 3001


@pytest.mark.asyncio
async def test_list_downloaded_oldest_first(session, channel, subscription):
    """list_downloaded_oldest_first returns DOWNLOADED items ordered by downloaded_at."""
    date1 = datetime.now(timezone.utc) - timedelta(days=100)
    date2 = datetime.now(timezone.utc) - timedelta(days=50)
    date3 = datetime.now(timezone.utc)

    item3 = MediaItem(
        channel_id=channel.id,
        subscription_id=subscription.id,
        tg_msg_id=4003,
        file_name="newest.mp4",
        status=MediaStatus.DOWNLOADED,
        date_posted=datetime.now(timezone.utc),
        downloaded_at=date3,
    )
    item1 = MediaItem(
        channel_id=channel.id,
        subscription_id=subscription.id,
        tg_msg_id=4001,
        file_name="oldest.mp4",
        status=MediaStatus.DOWNLOADED,
        date_posted=datetime.now(timezone.utc),
        downloaded_at=date1,
    )
    item2 = MediaItem(
        channel_id=channel.id,
        subscription_id=subscription.id,
        tg_msg_id=4002,
        file_name="middle.mp4",
        status=MediaStatus.DOWNLOADED,
        date_posted=datetime.now(timezone.utc),
        downloaded_at=date2,
    )
    pending = MediaItem(
        channel_id=channel.id,
        subscription_id=subscription.id,
        tg_msg_id=4004,
        file_name="pending.mp4",
        status=MediaStatus.PENDING,
        date_posted=datetime.now(timezone.utc),
        downloaded_at=date1,
    )

    session.add_all([item1, item2, item3, pending])
    await session.commit()

    # Query for oldest first
    result = await media.list_downloaded_oldest_first(session)

    # Should return only DOWNLOADED items, oldest first
    assert len(result) == 3
    assert result[0].tg_msg_id == 4001  # oldest
    assert result[1].tg_msg_id == 4002  # middle
    assert result[2].tg_msg_id == 4003  # newest


@pytest.mark.asyncio
async def test_set_status_downloaded_at_is_utc(session, channel, subscription):
    """set_status to DOWNLOADED sets downloaded_at in UTC and tz-aware."""
    item = MediaItem(
        channel_id=channel.id,
        subscription_id=subscription.id,
        tg_msg_id=5001,
        file_name="test.mp4",
        status=MediaStatus.PENDING,
        date_posted=datetime.now(timezone.utc),
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)

    # Set status to DOWNLOADED
    before = datetime.now(timezone.utc)
    await media.set_status(session, item.id, MediaStatus.DOWNLOADED)
    after = datetime.now(timezone.utc)

    # Verify: downloaded_at is set and tz-aware in UTC
    updated = await media.get(session, item.id)
    assert updated.downloaded_at is not None, "downloaded_at should be set"
    assert updated.downloaded_at.tzinfo is not None, "downloaded_at should be tz-aware"
    assert updated.downloaded_at.tzinfo == timezone.utc, "downloaded_at should be UTC"
    assert before <= updated.downloaded_at <= after, "downloaded_at should be recent"
