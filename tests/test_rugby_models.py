"""Rugby plugin-owned models: schema + relationships create cleanly."""

import pytest
import pytest_asyncio
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.models import Base, Channel, Subscription, MediaItem, MediaStatus
import app.rugby.models as rm


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:", echo=False, poolclass=StaticPool
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as s:
        yield s


@pytest.mark.asyncio
async def test_league_team_fixture_roundtrip(session):
    league = rm.RugbyLeague(
        id=4414, slug="english-prem-rugby", name="English Prem Rugby",
        sport="union", country="England", category="Featured",
        badge_url="https://x/badge.png", tracked=True,
    )
    team = rm.RugbyTeam(
        id=135207, league_id=4414, name="Sale Sharks", short_name="SAL",
        alt_names=["Sale"], stadium="Salford", country="England",
        badge_url="https://x/sale.png", logo_url="https://x/salelogo.png",
    )
    fixture = rm.RugbyFixture(
        id=2309783, league_id=4414, season="2025-2026", round="1",
        date=datetime(2025, 9, 25, tzinfo=timezone.utc),
        home_team_id=135207, away_team_id=135201,
        home_name="Sale Sharks", away_name="Gloucester",
        home_score=27, away_score=10,
    )
    session.add_all([league, team, fixture])
    await session.commit()

    got = await session.get(rm.RugbyFixture, 2309783)
    assert got.home_name == "Sale Sharks" and got.season == "2025-2026"
    assert (await session.get(rm.RugbyTeam, 135207)).alt_names == ["Sale"]


@pytest.mark.asyncio
async def test_match_and_subscription_link_to_core(session):
    """rugby_match -> media_items and rugby_subscription -> subscriptions."""
    chan = Channel(tg_id=1, title="Rugby")
    session.add(chan)
    await session.flush()
    sub = Subscription(channel_id=chan.id, storage_path="/d", rename_template="{title}{ext}")
    session.add(sub)
    await session.flush()
    item = MediaItem(channel_id=chan.id, tg_msg_id=5,
                     date_posted=datetime.now(timezone.utc), status=MediaStatus.PENDING)
    session.add(item)
    await session.flush()

    session.add(rm.RugbySubscription(subscription_id=sub.id, league_id=4414))
    session.add(rm.RugbyMatch(
        media_id=item.id, fixture_id=None, league_id=4414, season="2025-2026",
        home_name="Sale Sharks", away_name="Gloucester", round="1",
        confidence=0.92, status="auto",
    ))
    await session.commit()

    rs = await session.get(rm.RugbySubscription, sub.id)
    assert rs.league_id == 4414
    rmatch = (await session.execute(
        rm.RugbyMatch.__table__.select().where(rm.RugbyMatch.media_id == item.id)
    )).first()
    assert rmatch.status == "auto"
