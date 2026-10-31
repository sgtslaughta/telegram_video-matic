"""POST /api/subscriptions/{id}/rescan and /preview-filter."""
import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.db.models import Channel, MediaItem, Subscription
from app.sync.engine import SyncEngine
from app.telegram.dtos import MediaDTO
from test_integration_api import test_app  # noqa: F401


def _dto(i, name, size=10 * 1024 * 1024):
    return MediaDTO(tg_msg_id=i, channel_tg_id=1, topic_tg_id=None, caption="cap" * 100,
                    file_name=name, mime="video/mp4", size_bytes=size, duration_sec=1,
                    date_posted=datetime.now(timezone.utc), thumb_b64=None,
                    reactions={}, comments_count=0, raw={})


def _tg(dtos):
    tg = MagicMock()
    tg.disconnect = AsyncMock()
    calls = []

    async def it(chan, topic=None, since_msg_id=None, **kw):
        calls.append(kw)
        for d in dtos:
            yield d
    tg.iter_media = it
    tg.calls = calls
    return tg


def _seed(app):
    async def go():
        async with app.state.async_session() as s:
            ch = Channel(tg_id=1, title="c", is_forum=False)
            s.add(ch)
            await s.flush()
            sub = Subscription(channel_id=ch.id, storage_path="/tmp", rename_template="{name}",
                               filter_regex="keep", filter_mode="include")
            s.add(sub)
            s.add(MediaItem(channel_id=ch.id, tg_msg_id=1, file_name="keep_old.mp4",
                            date_posted=datetime.now(timezone.utc)))
            await s.commit()
            return ch.id, sub.id
    return asyncio.run(go())


def test_rescan_upserts_missing_only(test_app):
    with TestClient(test_app) as c:
        _, sub_id = _seed(test_app)
        tg = _tg([_dto(1, "keep_old.mp4"), _dto(2, "keep_new.mp4"), _dto(3, "other.mp4")])
        test_app.state.tg_service = tg
        test_app.state.engine = SyncEngine(test_app.state.async_session, tg, AsyncMock())
        r = c.post(f"/api/subscriptions/{sub_id}/rescan", json={"days": 7})
        assert r.json() == {"found": 2, "queued": 1, "skipped": 1}
        assert "since_date" in tg.calls[0]
        assert c.post(f"/api/subscriptions/{sub_id}/rescan", json={"days": 0}).status_code == 422
        assert c.post("/api/subscriptions/999/rescan", json={"days": 1}).status_code == 404


def test_preview_filter_no_writes(test_app):
    with TestClient(test_app) as c:
        ch_id, _ = _seed(test_app)
        tg = _tg([_dto(5, "keep.mp4"), _dto(6, "nope.mp4"), _dto(7, "keep_big.mp4", 900 * 1024 * 1024)])
        test_app.state.tg_service = tg
        async def count():
            async with test_app.state.async_session() as s:
                return (await s.execute(select(func.count()).select_from(MediaItem))).scalar()
        before = asyncio.run(count())
        r = c.post("/api/subscriptions/preview-filter", json={
            "channel_id": ch_id, "filter_regex": "keep", "filter_mode": "include", "max_size_mb": 100})
        rows = r.json()
        assert [x["would"] for x in rows] == ["download", "skip", "skip"]
        assert len(rows[0]["caption"]) == 200 and rows[1]["reason"]
        assert tg.calls[0] == {"limit": 50}
        assert asyncio.run(count()) == before
        bad = c.post("/api/subscriptions/preview-filter", json={"channel_id": ch_id, "filter_regex": "(", "filter_mode": "include"})
        assert bad.status_code == 400
