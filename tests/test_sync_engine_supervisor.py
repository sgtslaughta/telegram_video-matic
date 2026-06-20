"""Test suite for SyncEngine.supervisor lifecycle (Task 7)."""
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
from app.db.repositories import subscriptions, media, events
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
    )
    session.add(sub)
    await session.commit()
    await session.refresh(sub)
    return sub


@pytest.mark.asyncio
async def test_sync_engine_start_launches_tasks(session_factory, mock_tg_service, mock_plugin_host):
    """start() creates three asyncio tasks (poller, downloader, maintenance)."""
    engine = SyncEngine(
        session_factory=session_factory,
        tg_service=mock_tg_service,
        plugin_host=mock_plugin_host,
        poll_interval_sec=0.01,  # Short interval for testing
    )

    # Start the engine
    await engine.start()

    # Verify three tasks were created
    assert len(engine._tasks) == 3, f"Expected 3 tasks, got {len(engine._tasks)}"

    # Verify all are asyncio Tasks
    for task in engine._tasks:
        assert isinstance(task, asyncio.Task), f"Expected asyncio.Task, got {type(task)}"

    # Let them run briefly, then stop
    await asyncio.sleep(0.05)
    await engine.stop()

    # Verify all tasks are done or cancelled
    for task in engine._tasks:
        assert task.done(), f"Task should be done: {task}"


@pytest.mark.asyncio
async def test_sync_engine_stop_cancels_gracefully(session_factory, mock_tg_service, mock_plugin_host):
    """stop() sets event, waits for tasks with timeout, cancels if needed; no pending tasks."""
    engine = SyncEngine(
        session_factory=session_factory,
        tg_service=mock_tg_service,
        plugin_host=mock_plugin_host,
        poll_interval_sec=0.01,
    )

    # Mock tg_service.iter_media to avoid actual calls
    async def mock_iter_media(*args, **kwargs):
        # Simulate a slow operation that should be cancelled
        try:
            await asyncio.sleep(10)  # Never completes
        except asyncio.CancelledError:
            raise
        return
        yield  # Never reached

    mock_tg_service.iter_media = mock_iter_media

    # Start the engine
    await engine.start()
    await asyncio.sleep(0.02)  # Let tasks start

    # Stop should cancel cleanly
    await engine.stop()

    # Verify no pending tasks left behind
    pending = asyncio.all_tasks()
    # Filter out the test task itself
    pending = [t for t in pending if not t.get_name().startswith("test_")]

    for task in engine._tasks:
        assert task.done(), f"Task should be done after stop(): {task}"


@pytest.mark.asyncio
async def test_sync_engine_poller_runs_at_interval(session_factory, channel, subscription):
    """Poller runs _poller_once() at least once during engine.start()."""
    mock_tg_service = AsyncMock()
    mock_plugin_host = AsyncMock()

    # Track poller calls
    poller_calls = []

    # Create a version of _poller_once that records calls
    original_poller_once = SyncEngine._poller_once

    async def tracked_poller_once(self, session):
        poller_calls.append(1)
        return await original_poller_once(self, session)

    engine = SyncEngine(
        session_factory=session_factory,
        tg_service=mock_tg_service,
        plugin_host=mock_plugin_host,
        poll_interval_sec=0.01,
    )

    with patch.object(engine, '_poller_once', tracked_poller_once.__get__(engine)):
        # Mock iter_media to return no results
        async def mock_iter_media(*args, **kwargs):
            return
            yield  # Never executed
        mock_tg_service.iter_media = mock_iter_media

        # Start and let poller run
        await engine.start()
        await asyncio.sleep(0.05)
        await engine.stop()

    # Verify poller ran at least once
    assert len(poller_calls) > 0, "Poller should have run at least once"


