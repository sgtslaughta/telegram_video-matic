"""Test suite for SyncEngine.maintenance (Task 6: Drift & Pruning)."""
import pytest
import pytest_asyncio
import asyncio
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.models import (
    Base, Channel, Topic, Subscription, MediaItem, MediaStatus,
    SubMode, FilterMode, EventLevel
)
from app.db.repositories import media, subscriptions, events
from app.sync.engine import SyncEngine
from app.telegram.dtos import MediaDTO


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
async def mock_tg_service():
    """Mock TelegramService."""
    return AsyncMock()


@pytest_asyncio.fixture
async def mock_plugin_host():
    """Mock PluginHost."""
    host = AsyncMock()
    host.dispatch = AsyncMock()
    return host


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
        min_size_mb=None,
        max_size_mb=None,
        season_detection=True,
        retention_days=None,
        retention_disk_pct=None,
    )
    session.add(sub)
    await session.commit()
    await session.refresh(sub)
    return sub


@pytest.mark.asyncio
async def test_maintenance_missing_file_drift(session_factory, session, channel, subscription, tmp_path):
    """Missing-file drift: DOWNLOADED item with missing file → PENDING + drift event."""
    # Create a DOWNLOADED item with a local_path that doesn't exist
    item = MediaItem(
        channel_id=channel.id,
        topic_id=None,
        subscription_id=subscription.id,
        tg_msg_id=1001,
        caption="Test video",
        file_name="test.mp4",
        mime="video/mp4",
        size_bytes=1024 * 1024,
        duration_sec=60,
        date_posted=datetime.now(timezone.utc),
        status=MediaStatus.DOWNLOADED,
        local_path="/nonexistent/path/test.mp4",
        downloaded_at=datetime.now(timezone.utc),
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)

    # Create engine and run maintenance
    engine = SyncEngine(
        session_factory=session_factory,
        tg_service=AsyncMock(),
        plugin_host=MagicMock(),
        poll_interval_sec=60,
    )

    # Run single maintenance pass
    async with session_factory() as maint_session:
        await engine._maintenance_pass(maint_session)

    # Verify status changed to PENDING
    async with session_factory() as check_session:
        updated_item = await media.get(check_session, item.id)
        assert updated_item.status == MediaStatus.PENDING, f"Expected PENDING, got {updated_item.status}"

    # Verify drift event was logged
    async with session_factory() as check_session:
        items = await events.list_by_kind(check_session, "drift")
        assert len(items) > 0, "Expected drift event"
        assert items[0].media_id == item.id


@pytest.mark.asyncio
async def test_maintenance_age_prune(session_factory, session, channel, subscription, tmp_path):
    """Age prune: DOWNLOADED item older than retention_days → delete file, set local_path=None, status=SKIPPED."""
    # Create a temporary file
    file_path = tmp_path / "old_video.mp4"
    file_path.write_text("dummy content")

    # Create a DOWNLOADED item with old downloaded_at
    old_date = datetime.now(timezone.utc) - timedelta(days=100)
    item = MediaItem(
        channel_id=channel.id,
        topic_id=None,
        subscription_id=subscription.id,
        tg_msg_id=2001,
        caption="Old video",
        file_name="old_video.mp4",
        mime="video/mp4",
        size_bytes=1024 * 1024,
        duration_sec=60,
        date_posted=datetime.now(timezone.utc),
        status=MediaStatus.DOWNLOADED,
        local_path=str(file_path),
        downloaded_at=old_date,
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)

    # Mock settings to return 90 days retention
    with patch("app.db.repositories.settings.get") as mock_settings_get:
        async def settings_get_side_effect(s, key, default=None):
            if key == "retention_days":
                return 90
            return default
        mock_settings_get.side_effect = settings_get_side_effect

        # Create engine and run maintenance
        engine = SyncEngine(
            session_factory=session_factory,
            tg_service=AsyncMock(),
            plugin_host=MagicMock(),
            poll_interval_sec=60,
        )

        # Run single maintenance pass
        async with session_factory() as maint_session:
            await engine._maintenance_pass(maint_session)

    # Verify file was deleted
    assert not file_path.exists(), "File should be deleted"

    # Verify item status changed to SKIPPED and local_path cleared
    async with session_factory() as check_session:
        updated_item = await media.get(check_session, item.id)
        assert updated_item.status == MediaStatus.SKIPPED
        assert updated_item.local_path is None

    # Verify prune event was logged
    async with session_factory() as check_session:
        items = await events.list_by_kind(check_session, "prune")
        assert len(items) > 0, "Expected prune event"


