"""A subscription can follow several leagues (e.g. one topic carrying both
the Champions Cup and the Challenge Cup)."""
import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import app.rugby.models as rm
from app.db.models import Base, Channel, Subscription
from app.rugby.service import RugbyService
from app.sync.plugins import PluginContext
from tests.test_integration_api import test_app  # noqa: F401


@pytest_asyncio.fixture
async def factory():
    eng = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    f = async_sessionmaker(eng, class_=AsyncSession, expire_on_commit=False)
    async with f() as s:
        s.add_all([Channel(id=1, tg_id=1, title="c"), rm.RugbyLeague(id=4550, slug="cc", name="Champions Cup"),
                   rm.RugbyLeague(id=5418, slug="ch", name="Challenge Cup"),
                   Subscription(id=3, channel_id=1, storage_path="/m", rename_template="{title}")])
        await s.commit()
    yield f
    await eng.dispose()


@pytest.fixture
def svc(factory):
    return RugbyService(PluginContext(name="rugby", config={}, session_factory=factory))


@pytest.mark.asyncio
async def test_link_and_read_several_leagues(svc):
    await svc.set_links(3, [4550, 5418])
    assert sorted(await svc.get_subscription_leagues(3)) == [4550, 5418]
    await svc.set_links(3, [5418])
    assert await svc.get_subscription_leagues(3) == [5418]
    await svc.set_links(3, [])
    assert await svc.get_subscription_leagues(3) == []


@pytest.mark.asyncio
async def test_is_rugby_subscription(svc):
    assert await svc.is_rugby_subscription(3) is False
    await svc.set_links(3, [4550, 5418])
    assert await svc.is_rugby_subscription(3) is True


@pytest.mark.asyncio
async def test_migrates_old_single_league_table():
    """Old schema: subscription_id was the sole primary key."""
    eng = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    async with eng.begin() as conn:
        await conn.execute(text(
            "CREATE TABLE rugby_subscriptions (subscription_id INTEGER PRIMARY KEY, league_id INTEGER NOT NULL,"
            " created_at DATETIME, updated_at DATETIME)"))
        await conn.execute(text("INSERT INTO rugby_subscriptions VALUES (1, 4414, NULL, NULL), (2, 5479, NULL, NULL)"))
    from app.rugby.models import migrate_subscription_links
    async with eng.begin() as conn:
        await conn.run_sync(migrate_subscription_links)
        await conn.run_sync(migrate_subscription_links)  # idempotent
        await conn.execute(text("INSERT INTO rugby_subscriptions (subscription_id, league_id) VALUES (1, 5418)"))
        rows = (await conn.execute(text("SELECT subscription_id, league_id FROM rugby_subscriptions ORDER BY 1, 2"))).all()
    assert [tuple(r) for r in rows] == [(1, 4414), (1, 5418), (2, 5479)]
    await eng.dispose()


def test_api_put_get_league_ids(test_app):  # noqa: F811
    from fastapi.testclient import TestClient
    import app.rugby.service as rs
    calls = []

    async def fake_fetch(self, lid):
        calls.append(lid)
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(rs.RugbyService, "deep_fetch", fake_fetch)
    try:
        with TestClient(test_app) as c:
            host = test_app.state.plugin_host
            entry = next((e for e in host.entries if e.name == "rugby"), None)
            if entry is None or not entry.enabled:
                c.patch("/api/plugins/rugby", json={"enabled": True})
            import asyncio
            async def seed():
                async with test_app.state.async_session() as s:
                    s.add_all([Channel(id=1, tg_id=1, title="c"),
                               Subscription(id=3, channel_id=1, storage_path="/m", rename_template="{title}")])
                    for lid in (4550, 5418):  # plugin may already have seeded the catalog
                        if await s.get(rm.RugbyLeague, lid) is None:
                            s.add(rm.RugbyLeague(id=lid, slug=str(lid), name=str(lid)))
                    await s.commit()
            asyncio.run(seed())
            r = c.put("/api/plugins/rugby/subscriptions/3", json={"league_ids": [4550, 5418]})
            assert r.status_code == 200, r.text
            assert sorted(c.get("/api/plugins/rugby/subscriptions/3").json()["league_ids"]) == [4550, 5418]
            assert sorted(calls) == [4550, 5418]
    finally:
        monkeypatch.undo()