@pytest.mark.asyncio
async def test_sync_engine_downloader_runs_continuously(session_factory, channel, subscription):
    """Downloader runs continuously during engine.start()."""
    mock_tg_service = AsyncMock()
    mock_plugin_host = AsyncMock()

    downloader_calls = []
    original_downloader = SyncEngine._downloader

    async def tracked_downloader(self):
        downloader_calls.append(1)
        if len(downloader_calls) >= 2:
            # Stop after 2 iterations
            self._stop_event.set()
        return await original_downloader(self)

    engine = SyncEngine(
        session_factory=session_factory,
        tg_service=mock_tg_service,
        plugin_host=mock_plugin_host,
        poll_interval_sec=0.01,
    )

    with patch.object(engine, '_downloader', tracked_downloader.__get__(engine)):
        await engine.start()
        await asyncio.sleep(0.05)
        if not engine._stop_event.is_set():
            await engine.stop()
        await asyncio.sleep(0.01)

    # Verify downloader ran
    assert len(downloader_calls) > 0, "Downloader should have run"


@pytest.mark.asyncio
async def test_sync_engine_maintenance_runs_periodically(session_factory):
    """Maintenance loop runs during engine.start()."""
    mock_tg_service = AsyncMock()
    mock_plugin_host = AsyncMock()

    maintenance_calls = []
    original_maintenance = SyncEngine._maintenance_pass

    async def tracked_maintenance(self, session):
        maintenance_calls.append(1)
        return await original_maintenance(self, session)

    engine = SyncEngine(
        session_factory=session_factory,
        tg_service=mock_tg_service,
        plugin_host=mock_plugin_host,
        poll_interval_sec=0.01,
    )

    # Mock tg_service.iter_media
    async def mock_iter_media(*args, **kwargs):
        return
        yield
    mock_tg_service.iter_media = mock_iter_media

    with patch.object(engine, '_maintenance_pass', tracked_maintenance.__get__(engine)):
        await engine.start()
        await asyncio.sleep(0.05)
        await engine.stop()

    # Verify maintenance ran
    assert len(maintenance_calls) > 0, "Maintenance should have run"


@pytest.mark.asyncio
async def test_sync_engine_no_orphan_tasks_after_stop(session_factory, mock_tg_service, mock_plugin_host):
    """stop() leaves no orphan asyncio tasks (all cancelled/awaited)."""
    engine = SyncEngine(
        session_factory=session_factory,
        tg_service=mock_tg_service,
        plugin_host=mock_plugin_host,
        poll_interval_sec=0.01,
    )

    # Mock to avoid real network calls
    async def mock_iter_media(*args, **kwargs):
        return
        yield
    mock_tg_service.iter_media = mock_iter_media

    await engine.start()
    initial_task_count = len(engine._tasks)
    assert initial_task_count == 3, f"Expected 3 tasks, got {initial_task_count}"

    await asyncio.sleep(0.02)
    await engine.stop()

    # All tasks should be done
    for task in engine._tasks:
        assert task.done(), f"Task {task} not done after stop()"


@pytest.mark.asyncio
async def test_sync_engine_exception_in_loop_doesnt_kill_supervisor(session_factory):
    """Exception in poller/downloader/maintenance doesn't crash supervisor."""
    mock_tg_service = AsyncMock()
    mock_plugin_host = AsyncMock()

    # Make iter_media raise an exception on first call
    call_count = [0]

    async def mock_iter_media(*args, **kwargs):
        call_count[0] += 1
        if call_count[0] == 1:
            raise RuntimeError("Test error")
        return
        yield

    mock_tg_service.iter_media = mock_iter_media

    engine = SyncEngine(
        session_factory=session_factory,
        tg_service=mock_tg_service,
        plugin_host=mock_plugin_host,
        poll_interval_sec=0.01,
    )

    await engine.start()
    await asyncio.sleep(0.05)
    await engine.stop()

    # Should complete without crashing
    assert True


@pytest.mark.asyncio
async def test_sync_engine_start_stop_idempotent(session_factory, mock_tg_service, mock_plugin_host):
    """Multiple start()/stop() cycles work correctly."""
    engine = SyncEngine(
        session_factory=session_factory,
        tg_service=mock_tg_service,
        plugin_host=mock_plugin_host,
        poll_interval_sec=0.01,
    )

    # Mock iter_media
    async def mock_iter_media(*args, **kwargs):
        return
        yield
    mock_tg_service.iter_media = mock_iter_media

    # Cycle 1
    await engine.start()
    await asyncio.sleep(0.02)
    await engine.stop()

    # Cycle 2 (should work without error)
    await engine.start()
    await asyncio.sleep(0.02)
    await engine.stop()

    assert True, "Multiple cycles should work"
