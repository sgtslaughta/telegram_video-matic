"""1.5.1: poller self-heals a dead Telegram connection; health reports it;
repeated errors collapse; polling is oldest-first."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from starlette.responses import Response

from app.api.routers import health
from app.db.models import Base, Event
from app.db.repositories import events
from app.sync.engine import SyncEngine


@pytest_asyncio.fixture
async def factory():
    eng = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield async_sessionmaker(eng, class_=AsyncSession, expire_on_commit=False)
    await eng.dispose()


def _tg(connected: bool, connect_side_effect=None):
    tg = MagicMock()
    tg.client = MagicMock()
    tg.client.is_connected = MagicMock(return_value=connected)
    tg.connect = AsyncMock(side_effect=connect_side_effect)
    return tg


def _engine(factory, tg):
    return SyncEngine(session_factory=factory, tg_service=tg, plugin_host=AsyncMock(), poll_interval_sec=300)


@pytest.mark.asyncio
async def test_reconnects_when_disconnected(factory):
    tg = _tg(connected=False)
    eng = _engine(factory, tg)
    assert await eng._ensure_connected() is True
    tg.connect.assert_awaited_once()


@pytest.mark.asyncio
async def test_backoff_after_failed_reconnect(factory):
    tg = _tg(connected=False, connect_side_effect=OSError("429"))
    eng = _engine(factory, tg)
    assert await eng._ensure_connected() is False
    assert await eng._ensure_connected() is False  # still inside backoff window
    assert tg.connect.await_count == 1
    assert eng._reconnect_delay == 30
    eng._next_reconnect_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    await eng._ensure_connected()
    assert eng._reconnect_delay == 60  # doubled
    eng._reconnect_delay = 600
    eng._next_reconnect_at = None
    await eng._ensure_connected()
    assert eng._reconnect_delay == 600  # capped


@pytest.mark.asyncio
async def test_poller_skips_and_does_not_mark_ok_when_down(factory):
    tg = _tg(connected=False, connect_side_effect=OSError("down"))
    eng = _engine(factory, tg)
    eng.last_ok_poll_at = None
    async with factory() as s:
        await eng._poller_once(s)
    assert eng.last_ok_poll_at is None
    tg.iter_media.assert_not_called()


@pytest.mark.asyncio
async def test_poller_marks_ok_when_connected(factory):
    eng = _engine(factory, _tg(connected=True))
    eng.last_ok_poll_at = None
    async with factory() as s:
        await eng._poller_once(s)
    assert eng.last_ok_poll_at is not None


def _app_state(engine, tg):
    return SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(engine=engine, tg_service=tg)))


@pytest.mark.asyncio
async def test_health_ok_without_telegram():
    r = Response()
    body = await health.health(_app_state(None, None), r)
    assert r.status_code == 200 and body["status"] == "ok"


@pytest.mark.asyncio
async def test_health_503_when_disconnected(factory):
    tg = _tg(connected=False)
    eng = _engine(factory, tg)
    eng.last_ok_poll_at = datetime.now(timezone.utc)
    r = Response()
    body = await health.health(_app_state(eng, tg), r)
    assert r.status_code == 503 and body["telegram"] == "disconnected"


@pytest.mark.asyncio
async def test_health_503_when_poll_stale(factory):
    tg = _tg(connected=True)
    eng = _engine(factory, tg)
    eng.last_ok_poll_at = datetime.now(timezone.utc) - timedelta(seconds=901)
    r = Response()
    body = await health.health(_app_state(eng, tg), r)
    assert r.status_code == 503 and body["status"] == "stale"


@pytest.mark.asyncio
async def test_health_200_when_fresh(factory):
    tg = _tg(connected=True)
    eng = _engine(factory, tg)
    eng.last_ok_poll_at = datetime.now(timezone.utc)
    r = Response()
    body = await health.health(_app_state(eng, tg), r)
    assert r.status_code == 200 and body["telegram"] == "connected"


@pytest.mark.asyncio
async def test_repeated_errors_collapse_even_when_interleaved(factory):
    async with factory() as s:
        for _ in range(3):
            await events.add(s, level="error", kind="sync", subscription_id=None, message="boom A")
            await events.add(s, level="error", kind="sync", subscription_id=None, message="boom B")
        await events.add(s, level="info", kind="sync", message="same info")
        await events.add(s, level="info", kind="sync", message="same info")
        rows = (await s.execute(select(Event).order_by(Event.id))).scalars().all()
    assert [(e.message, e.count) for e in rows] == [
        ("boom A", 3), ("boom B", 3), ("same info", 1), ("same info", 1)
    ]


@pytest.mark.asyncio
async def test_iter_media_reads_oldest_first():
    from app.telegram.service import TelegramService
    from app.telegram.dtos import ChannelDTO

    seen = {}

    async def fake_iter(entity, **kw):
        seen.update(kw)
        return
        yield  # pragma: no cover

    svc = TelegramService(account_repo=MagicMock())
    svc.client = MagicMock()
    svc.client.iter_messages = fake_iter
    svc._channel_input = AsyncMock(return_value="e")
    chan = ChannelDTO(tg_id=1, title="c", username=None, is_forum=False, photo_b64=None, raw={})
    async for _ in svc.iter_media(chan, None, since_msg_id=5):
        pass
    assert seen["reverse"] is True and seen["min_id"] == 5