@pytest.mark.asyncio
async def test_maintenance_disk_pct_prune(session_factory, session, channel, subscription, tmp_path):
    """Disk % prune: when usage >= retention_disk_pct, delete oldest DOWNLOADED files."""
    # Create two temporary files
    file1 = tmp_path / "video1.mp4"
    file2 = tmp_path / "video2.mp4"
    file1.write_text("content1")
    file2.write_text("content2")

    # Create two DOWNLOADED items, file1 older than file2
    old_date = datetime.now(timezone.utc) - timedelta(hours=1)
    new_date = datetime.now(timezone.utc)

    item1 = MediaItem(
        channel_id=channel.id,
        topic_id=None,
        subscription_id=subscription.id,
        tg_msg_id=3001,
        caption="Old video",
        file_name="video1.mp4",
        mime="video/mp4",
        size_bytes=1024 * 1024,
        duration_sec=60,
        date_posted=datetime.now(timezone.utc),
        status=MediaStatus.DOWNLOADED,
        local_path=str(file1),
        downloaded_at=old_date,
    )
    item2 = MediaItem(
        channel_id=channel.id,
        topic_id=None,
        subscription_id=subscription.id,
        tg_msg_id=3002,
        caption="New video",
        file_name="video2.mp4",
        mime="video/mp4",
        size_bytes=1024 * 1024,
        duration_sec=60,
        date_posted=datetime.now(timezone.utc),
        status=MediaStatus.DOWNLOADED,
        local_path=str(file2),
        downloaded_at=new_date,
    )
    session.add(item1)
    session.add(item2)
    await session.commit()
    await session.refresh(item1)
    await session.refresh(item2)

    # Mock disk_usage to simulate >= threshold (e.g., 85% when threshold is 80%)
    mock_usage_high = AsyncMock()
    mock_usage_high.used = 85
    mock_usage_high.total = 100

    mock_usage_low = AsyncMock()
    mock_usage_low.used = 70
    mock_usage_low.total = 100

    usage_sequence = [mock_usage_high, mock_usage_low]
    usage_iter = iter(usage_sequence)

    def mock_disk_usage(path):
        return next(usage_iter)

    with patch("shutil.disk_usage", side_effect=mock_disk_usage):
        with patch("app.db.repositories.settings.get") as mock_settings_get:
            async def settings_get_side_effect(s, key, default=None):
                if key == "retention_days":
                    return 90
                elif key == "retention_disk_pct":
                    return 80
                return default
            mock_settings_get.side_effect = settings_get_side_effect

            # Create engine and run maintenance
            engine = SyncEngine(
                session_factory=session_factory,
                tg_service=AsyncMock(),
                plugin_host=MagicMock(),
                poll_interval_sec=60,
            )

            # Run single maintenance pass
            async with session_factory() as maint_session:
                await engine._maintenance_pass(maint_session)

    # Verify oldest file (file1) was deleted, newest (file2) was not
    assert not file1.exists(), "Oldest file should be deleted"
    assert file2.exists(), "Newer file should not be deleted"

    # Verify item1 status is SKIPPED and local_path is None
    async with session_factory() as check_session:
        updated_item1 = await media.get(check_session, item1.id)
        assert updated_item1.status == MediaStatus.SKIPPED
        assert updated_item1.local_path is None

    # Verify item2 status is still DOWNLOADED
    async with session_factory() as check_session:
        updated_item2 = await media.get(check_session, item2.id)
        assert updated_item2.status == MediaStatus.DOWNLOADED


