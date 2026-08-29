"""RugbyService: catalog refresh (seed fallback), deep fetch, match, tokens."""

import pytest
import pytest_asyncio
from datetime import datetime, timezone
from sqlalchemy import select, func
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


class FakeApi:
    async def list_seasons(self, league_id):
        return ["2025-2026"]

    _EVENT = {
        "idEvent": "2309783", "strSeason": "2025-2026", "intRound": "1",
        "dateEvent": "2025-09-25", "idHomeTeam": "135207", "idAwayTeam": "135201",
        "strHomeTeam": "Sale Sharks", "strAwayTeam": "Gloucester",
        "intHomeScore": "27", "intAwayScore": "10",
        "strLeagueBadge": "https://x/leaguebadge.png",
    }

    async def fetch_season(self, league_id, season):
        return [self._EVENT]

    async def fetch_round(self, league_id, rnd, season):
        return [self._EVENT] if rnd == 1 and season == "2025-2026" else []

    async def fetch_past_league(self, league_id):
        # Same final the playoff sweep also returns -> exercises dedup.
        return [self._EVENT]

    async def lookup_team(self, team_id):
        return {"strTeam": f"Team {team_id}", "strTeamAlternate": "Alt",
                "strStadium": "Ground", "strBadge": "https://x/b.png",
                "strLogo": "https://x/l.png", "strCountry": "England"}


class RateLimitedApi(FakeApi):
    async def fetch_round(self, league_id, rnd, season):
        from app.rugby.api import RugbyApiError
        raise RugbyApiError("eventsround.php", "HTTP 429: rate limited")

    async def fetch_past_league(self, league_id):
        return []


def test_event_datetime_extracts_time():
    """Kick-off time comes from strTimestamp / dateEvent+strTime, not just date."""
    from app.rugby.service import _event_datetime
    d = _event_datetime({"dateEvent": "2026-06-06", "strTime": "14:00:00"})
    assert (d.hour, d.minute) == (14, 0)
    d2 = _event_datetime({"strTimestamp": "2026-06-06T19:45:00+00:00",
                          "dateEvent": "2026-06-06"})
    assert d2.hour == 19 and d2.minute == 45
    d3 = _event_datetime({"dateEvent": "2026-06-06"})  # date only still works
    assert d3.year == 2026 and d3.hour == 0
    assert _event_datetime({}) is None


def test_recent_seasons_both_formats():
    """Scan must cover split-year (northern) AND single-year (southern) seasons."""
    from app.rugby.service import _recent_seasons
    seasons = _recent_seasons()
    split = [s for s in seasons if "-" in s]
    single = [s for s in seasons if "-" not in s]
    assert len(split) == 2 and len(single) == 2
    for s in split:  # contiguous "YYYY-YYYY"
        a, b = s.split("-")
        assert int(b) == int(a) + 1
    for s in single:  # bare "YYYY"
        assert s.isdigit() and len(s) == 4


@pytest.mark.asyncio
async def test_refresh_catalog_empty_scrape_uses_seed(ctx, factory, monkeypatch):
    """A scrape that returns [] (not an exception) must still seed the catalog."""
    async def empty():
        return []
    monkeypatch.setattr("app.rugby.scraper.fetch_league_catalog", empty)
    n = await RugbyService(ctx, api=FakeApi()).refresh_catalog()
    assert n >= 50


@pytest.mark.asyncio
async def test_refresh_catalog_falls_back_to_seed(ctx, factory, monkeypatch):
    async def boom():
        raise RuntimeError("network down")
    monkeypatch.setattr("app.rugby.scraper.fetch_league_catalog", boom)

    n = await RugbyService(ctx, api=FakeApi()).refresh_catalog()
    assert n >= 50
    async with factory() as s:
        count = (await s.execute(select(func.count()).select_from(rm.RugbyLeague))).scalar()
        assert await s.get(rm.RugbyLeague, 4414) is not None
    assert count >= 50
    assert ctx.health["status"]["leagues"] >= 50


@pytest.mark.asyncio
async def test_deep_fetch_flags_rate_limited(ctx, factory):
    """Rate-limited rounds set status.rate_limited (amber) without a hard error."""
    async with factory() as s:
        s.add(rm.RugbyLeague(id=4414, slug="x", name="X"))
        await s.commit()
    await RugbyService(ctx, api=RateLimitedApi()).deep_fetch(4414)
    assert ctx.health["status"].get("rate_limited") is True
    assert ctx.health["last_error"] is None  # amber, not red


@pytest.mark.asyncio
async def test_deep_fetch_reports_sync_progress(ctx, factory):
    """A standalone deep_fetch flips syncing on then off with done=total=1."""
    async with factory() as s:
        s.add(rm.RugbyLeague(id=4414, slug="x", name="English Prem Rugby"))
        await s.commit()
    await RugbyService(ctx, api=FakeApi()).deep_fetch(4414)
    st = ctx.health["status"]
    assert st["syncing"] is False
    assert st["sync_done"] == 1 and st["sync_total"] == 1
    assert st["sync_current"] == "English Prem Rugby"


