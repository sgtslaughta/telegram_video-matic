"""Rugby v2: venue capture, browse enrichment, wizard preview, Jellyfin NFO actors."""

import pytest
import pytest_asyncio
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.models import Base, Channel, Subscription, MediaItem, MediaStatus, Topic
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


async def _seed(factory, *, with_match=True, msg_id=7,
                file_name="Sale Sharks v Gloucester.mp4"):
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
                         file_name=file_name,
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
async def test_path_for_builds_league_season_tree(ctx, factory):
    _c, _s, item_id = await _seed(factory)
    path = await RugbyService(ctx).path_for(item_id, ".mp4")
    assert path == "English Prem Rugby/2025-2026/Sale Sharks vs Gloucester.mp4"


@pytest.mark.asyncio
async def test_path_for_none_when_unmatched(ctx, factory):
    _c, _s, item_id = await _seed(factory, with_match=False)
    assert await RugbyService(ctx).path_for(item_id, ".mp4") is None


@pytest.mark.asyncio
async def test_enrichment_excludes_unmatched(ctx, factory):
    # Media whose filename matches no fixture is left out entirely.
    chan_id, _s, _i = await _seed(factory, with_match=False, msg_id=8,
                                  file_name="random cooking video.mp4")
    assert await RugbyService(ctx).enrichment(chan_id) == {}


@pytest.mark.asyncio
async def test_enrichment_matches_on_the_fly_without_stored_match(ctx, factory):
    # No rugby_match row, but the filename matches a loaded fixture -> enriched.
    chan_id, _s, _i = await _seed(factory, with_match=False, msg_id=9)
    enr = await RugbyService(ctx).enrichment(chan_id)
    assert 9 in enr
    assert enr[9]["home"] == "Sale Sharks" and enr[9]["away"] == "Gloucester"
    assert enr[9]["home_badge"] == "https://x/sale.png"
    assert enr[9]["venue"] == "Salford Community Stadium"


@pytest.mark.asyncio
async def test_detect_channel_leagues_from_titles(ctx, factory):
    chan_id, _s, _i = await _seed(factory)  # league 4414 "English Prem Rugby"
    async with factory() as s:
        s.add(rm.RugbyLeague(id=4430, slug="french-top-14",
                             name="French Top 14", sport="union"))
        s.add(rm.RugbyLeague(id=4551, slug="super-rugby",
                             name="Super Rugby", sport="union"))
        chan = await s.get(Channel, chan_id)
        for mid, fn in [(101, "Toulouse v Montpellier - Top 14 - 1st March 2026.mp4"),
                        (102, "Chiefs v Crusaders - Super Rugby Pacific Final.mp4"),
                        (103, "random cooking video.mp4")]:
            s.add(MediaItem(channel_id=chan.id, tg_msg_id=mid, file_name=fn,
                            date_posted=datetime(2026, 3, 1, tzinfo=timezone.utc),
                            status=MediaStatus.PENDING))
        await s.commit()
    ids = await RugbyService(ctx).detect_channel_leagues(chan_id)
    assert 4430 in ids and 4551 in ids  # Top 14 + Super Rugby from title hints
    # A "PREM" hint maps to the English Prem league too.
    async with factory() as s:
        chan = await s.get(Channel, chan_id)
        s.add(MediaItem(channel_id=chan.id, tg_msg_id=104,
                        file_name="Bath v Sale - PREM Round 1.mp4",
                        date_posted=datetime(2026, 3, 1, tzinfo=timezone.utc),
                        status=MediaStatus.PENDING))
        await s.commit()
    assert 4414 in await RugbyService(ctx).detect_channel_leagues(chan_id)


@pytest.mark.asyncio
async def test_detect_from_forum_topic_names(ctx, factory):
    """Forum topics named by competition are detected even with no cached media."""
    async with factory() as s:
        s.add(rm.RugbyLeague(id=4446, slug="urc", name="United Rugby Championship"))
        s.add(rm.RugbyLeague(id=4714, slug="six", name="Six Nations Championship"))
        chan = Channel(tg_id=1, title="Rugby")
        s.add(chan)
        await s.flush()
        s.add(Topic(channel_id=chan.id, tg_topic_id=10, title="URC"))
        s.add(Topic(channel_id=chan.id, tg_topic_id=11, title="Six Nations 2026"))
        s.add(Topic(channel_id=chan.id, tg_topic_id=12, title="General"))
        cid = chan.id
        await s.commit()
    ids = await RugbyService(ctx).detect_channel_leagues(cid)
    assert 4446 in ids and 4714 in ids  # from topic names, no media needed


@pytest.mark.asyncio
async def test_map_titles_to_leagues_from_live_titles(ctx, factory):
    # Detect leagues from arbitrary title strings (live TG, not cached media).
    async with factory() as s:
        s.add(rm.RugbyLeague(id=4446, slug="urc", name="United Rugby Championship"))
        s.add(rm.RugbyLeague(id=4714, slug="six-nations", name="Six Nations Championship"))
        s.add(rm.RugbyLeague(id=4430, slug="top-14", name="French Top 14"))
        await s.commit()
    ids = await RugbyService(ctx).map_titles_to_leagues([
        "Leinster v Munster - URC - Round 5.mp4",
        "France v England - Six Nations 2026.mp4",
        "Toulouse v Toulon - Top 14.mp4",
        "random clip.mp4",
    ])
    assert set(ids) == {4446, 4714, 4430}


@pytest.mark.asyncio
async def test_enrich_messages_matches_live_uncached(ctx, factory):
    """A live message (no cached media row) still matches loaded fixtures."""
    await _seed(factory, with_match=False)  # league 4414 + Sale v Gloucester fixture
    res = await RugbyService(ctx).enrich_messages([
        {"tg_msg_id": 555, "text": "Sale Sharks v Gloucester highlights.mp4",
         "date": None}])
    assert "555" not in res  # keyed by int internally
    assert 555 in res and res[555]["home"] == "Sale Sharks"
    assert res[555]["home_badge"] == "https://x/sale.png"


class _RoundApi:
    async def fetch_round(self, league_id, rnd, season):
        if rnd == 18:
            return [{"idEvent": "99", "strSeason": season, "intRound": "18",
                     "dateEvent": "2026-06-06", "idHomeTeam": "1", "idAwayTeam": "2",
                     "strHomeTeam": "Bath Rugby", "strAwayTeam": "Leicester Tigers"}]
        return []


@pytest.mark.asyncio
async def test_ondemand_fetch_single_lookup(ctx, factory):
    """A miss with a parseable league+round triggers one targeted round fetch."""
    async with factory() as s:
        s.add(rm.RugbyLeague(id=4414, slug="english-prem-rugby",
                             name="English Prem Rugby"))
        await s.commit()
    svc = RugbyService(ctx, api=_RoundApi())
    ok = await svc._ondemand_fetch(
        "Bath v Leicester - PREM Round 18 - 6th June 2026.mp4", None)
    assert ok is True
    async with factory() as s:
        fx = await s.get(rm.RugbyFixture, 99)
        assert fx is not None and fx.round == "18"
    # Second call for the same round is deduped (no second API hit needed).
    assert await svc._ondemand_fetch(
        "Bath v Leicester - PREM Round 18 - 6th June 2026.mp4", None) is False


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
