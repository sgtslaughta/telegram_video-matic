"""Test suite for SyncEngine.poller (Task 4)."""
import pytest
import pytest_asyncio
import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.models import (
    Base, Channel, Topic, Subscription, MediaItem, MediaStatus,
    SubMode, FilterMode, EventLevel
)
from app.db.repositories import media, subscriptions, events
from app.sync.engine import SyncEngine, classify
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
async def mock_broadcast():
    """Mock broadcast callable."""
    return AsyncMock()


@pytest.mark.asyncio
async def test_sync_engine_init(session_factory, mock_tg_service, mock_plugin_host, mock_broadcast):
    """SyncEngine.__init__ initializes fields."""
    engine = SyncEngine(
        session_factory=session_factory,
        tg_service=mock_tg_service,
        plugin_host=mock_plugin_host,
        broadcast=mock_broadcast,
        poll_interval_sec=60
    )

    assert engine.session_factory == session_factory
    assert engine.tg_service == mock_tg_service
    assert engine.plugin_host == mock_plugin_host
    assert engine.broadcast == mock_broadcast
    assert engine.poll_interval_sec == 60
    assert hasattr(engine, '_stop_event')
    assert hasattr(engine, '_tasks')


@pytest.mark.asyncio
async def test_poller_fetches_and_classifies(session_factory, session, mock_tg_service, mock_plugin_host, mock_broadcast):
    """Poller calls subscriptions.list_enabled, iter_media, upserts, classifies, dispatches."""
    # Setup: create subscription, channel, and fake media DTOs
    channel = Channel(
        tg_id=111,
        title="Test Channel",
        is_forum=False,
        photo_b64=None,
    )
    session.add(channel)
    await session.commit()
    await session.refresh(channel)

    sub = Subscription(
        channel_id=channel.id,
        topic_id=None,
        storage_path="/tmp/test",
        rename_template="{original}",
        enabled=True,
        mode=SubMode.IMMEDIATE,
    )
    session.add(sub)
    await session.commit()
    await session.refresh(sub)

    # Mock iter_media to yield 2 fake MediaDTOs
    media_dtos = [
        MediaDTO(
            tg_msg_id=1,
            channel_tg_id=111,
            topic_tg_id=None,
            caption="Video 1",
            file_name="video1.mp4",
            mime="video/mp4",
            size_bytes=100*1024*1024,
            duration_sec=60,
            date_posted=datetime.now(timezone.utc),
            thumb_b64=None,
            reactions=None,
            comments_count=None,
            raw={},
        ),
        MediaDTO(
            tg_msg_id=2,
            channel_tg_id=111,
            topic_tg_id=None,
            caption="Video 2",
            file_name="video2.mp4",
            mime="video/mp4",
            size_bytes=50*1024*1024,
            duration_sec=30,
            date_posted=datetime.now(timezone.utc),
            thumb_b64=None,
            reactions=None,
            comments_count=None,
            raw={},
        ),
    ]

    async def mock_iter_media(channel_id, topic_id, since_msg_id=None):
        for dto in media_dtos:
            yield dto

    mock_tg_service.iter_media = mock_iter_media

    # Create engine and run one poll cycle
    engine = SyncEngine(
        session_factory=session_factory,
        tg_service=mock_tg_service,
        plugin_host=mock_plugin_host,
        broadcast=mock_broadcast,
        poll_interval_sec=1  # short interval for test
    )

    # Run poller once
    async with session_factory() as test_session:
        await engine._poller_once(test_session)

    # Verify media items were created
    async with session_factory() as test_session:
        result = await test_session.execute(
            __import__('sqlalchemy').select(MediaItem).where(
                MediaItem.subscription_id == sub.id
            )
        )
        items = result.scalars().all()
        assert len(items) == 2
        assert items[0].status == MediaStatus.PENDING
        assert items[1].status == MediaStatus.PENDING

    # Verify plugin dispatch was called
    assert mock_plugin_host.dispatch.call_count >= 2