@pytest.mark.asyncio
async def test_maintenance_does_not_touch_pending_queued_failed(session_factory, session, channel, subscription, tmp_path):
    """Pruning NEVER touches PENDING/QUEUED/FAILED items."""
    # Create three files
    file1 = tmp_path / "pending.mp4"
    file2 = tmp_path / "queued.mp4"
    file3 = tmp_path / "failed.mp4"
    file1.write_text("pending")
    file2.write_text("queued")
    file3.write_text("failed")

    # Create items with different statuses
    old_date = datetime.now(timezone.utc) - timedelta(days=100)

    pending_item = MediaItem(
        channel_id=channel.id,
        topic_id=None,
        subscription_id=subscription.id,
        tg_msg_id=4001,
        caption="Pending",
        file_name="pending.mp4",
        mime="video/mp4",
        size_bytes=1024 * 1024,
        duration_sec=60,
        date_posted=datetime.now(timezone.utc),
        status=MediaStatus.PENDING,
        local_path=str(file1),
    )
    queued_item = MediaItem(
        channel_id=channel.id,
        topic_id=None,
        subscription_id=subscription.id,
        tg_msg_id=4002,
        caption="Queued",
        file_name="queued.mp4",
        mime="video/mp4",
        size_bytes=1024 * 1024,
        duration_sec=60,
        date_posted=datetime.now(timezone.utc),
        status=MediaStatus.QUEUED,
        local_path=str(file2),
        downloaded_at=old_date,
    )
    failed_item = MediaItem(
        channel_id=channel.id,
        topic_id=None,
        subscription_id=subscription.id,
        tg_msg_id=4003,
        caption="Failed",
        file_name="failed.mp4",
        mime="video/mp4",
        size_bytes=1024 * 1024,
        duration_sec=60,
        date_posted=datetime.now(timezone.utc),
        status=MediaStatus.FAILED,
        local_path=str(file3),
        downloaded_at=old_date,
    )

    session.add(pending_item)
    session.add(queued_item)
    session.add(failed_item)
    await session.commit()
    await session.refresh(pending_item)
    await session.refresh(queued_item)
    await session.refresh(failed_item)

    # Mock settings for aggressive pruning
    with patch("app.db.repositories.settings.get") as mock_settings_get:
        async def settings_get_side_effect(s, key, default=None):
            if key == "retention_days":
                return 1  # Very aggressive
            return default
        mock_settings_get.side_effect = settings_get_side_effect

        # Create engine and run maintenance
        engine = SyncEngine(
            session_factory=session_factory,
            tg_service=AsyncMock(),
            plugin_host=MagicMock(),
            poll_interval_sec=60,
        )

        # Run single maintenance pass
        async with session_factory() as maint_session:
            await engine._maintenance_pass(maint_session)

    # Verify all files still exist (pruning never touches non-DOWNLOADED)
    assert file1.exists(), "PENDING file should not be deleted"
    assert file2.exists(), "QUEUED file should not be deleted"
    assert file3.exists(), "FAILED file should not be deleted"

    # Verify statuses unchanged
    async with session_factory() as check_session:
        up = await media.get(check_session, pending_item.id)
        uq = await media.get(check_session, queued_item.id)
        uf = await media.get(check_session, failed_item.id)
        assert up.status == MediaStatus.PENDING
        assert uq.status == MediaStatus.QUEUED
        assert uf.status == MediaStatus.FAILED


