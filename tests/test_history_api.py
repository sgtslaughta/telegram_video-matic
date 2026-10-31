"""GET /api/history and /api/wanted/failed."""
import asyncio

from fastapi.testclient import TestClient

from app.db.models import Channel, DownloadJob, Event, MediaItem, MediaStatus
from test_integration_api import test_app  # noqa: F401  (fixture)
from datetime import datetime, timezone


def _seed(app):
    async def go():
        async with app.state.async_session() as s:
            ch = Channel(tg_id=1, title="c", is_forum=False)
            s.add(ch)
            await s.flush()
            def mk(i, st, **kw):
                return MediaItem(channel_id=ch.id, tg_msg_id=i, file_name=f"f{i}.mp4",
                                 date_posted=datetime.now(timezone.utc), status=st, **kw)
            a, b, c = mk(1, MediaStatus.DOWNLOADED), mk(2, MediaStatus.FAILED), mk(3, MediaStatus.SKIPPED, skip_reason="too small")
            s.add_all([a, b, c])
            await s.flush()
            s.add_all([
                Event(level="success", kind="download", media_id=a.id, message="Downloaded f1.mp4"),
                Event(level="error", kind="download", media_id=b.id, message="Download failed after 5 attempts: boom"),
                Event(level="info", kind="prune", media_id=a.id, message="Deleted (age)"),
                Event(level="success", kind="rugby", media_id=a.id, message="Matched A vs B"),
                Event(level="info", kind="drift", media_id=a.id, message="File missing on disk, re-queued"),
                Event(level="info", kind="sync", message="no media"),
                DownloadJob(media_id=b.id, status="failed", attempt=5, error="boom"),
            ])
            await s.commit()
            return a.id
    return asyncio.run(go())


def test_history_kinds_and_filters(test_app):  # noqa: F811
    with TestClient(test_app) as c:
        aid = _seed(test_app)
        rows = c.get("/api/history").json()
        assert sorted(r["kind"] for r in rows) == [
            "deleted", "downloaded", "failed", "matched", "other", "skipped"]
        sk = next(r for r in rows if r["kind"] == "skipped")
        assert sk["message"] == "too small" and sk["file_name"] == "f3.mp4"
        assert [r["kind"] for r in c.get("/api/history?kind=failed").json()] == ["failed"]
        assert len(c.get(f"/api/history?media_id={aid}").json()) == 4
        assert len(c.get("/api/history?limit=2&offset=1").json()) == 2


def test_wanted_failed(test_app):  # noqa: F811
    with TestClient(test_app) as c:
        _seed(test_app)
        rows = c.get("/api/wanted/failed").json()
        assert len(rows) == 1
        assert rows[0]["error"] == "boom" and rows[0]["attempt"] == 5