@pytest.mark.asyncio
async def test_deep_fetch_loads_fixtures_and_teams(ctx, factory):
    async with factory() as s:
        s.add(rm.RugbyLeague(id=4414, slug="english-prem-rugby", name="English Prem Rugby"))
        await s.commit()

    await RugbyService(ctx, api=FakeApi()).deep_fetch(4414)

    async with factory() as s:
        fx = await s.get(rm.RugbyFixture, 2309783)
        assert fx.home_name == "Sale Sharks" and fx.round == "1"
        assert await s.get(rm.RugbyTeam, 135207) is not None
        league = await s.get(rm.RugbyLeague, 4414)
        assert league.tracked is True and league.badge_url == "https://x/leaguebadge.png"


@pytest.mark.asyncio
async def test_match_item_and_naming_tokens(ctx, factory):
    async with factory() as s:
        s.add(rm.RugbyLeague(id=4414, slug="english-prem-rugby",
                             name="English Prem Rugby", sport="union"))
        s.add(rm.RugbyFixture(
            id=2309783, league_id=4414, season="2025-2026", round="1",
            date=datetime(2025, 9, 25, tzinfo=timezone.utc),
            home_name="Sale Sharks", away_name="Gloucester"))
        chan = Channel(tg_id=1, title="Rugby")
        s.add(chan)
        await s.flush()
        sub = Subscription(channel_id=chan.id, storage_path="/d",
                           rename_template="{rugby_league}/{home} vs {away}{ext}")
        s.add(sub)
        await s.flush()
        item = MediaItem(channel_id=chan.id, tg_msg_id=7, subscription_id=sub.id,
                         file_name="Sale Sharks v Gloucester.mp4",
                         date_posted=datetime(2025, 9, 25, tzinfo=timezone.utc),
                         status=MediaStatus.PENDING)
        s.add(item)
        await s.flush()
        s.add(rm.RugbySubscription(subscription_id=sub.id, league_id=4414))
        await s.commit()
        sub_id, item_id = sub.id, item.id

    svc = RugbyService(ctx, api=FakeApi())
    async with factory() as s:
        item = await s.get(MediaItem, item_id)
    status = await svc.match_item(item)
    assert status in ("auto", "needs_review")

    # match_item now surfaces every outcome to the activity feed.
    async with factory() as s:
        from app.db.models import Event
        evs = (await s.execute(
            select(Event).where(Event.kind == "rugby"))).scalars().all()
    assert evs and any(
        ("Matched" in e.message) or ("Needs review" in e.message) for e in evs)

    tokens = await svc.naming_tokens(item_id)
    if status == "auto":
        assert tokens["rugby_league"] == "English Prem Rugby"
        assert tokens["home"] == "Sale Sharks" and tokens["away"] == "Gloucester"
        assert tokens["rugby_season"] == "2025-2026" and tokens["rugby_sport"] == "union"
    else:
        assert tokens == {}  # needs_review withholds tokens until confirmed


def test_episode_number_unique_per_game_in_round():
    """Round number alone collides (Jellyfin merges the round into one episode);
    round*100 + slot keeps each game distinct while preserving round order."""
    from types import SimpleNamespace
    from app.rugby.service import _episode_number

    m = SimpleNamespace(round="2")
    e1, lbl = _episode_number(m, None, slot=1)
    e2, _ = _episode_number(m, None, slot=2)
    e3, _ = _episode_number(m, None, slot=3)
    assert (e1, e2, e3) == (201, 202, 203)   # distinct, ordered
    assert lbl == "Round 2"
    # Later rounds sort after earlier ones regardless of slot.
    r18, _ = _episode_number(SimpleNamespace(round="18"), None, slot=1)
    assert r18 > e3

    # Finals (non-numeric) land after the regular season and stay distinct.
    fx = SimpleNamespace(date=datetime(2026, 6, 1, tzinfo=timezone.utc))
    f1, flbl = _episode_number(SimpleNamespace(round="Final"), fx, slot=1)
    f2, _ = _episode_number(SimpleNamespace(round="Final"), fx, slot=2)
    assert f1 != f2 and f1 > r18 and flbl == "Final"