@pytest.mark.asyncio
async def test_maintenance_orphans_untouched(session_factory, session, channel, subscription, tmp_path):
    """Files on disk not in DB are never deleted (no directory scan)."""
    # Create an orphan file (not in DB)
    orphan_file = tmp_path / "orphan.mp4"
    orphan_file.write_text("orphan content")

    # Create one DOWNLOADED item for comparison
    file1 = tmp_path / "tracked.mp4"
    file1.write_text("tracked")

    old_date = datetime.now(timezone.utc) - timedelta(days=100)
    item = MediaItem(
        channel_id=channel.id,
        topic_id=None,
        subscription_id=subscription.id,
        tg_msg_id=5001,
        caption="Tracked",
        file_name="tracked.mp4",
        mime="video/mp4",
        size_bytes=1024 * 1024,
        duration_sec=60,
        date_posted=datetime.now(timezone.utc),
        status=MediaStatus.DOWNLOADED,
        local_path=str(file1),
        downloaded_at=old_date,
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)

    # Mock settings for aggressive pruning
    with patch("app.db.repositories.settings.get") as mock_settings_get:
        async def settings_get_side_effect(s, key, default=None):
            if key == "retention_days":
                return 1
            return default
        mock_settings_get.side_effect = settings_get_side_effect

        # Create engine and run maintenance
        engine = SyncEngine(
            session_factory=session_factory,
            tg_service=AsyncMock(),
            plugin_host=MagicMock(),
            poll_interval_sec=60,
        )

        # Run single maintenance pass
        async with session_factory() as maint_session:
            await engine._maintenance_pass(maint_session)

    # Verify orphan file is UNTOUCHED (never scanned/deleted)
    assert orphan_file.exists(), "Orphan file on disk should never be deleted"
    # Tracked file is deleted because it's in DB and old
    assert not file1.exists(), "Tracked old file should be deleted"


@pytest.mark.asyncio
async def test_maintenance_gap_reconcile_new_media(session_factory, session, channel, subscription):
    """Gap reconcile: full iter_media reveals msg_id not in DB → insert as PENDING."""
    # Setup: DB has msg_ids {1, 2}
    item1 = MediaItem(
        channel_id=channel.id,
        topic_id=None,
        subscription_id=subscription.id,
        tg_msg_id=1,
        caption="First",
        file_name="first.mp4",
        mime="video/mp4",
        size_bytes=1024 * 1024,
        duration_sec=60,
        date_posted=datetime.now(timezone.utc),
        status=MediaStatus.DOWNLOADED,
    )
    item2 = MediaItem(
        channel_id=channel.id,
        topic_id=None,
        subscription_id=subscription.id,
        tg_msg_id=2,
        caption="Second",
        file_name="second.mp4",
        mime="video/mp4",
        size_bytes=1024 * 1024,
        duration_sec=60,
        date_posted=datetime.now(timezone.utc),
        status=MediaStatus.DOWNLOADED,
    )
    session.add(item1)
    session.add(item2)
    await session.commit()

    # Mock tg_service.iter_media to return {1, 2, 3} (msg 3 is new)
    mock_tg_service = MagicMock()

    async def mock_iter_media(channel_id, topic_id, since_msg_id=None):
        # Return all three regardless of since_msg_id (full fetch for gap reconcile)
        dtos = [
            MediaDTO(
                channel_tg_id=channel.tg_id,
                topic_tg_id=None,
                tg_msg_id=1,
                caption="First",
                file_name="first.mp4",
                mime="video/mp4",
                size_bytes=1024 * 1024,
                duration_sec=60,
                date_posted=datetime.now(timezone.utc),
                thumb_b64=None,
                reactions=None,
                comments_count=None,
                raw=None,
            ),
            MediaDTO(
                channel_tg_id=channel.tg_id,
                topic_tg_id=None,
                tg_msg_id=2,
                caption="Second",
                file_name="second.mp4",
                mime="video/mp4",
                size_bytes=1024 * 1024,
                duration_sec=60,
                date_posted=datetime.now(timezone.utc),
                thumb_b64=None,
                reactions=None,
                comments_count=None,
                raw=None,
            ),
            MediaDTO(
                channel_tg_id=channel.tg_id,
                topic_tg_id=None,
                tg_msg_id=3,
                caption="Third (new)",
                file_name="third.mp4",
                mime="video/mp4",
                size_bytes=1024 * 1024,
                duration_sec=60,
                date_posted=datetime.now(timezone.utc),
                thumb_b64=None,
                reactions=None,
                comments_count=None,
                raw=None,
            ),
        ]
        for dto in dtos:
            yield dto

    mock_tg_service.iter_media = mock_iter_media

    # Create engine and run maintenance
    engine = SyncEngine(
        session_factory=session_factory,
        tg_service=mock_tg_service,
        plugin_host=MagicMock(),
        poll_interval_sec=60,
    )

    # Run single maintenance pass
    async with session_factory() as maint_session:
        await engine._maintenance_pass(maint_session)

    # Verify: msg 3 was inserted with PENDING status
    async with session_factory() as check_session:
        item3 = await media.get_by_tg_msg_id(check_session, channel.id, 3)
        assert item3 is not None, "Gap item (msg 3) should be inserted"
        assert item3.status == MediaStatus.PENDING, f"Expected PENDING, got {item3.status}"
        assert item3.subscription_id == subscription.id

    # Verify: items 1 and 2 remain unchanged
    async with session_factory() as check_session:
        check_item1 = await media.get_by_tg_msg_id(check_session, channel.id, 1)
        check_item2 = await media.get_by_tg_msg_id(check_session, channel.id, 2)
        assert check_item1.status == MediaStatus.DOWNLOADED
        assert check_item2.status == MediaStatus.DOWNLOADED

    # Verify: drift event logged for gap item (only if gap_count > 0)
    async with session_factory() as check_session:
        drift_events = await events.list_by_kind(check_session, "drift")
        gap_events = [e for e in drift_events if "gap" in (e.message or "").lower()]
        assert len(gap_events) > 0, "Expected gap drift event"


