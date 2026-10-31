"""1.8.0: hourly poll stats feed the overview sync pulse."""
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db.models import Base
from app.sync import pulse

NOW = datetime(2026, 11, 1, 12, 30, tzinfo=timezone.utc)


@pytest_asyncio.fixture
async def s():
    eng = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_sessionmaker(eng, class_=AsyncSession, expire_on_commit=False)() as session:
        yield session
    await eng.dispose()


@pytest.mark.asyncio
async def test_record_aggregates_per_hour_and_series_fills_gaps(s):
    await pulse.record(s, 1, "ok", queued=2, now=NOW)
    await pulse.record(s, 1, "ok", now=NOW + timedelta(minutes=10))
    await pulse.record(s, 1, "down", now=NOW - timedelta(hours=2))
    out = await pulse.series(s, [1], hours=4, now=NOW)
    cells = out[1]
    assert len(cells) == 4
    assert cells[-1]["ok"] == 2 and cells[-1]["queued"] == 2
    assert cells[-3]["down"] == 1
    assert cells[0] == {"t": (NOW.replace(minute=0) - timedelta(hours=3)).isoformat(),
                        "ok": 0, "error": 0, "down": 0, "queued": 0}


@pytest.mark.asyncio
async def test_prune_old(s):
    await pulse.record(s, 1, "ok", now=NOW - timedelta(days=9))
    await pulse.prune(s, now=NOW)
    assert (await pulse.series(s, [1], hours=24 * 10, now=NOW))[1][0]["ok"] == 0