@pytest.mark.asyncio
async def test_poller_uses_max_tg_msg_id(session_factory, session, mock_tg_service, mock_plugin_host, mock_broadcast):
    """Poller uses max stored tg_msg_id as since_msg_id."""
    channel = Channel(tg_id=111, title="Test", is_forum=False)
    session.add(channel)
    await session.commit()
    await session.refresh(channel)

    sub = Subscription(
        channel_id=channel.id,
        topic_id=None,
        storage_path="/tmp",
        rename_template="{original}",
        enabled=True,
    )
    session.add(sub)
    await session.commit()
    await session.refresh(sub)

    # Insert an existing media item with tg_msg_id=5
    item = MediaItem(
        channel_id=channel.id,
        topic_id=None,
        subscription_id=sub.id,
        tg_msg_id=5,
        caption="Old video",
        file_name="old.mp4",
        date_posted=datetime.now(timezone.utc),
        status=MediaStatus.PENDING,
    )
    session.add(item)
    await session.commit()

    # Mock iter_media to verify since_msg_id is passed correctly
    captured_since_msg_id = None

    async def mock_iter_media(channel_id, topic_id, since_msg_id=None):
        nonlocal captured_since_msg_id
        captured_since_msg_id = since_msg_id
        # Return a new media with tg_msg_id > 5
        yield MediaDTO(
            tg_msg_id=10,
            channel_tg_id=111,
            topic_tg_id=None,
            caption="New video",
            file_name="new.mp4",
            mime="video/mp4",
            size_bytes=100*1024*1024,
            duration_sec=60,
            date_posted=datetime.now(timezone.utc),
            thumb_b64=None,
            reactions=None,
            comments_count=None,
            raw={},
        )

    mock_tg_service.iter_media = mock_iter_media

    engine = SyncEngine(
        session_factory=session_factory,
        tg_service=mock_tg_service,
        plugin_host=mock_plugin_host,
        broadcast=mock_broadcast,
    )

    async with session_factory() as test_session:
        await engine._poller_once(test_session)

    # Verify since_msg_id was 5 (max of existing)
    assert captured_since_msg_id == 5


@pytest.mark.asyncio
async def test_poller_skips_with_events(session_factory, session, mock_tg_service, mock_plugin_host, mock_broadcast):
    """Poller sets skipped status and emits event when classify returns skip."""
    channel = Channel(tg_id=111, title="Test", is_forum=False)
    session.add(channel)
    await session.commit()
    await session.refresh(channel)

    sub = Subscription(
        channel_id=channel.id,
        topic_id=None,
        storage_path="/tmp",
        rename_template="{original}",
        enabled=True,  # Keep enabled so we fetch it
        min_size_mb=500,  # Set a high minimum size to trigger skip
    )
    session.add(sub)
    await session.commit()
    await session.refresh(sub)

    async def mock_iter_media(channel_id, topic_id, since_msg_id=None):
        yield MediaDTO(
            tg_msg_id=1,
            channel_tg_id=111,
            topic_tg_id=None,
            caption="Test",
            file_name="test.mp4",
            mime="video/mp4",
            size_bytes=100*1024*1024,
            duration_sec=60,
            date_posted=datetime.now(timezone.utc),
            thumb_b64=None,
            reactions=None,
            comments_count=None,
            raw={},
        )

    mock_tg_service.iter_media = mock_iter_media

    engine = SyncEngine(
        session_factory=session_factory,
        tg_service=mock_tg_service,
        plugin_host=mock_plugin_host,
        broadcast=mock_broadcast,
    )

    async with session_factory() as test_session:
        await engine._poller_once(test_session)

    # Verify skipped status and event created
    async with session_factory() as test_session:
        result = await test_session.execute(
            __import__('sqlalchemy').select(MediaItem)
        )
        items = result.scalars().all()
        assert len(items) == 1
        assert items[0].status == MediaStatus.SKIPPED

        # Check event was logged
        result = await test_session.execute(
            __import__('sqlalchemy').select(__import__('app.db.models', fromlist=['Event']).Event)
        )
        events_list = result.scalars().all()
        assert any(e.kind == "filter" for e in events_list)


@pytest.mark.asyncio
async def test_poller_catches_exceptions(session_factory, mock_tg_service, mock_plugin_host, mock_broadcast):
    """Poller catches exceptions and continues."""
    async def mock_iter_media_error(*args, **kwargs):
        raise RuntimeError("Telegram service error")

    mock_tg_service.iter_media = mock_iter_media_error

    engine = SyncEngine(
        session_factory=session_factory,
        tg_service=mock_tg_service,
        plugin_host=mock_plugin_host,
        broadcast=mock_broadcast,
    )

    # Should not raise
    async with session_factory() as test_session:
        await engine._poller_once(test_session)
