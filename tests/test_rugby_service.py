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

    async def fetch_season(self, league_id, season):
        return [{
            "idEvent": "2309783", "strSeason": "2025-2026", "intRound": "1",
            "dateEvent": "2025-09-25", "idHomeTeam": "135207", "idAwayTeam": "135201",
            "strHomeTeam": "Sale Sharks", "strAwayTeam": "Gloucester",
            "intHomeScore": "27", "intAwayScore": "10",
            "strLeagueBadge": "https://x/leaguebadge.png",
        }]

    async def lookup_team(self, team_id):
        return {"strTeam": f"Team {team_id}", "strTeamAlternate": "Alt",
                "strStadium": "Ground", "strBadge": "https://x/b.png",
                "strLogo": "https://x/l.png", "strCountry": "England"}


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

    tokens = await svc.naming_tokens(item_id)
    if status == "auto":
        assert tokens["rugby_league"] == "English Prem Rugby"
        assert tokens["home"] == "Sale Sharks" and tokens["away"] == "Gloucester"
        assert tokens["rugby_season"] == "2025-2026" and tokens["rugby_sport"] == "union"
    else:
        assert tokens == {}  # needs_review withholds tokens until confirmed