@pytest.mark.asyncio
async def test_rematch_picks_up_fixtures_that_arrived_after_download(ctx, factory):
    """Matching only runs at discovery, so a fixture fetched later can never
    attach on its own — rematch() is the catch-up pass."""
    async with factory() as s:
        s.add(rm.RugbyLeague(id=4414, slug="english-prem-rugby",
                             name="English Prem Rugby", sport="union"))
        chan = Channel(tg_id=1, title="Rugby")
        s.add(chan)
        await s.flush()
        sub = Subscription(channel_id=chan.id, storage_path="/d",
                           rename_template="{title}{ext}")
        s.add(sub)
        await s.flush()
        # Downloaded while no fixture existed -> no match row was ever written.
        unmatched = MediaItem(channel_id=chan.id, tg_msg_id=7, subscription_id=sub.id,
                              file_name="Sale Sharks v Gloucester.mp4",
                              date_posted=datetime(2025, 9, 25, tzinfo=timezone.utc),
                              status=MediaStatus.DOWNLOADED)
        # Already matched: rematch must leave it alone.
        done = MediaItem(channel_id=chan.id, tg_msg_id=8, subscription_id=sub.id,
                         file_name="Bath v Saracens.mp4",
                         date_posted=datetime(2025, 9, 25, tzinfo=timezone.utc),
                         status=MediaStatus.DOWNLOADED)
        s.add_all([unmatched, done])
        await s.flush()
        s.add(rm.RugbyMatch(media_id=done.id, status="auto", league_id=4414))
        s.add(rm.RugbySubscription(subscription_id=sub.id, league_id=4414))
        await s.commit()
        unmatched_id, done_id = unmatched.id, done.id

    svc = RugbyService(ctx, api=FakeApi())
    assert await svc.rematch() == {"scanned": 1, "matched": 0, "review": 0, "filed": 0}

    # The fixture lands (deep fetch, newly tracked league) — now it can match.
    async with factory() as s:
        s.add(rm.RugbyFixture(
            id=2309783, league_id=4414, season="2025-2026", round="1",
            date=datetime(2025, 9, 25, tzinfo=timezone.utc),
            home_name="Sale Sharks", away_name="Gloucester"))
        await s.commit()

    result = await svc.rematch()
    assert result["scanned"] == 1 and result["matched"] == 1

    async with factory() as s:
        rows = {m.media_id: m for m in (await s.execute(select(rm.RugbyMatch))).scalars()}
    assert rows[unmatched_id].home_name == "Sale Sharks"
    assert rows[done_id].home_name is None  # untouched


@pytest.mark.asyncio
async def test_match_falls_back_to_other_tracked_leagues(ctx, factory):
    """A forum topic mixes competitions, so a miss in the bound league retries
    across every tracked league — but only ever as needs_review."""
    async with factory() as s:
        s.add(rm.RugbyLeague(id=5852, slug="nations", name="Nations Championship",
                             sport="union", tracked=True))
        s.add(rm.RugbyLeague(id=5479, slug="friendlies", sport="union",
                             name="Rugby Union International Friendlies", tracked=True))
        # Only the *unbound* league has the fixture.
        s.add(rm.RugbyFixture(
            id=99, league_id=5479, season="2026", round="0",
            date=datetime(2026, 8, 25, tzinfo=timezone.utc),
            home_name="Lions", away_name="New Zealand Rugby"))
        chan = Channel(tg_id=1, title="Rugby")
        s.add(chan)
        await s.flush()
        sub = Subscription(channel_id=chan.id, storage_path="/d",
                           rename_template="{title}{ext}")
        s.add(sub)
        await s.flush()
        item = MediaItem(channel_id=chan.id, tg_msg_id=9, subscription_id=sub.id,
                         file_name="2026 08 25 Lions v New Zealand [Ellis Park].mp4",
                         date_posted=datetime(2026, 8, 25, tzinfo=timezone.utc),
                         status=MediaStatus.DOWNLOADED)
        s.add(item)
        await s.flush()
        s.add(rm.RugbySubscription(subscription_id=sub.id, league_id=5852))
        await s.commit()
        item_id = item.id

    svc = RugbyService(ctx, api=FakeApi())
    async with factory() as s:
        item = await s.get(MediaItem, item_id)
    status = await svc.match_item(item)

    assert status == "needs_review"  # never auto-files across the binding
    async with factory() as s:
        row = (await s.execute(
            select(rm.RugbyMatch).where(rm.RugbyMatch.media_id == item_id)
        )).scalar_one()
    assert row.league_id == 5479  # the fixture's league, not the subscription's
    assert row.home_name == "Lions" and row.away_name == "New Zealand Rugby"


@pytest.mark.asyncio
async def test_deep_fetch_scans_round_zero(ctx, factory):
    """Friendlies, tours and one-off internationals are all round 0 upstream —
    a scan starting at round 1 sees none of them."""
    class RoundZeroApi(FakeApi):
        _FRIENDLY = {
            "idEvent": "5001", "strSeason": "2026", "intRound": "0",
            "dateEvent": "2026-08-15", "idHomeTeam": "1", "idAwayTeam": "2",
            "strHomeTeam": "Australia Rugby", "strAwayTeam": "Japan Rugby",
        }

        async def fetch_round(self, league_id, rnd, season):
            return [self._FRIENDLY] if rnd == 0 and season == "2026" else []

        async def fetch_past_league(self, league_id):
            return []

    async with factory() as s:
        s.add(rm.RugbyLeague(id=5479, slug="friendlies", sport="union",
                             name="Rugby Union International Friendlies"))
        await s.commit()

    svc = RugbyService(ctx, api=RoundZeroApi())
    await svc.deep_fetch(5479, season="2026")

    async with factory() as s:
        fx = (await s.execute(select(rm.RugbyFixture))).scalars().all()
    assert [(f.home_name, f.away_name, f.round) for f in fx] == [
        ("Australia Rugby", "Japan Rugby", "0")]