@pytest.mark.asyncio
async def test_maintenance_gap_reconcile_skip_filtered(session_factory, session, channel, subscription):
    """Gap reconcile: if gap item is filtered (skip), set status to SKIPPED + event."""
    # Setup: subscription has a filter that excludes "skip_me"
    sub_filtered = Subscription(
        channel_id=channel.id,
        topic_id=None,
        storage_path="/tmp/test",
        rename_template="{original}",
        enabled=True,
        mode=SubMode.IMMEDIATE,
        filter_regex="skip_me",
        filter_mode=FilterMode.EXCLUDE,
        min_size_mb=None,
        max_size_mb=None,
        season_detection=True,
    )
    session.add(sub_filtered)
    # Disable the default fixture subscription so only sub_filtered (the one
    # with the exclude filter) owns the gap message. Two channel-level subs on
    # one channel is allowed (topic_id NULL is distinct under UNIQUE), so we
    # isolate the filtered sub to assert its skip behavior unambiguously.
    subscription.enabled = False
    session.add(subscription)
    await session.commit()
    await session.refresh(sub_filtered)

    # Mock tg_service.iter_media to return one media that should be skipped
    mock_tg_service = MagicMock()

    async def mock_iter_media(channel_id, topic_id, since_msg_id=None):
        yield MediaDTO(
            channel_tg_id=channel.tg_id,
            topic_tg_id=None,
            tg_msg_id=100,
            caption="skip_me",
            file_name="skip_me.mp4",
            mime="video/mp4",
            size_bytes=1024 * 1024,
            duration_sec=60,
            date_posted=datetime.now(timezone.utc),
            thumb_b64=None,
            reactions=None,
            comments_count=None,
            raw=None,
        )

    mock_tg_service.iter_media = mock_iter_media

    # Create engine and run maintenance
    engine = SyncEngine(
        session_factory=session_factory,
        tg_service=mock_tg_service,
        plugin_host=MagicMock(),
        poll_interval_sec=60,
    )

    # Run single maintenance pass
    async with session_factory() as maint_session:
        await engine._maintenance_pass(maint_session)

    # Verify: item was inserted with SKIPPED status
    async with session_factory() as check_session:
        item = await media.get_by_tg_msg_id(check_session, channel.id, 100)
        assert item is not None, "Gap item should be inserted even if filtered"
        assert item.status == MediaStatus.SKIPPED, f"Expected SKIPPED, got {item.status}"

    # Filter skips are silent now (SKIPPED status is the record) — no per-item
    # "filter" event, to keep the activity feed clean.
    async with session_factory() as check_session:
        filter_events = await events.list_by_kind(check_session, "filter")
        assert len(filter_events) == 0, "Filter skips should not log events"
