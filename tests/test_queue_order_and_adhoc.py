"""Deferred items: ad-hoc Browse downloads must not hide newer posts from
subscriptions (suspect C); the download queue can be reordered."""
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db.models import Base, Channel, MediaItem, MediaStatus, Subscription
from app.db.repositories import media
from tests.test_integration_api import test_app  # noqa: F401

NOW = datetime(2026, 11, 1, tzinfo=timezone.utc)


@pytest_asyncio.fixture
async def s():
    eng = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_sessionmaker(eng, class_=AsyncSession, expire_on_commit=False)() as session:
        session.add(Channel(id=1, tg_id=1, title="c"))
        session.add(Subscription(id=1, channel_id=1, storage_path="/m", rename_template="{f}"))
        await session.commit()
        yield session
    await eng.dispose()


def _item(i, sub, status=MediaStatus.PENDING, prio=None):
    return MediaItem(id=i, channel_id=1, tg_msg_id=i, subscription_id=sub, date_posted=NOW, status=status, priority=prio)


@pytest.mark.asyncio
async def test_adhoc_download_does_not_advance_subscription_cursor(s):
    s.add_all([_item(10, 1, MediaStatus.DOWNLOADED), _item(500, None, MediaStatus.DOWNLOADED)])
    await s.commit()
    assert await media.get_max_tg_msg_id(s, 1, None) == 10


@pytest.mark.asyncio
async def test_claim_pending_respects_priority(s):
    s.add_all([_item(1, 1), _item(2, 1, prio=5), _item(3, 1, prio=1)])
    await s.commit()
    claimed = await media.claim_pending(s, limit=2)
    assert [m.id for m in claimed] == [2, 3]


def test_reorder_endpoint(test_app):  # noqa: F811
    import asyncio
    with TestClient(test_app) as c:
        async def seed():
            async with test_app.state.async_session() as db:
                db.add(Channel(id=1, tg_id=1, title="c"))
                db.add_all([_item(1, None), _item(2, None), _item(3, None)])
                await db.commit()
        asyncio.run(seed())
        assert [q["media_id"] for q in c.get("/api/downloads/queued").json()] == [1, 2, 3]
        assert c.post("/api/downloads/reorder", json={"media_ids": [3, 1, 2]}).status_code == 200
        assert [q["media_id"] for q in c.get("/api/downloads/queued").json()] == [3, 1, 2]


@pytest.mark.asyncio
async def test_poll_adopts_adhoc_item_without_requeue(s):
    from unittest.mock import AsyncMock
    from app.sync.engine import SyncEngine
    from app.telegram.dtos import MediaDTO
    s.add(_item(500, None, MediaStatus.DOWNLOADED))
    await s.commit()
    dto = MediaDTO(tg_msg_id=500, channel_tg_id=1, topic_tg_id=None, caption="x", file_name="x.mkv",
                   mime="video/mp4", size_bytes=1, duration_sec=1, date_posted=NOW, thumb_b64=None,
                   reactions={}, comments_count=0, raw={})

    class Tg:
        client = None

        async def iter_media(self, *a, **k):
            yield dto

    factory = async_sessionmaker(s.bind, class_=AsyncSession, expire_on_commit=False)
    eng = SyncEngine(session_factory=factory, tg_service=Tg(), plugin_host=AsyncMock())
    sub = await s.get(Subscription, 1)
    await eng._poll_one_sub(s, sub)
    item = await s.get(MediaItem, 500)
    await s.refresh(item)
    assert item.status == MediaStatus.DOWNLOADED and item.subscription_id == 1
