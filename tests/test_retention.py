"""1.7.0 retention: ages from content date, honors keep pins, caps mass deletes."""
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db.models import Base, Channel, Event, MediaItem, MediaStatus, Setting, Subscription
from app.sync import retention

NOW = datetime(2026, 11, 1, tzinfo=timezone.utc)


@pytest_asyncio.fixture
async def s():
    eng = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    f = async_sessionmaker(eng, class_=AsyncSession, expire_on_commit=False)
    async with f() as session:
        session.add(Channel(id=1, tg_id=1, title="c"))
        session.add(Subscription(id=1, channel_id=1, storage_path="/m", rename_template="{f}"))
        session.add(Subscription(id=2, channel_id=1, storage_path="/m", rename_template="{f}", retention_days=30))
        session.add(Setting(key="retention_days", value="90"))
        await session.commit()
        yield session
    await eng.dispose()


_n = [0]


async def _item(s, tmp_path, *, posted_days, content_days=None, downloaded_days=1, sub=1, keep=False, size=10):
    _n[0] += 1
    f = tmp_path / f"v{_n[0]}.mkv"
    f.write_bytes(b"x")
    it = MediaItem(channel_id=1, subscription_id=sub, tg_msg_id=_n[0], status=MediaStatus.DOWNLOADED,
                   date_posted=NOW - timedelta(days=posted_days),
                   content_date=NOW - timedelta(days=content_days) if content_days is not None else None,
                   downloaded_at=NOW - timedelta(days=downloaded_days), local_path=str(f),
                   keep=keep, size_bytes=size)
    s.add(it)
    await s.commit()
    return it


async def _plan(s, **kw):
    kw.setdefault("disk_used", 1)
    kw.setdefault("disk_total", 100)
    return await retention.plan(s, NOW, **kw)


@pytest.mark.asyncio
async def test_age_counts_from_content_date_not_download(s, tmp_path):
    old_match = await _item(s, tmp_path, posted_days=5, content_days=200, downloaded_days=1)
    fresh_import = await _item(s, tmp_path, posted_days=10, downloaded_days=200)
    ids = {p.item.id for p in await _plan(s)}
    assert old_match.id in ids and fresh_import.id not in ids


@pytest.mark.asyncio
async def test_sub_override_replaces_global(s, tmp_path):
    a = await _item(s, tmp_path, posted_days=45, sub=2)  # 30d sub → prune
    b = await _item(s, tmp_path, posted_days=45, sub=1)  # 90d global → keep
    ids = {p.item.id for p in await _plan(s)}
    assert a.id in ids and b.id not in ids


@pytest.mark.asyncio
async def test_keep_pins_item_and_subscription(s, tmp_path):
    a = await _item(s, tmp_path, posted_days=400, keep=True)
    sub = await s.get(Subscription, 2)
    sub.keep = True
    await s.commit()
    b = await _item(s, tmp_path, posted_days=400, sub=2)
    assert {p.item.id for p in await _plan(s)}.isdisjoint({a.id, b.id})


@pytest.mark.asyncio
async def test_disk_pressure_prunes_oldest_until_under(s, tmp_path):
    items = [await _item(s, tmp_path, posted_days=d, size=10) for d in (10, 20, 30)]
    plan = await _plan(s, disk_used=95, disk_total=100, disk_pct_limit=80)
    assert [p.item.id for p in plan] == [items[2].id, items[1].id]  # oldest first, 95→75
    assert all(p.reason == "disk" for p in plan)


@pytest.mark.asyncio
async def test_apply_marks_pruned_and_deletes_file(s, tmp_path):
    it = await _item(s, tmp_path, posted_days=400)
    path = it.local_path
    res = await retention.apply(s, await _plan(s))
    await s.refresh(it)
    assert res == {"pruned": 1, "paused": False}
    assert it.status == MediaStatus.PRUNED and it.local_path is None
    import os
    assert not os.path.exists(path)


@pytest.mark.asyncio
async def test_mass_delete_pauses_until_confirmed(s, tmp_path):
    for _ in range(4):
        await _item(s, tmp_path, posted_days=400)
    plan = await _plan(s)
    res = await retention.apply(s, plan, cap=3)
    assert res == {"pruned": 0, "paused": True}
    rows = (await s.execute(select(MediaItem).where(MediaItem.status == MediaStatus.PRUNED))).all()
    assert rows == []
    ev = (await s.execute(select(Event).where(Event.kind == "prune"))).scalars().all()
    assert ev and ev[-1].level == "warning"
    res = await retention.apply(s, plan, cap=3, confirmed=True)
    assert res == {"pruned": 4, "paused": False}


@pytest.mark.asyncio
async def test_preview_shows_next_7_days(s, tmp_path):
    soon = await _item(s, tmp_path, posted_days=85)
    later = await _item(s, tmp_path, posted_days=60)
    prev = await retention.preview(s, NOW, days=7)
    assert [i["id"] for i in prev["items"]] == [soon.id] and later.id


def test_sweep_orphans_removes_leftover_metadata(tmp_path):
    """Sidecars of a deleted video, then folders holding only metadata, go;
    anything beside a surviving video, or any unknown file, stays."""
    keep = tmp_path / "Prem" / "Season 2026"
    keep.mkdir(parents=True)
    for n in ("a.mp4", "a.nfo", "a-thumb.jpg", "season.nfo"):
        (keep / n).write_bytes(b"x")
    gone = tmp_path / "Prem" / "Season 25"
    gone.mkdir()
    for n in ("b.nfo", "b-thumb.jpg", "season.nfo", "poster.jpg"):
        (gone / n).write_bytes(b"x")
    mine = tmp_path / "Notes"
    mine.mkdir()
    (mine / "readme.txt").write_bytes(b"x")

    files, dirs = retention.sweep_orphans(str(tmp_path))
    assert (files, dirs) == (2, 1)
    assert not gone.exists()
    assert sorted(p.name for p in keep.iterdir()) == ["a-thumb.jpg", "a.mp4", "a.nfo", "season.nfo"]
    assert (mine / "readme.txt").exists() and (tmp_path / "Prem").exists()


@pytest.mark.asyncio
async def test_prune_deletes_sidecars(s, tmp_path):
    it = await _item(s, tmp_path, posted_days=200)
    for suf in (".nfo", "-thumb.jpg"):
        (tmp_path / f"{it.local_path.rsplit('/', 1)[1].rsplit('.', 1)[0]}{suf}").write_bytes(b"x")
    await retention.apply(s, await retention.plan(s, NOW, disk_used=0, disk_total=0))
    assert list(tmp_path.iterdir()) == []
