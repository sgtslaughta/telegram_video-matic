"""Rugby v2: venue capture, browse enrichment, wizard preview, Jellyfin NFO actors."""

import pytest
import pytest_asyncio
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.models import Base, Channel, Subscription, MediaItem, MediaStatus
from app.sync.plugins import PluginContext
import app.rugby.models as rm
from app.rugby.service import RugbyService


@pytest_asyncio.fixture
async def factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture
def ctx(factory):
    return PluginContext(name="rugby", config={}, session_factory=factory)


async def _seed(factory, *, with_match=True, msg_id=7):
    """League + 2 teams + a fixture (+ optional matched media item)."""
    async with factory() as s:
        s.add(rm.RugbyLeague(id=4414, slug="english-prem-rugby",
                             name="English Prem Rugby", sport="union",
                             badge_url="https://x/league.png"))
        s.add(rm.RugbyTeam(id=135207, league_id=4414, name="Sale Sharks",
                           badge_url="https://x/sale.png"))
        s.add(rm.RugbyTeam(id=135201, league_id=4414, name="Gloucester",
                           badge_url="https://x/glos.png"))
        s.add(rm.RugbyFixture(
            id=2309783, league_id=4414, season="2025-2026", round="1",
            date=datetime(2025, 9, 25, tzinfo=timezone.utc),
            home_team_id=135207, away_team_id=135201,
            home_name="Sale Sharks", away_name="Gloucester",
            home_score=27, away_score=10, venue="Salford Community Stadium"))
        chan = Channel(tg_id=1, title="Rugby")
        s.add(chan)
        await s.flush()
        sub = Subscription(channel_id=chan.id, storage_path="/d",
                           rename_template="{rugby_league}/{home} vs {away}{ext}",
                           jellyfin_metadata=True)
        s.add(sub)
        await s.flush()
        item = MediaItem(channel_id=chan.id, tg_msg_id=msg_id, subscription_id=sub.id,
                         file_name="Sale Sharks v Gloucester.mp4",
                         date_posted=datetime(2025, 9, 25, tzinfo=timezone.utc),
                         status=MediaStatus.PENDING)
        s.add(item)
        await s.flush()
        if with_match:
            s.add(rm.RugbyMatch(media_id=item.id, fixture_id=2309783, league_id=4414,
                                season="2025-2026", round="1", home_name="Sale Sharks",
                                away_name="Gloucester", confidence=0.95, status="auto"))
        ids = (chan.id, sub.id, item.id)
        await s.commit()
    return ids


@pytest.mark.asyncio
async def test_enrichment_keyed_by_tg_msg_id(ctx, factory):
    chan_id, _sub, _item = await _seed(factory, msg_id=7)
    enr = await RugbyService(ctx).enrichment(chan_id)
    assert 7 in enr
    e = enr[7]
    assert e["home"] == "Sale Sharks" and e["away"] == "Gloucester"
    assert e["home_badge"] == "https://x/sale.png" and e["away_badge"] == "https://x/glos.png"
    assert e["venue"] == "Salford Community Stadium"
    assert e["home_score"] == 27 and e["away_score"] == 10
    assert e["league"] == "English Prem Rugby" and e["round"] == "1"


@pytest.mark.asyncio
async def test_enrichment_excludes_unmatched(ctx, factory):
    chan_id, _s, _i = await _seed(factory, with_match=False, msg_id=8)
    assert await RugbyService(ctx).enrichment(chan_id) == {}


@pytest.mark.asyncio
async def test_preview_matches_and_renders(ctx, factory):
    await _seed(factory, with_match=False)
    res = await RugbyService(ctx).preview(4414, "Sale Sharks v Gloucester highlights.mp4")
    assert res["matched"] is True and res["status"] == "auto"
    assert res["home"] == "Sale Sharks" and res["away"] == "Gloucester"
    assert res["home_badge"] == "https://x/sale.png"
    assert res["fixtures_count"] == 1 and res["teams_count"] == 2
    assert res["tokens"]["rugby_league"] == "English Prem Rugby"


@pytest.mark.asyncio
async def test_preview_no_match(ctx, factory):
    await _seed(factory, with_match=False)
    res = await RugbyService(ctx).preview(4414, "random cooking video.mp4")
    assert res["matched"] is False and res["status"] == "none"
    assert res["fixtures_count"] == 1  # still reports what's loaded


@pytest.mark.asyncio
async def test_write_jellyfin_nfo_has_team_actors(ctx, factory, tmp_path, monkeypatch):
    _c, _s, item_id = await _seed(factory)

    async def fake_logo(url, dest, **kw):
        Path(dest).write_bytes(b"img")
    monkeypatch.setattr("app.rugby.scraper.download_logo", fake_logo)

    video = tmp_path / "match.mp4"
    video.write_bytes(b"x")
    async with factory() as s:
        item = await s.get(MediaItem, item_id)
    await RugbyService(ctx).write_jellyfin(item, video)

    nfo = (tmp_path / "match.nfo").read_text()
    assert "<episodedetails>" in nfo
    assert "<title>Sale Sharks vs Gloucester</title>" in nfo
    assert "<genre>Rugby</genre>" in nfo
    # both teams as actors with their badge as thumb
    assert nfo.count("<actor>") == 2
    assert "<name>Sale Sharks</name>" in nfo and "<role>Home</role>" in nfo
    assert "<thumb>https://x/sale.png</thumb>" in nfo
    assert "Salford Community Stadium" in nfo  # venue in plot
    assert (tmp_path / "poster.jpg").exists()  # home badge poster still written
