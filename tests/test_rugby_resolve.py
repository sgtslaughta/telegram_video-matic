"""Rugby resolution: API sweep, topic history, fallback folders, import, dry runs."""

from datetime import datetime, timezone

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import app.rugby.models as rm
from app.db.models import Base, Channel, MediaItem, MediaStatus, Topic
from app.rugby import filing, matcher
from app.rugby.service import RugbyService
from app.sync.plugins import PluginContext

UTC = timezone.utc


@pytest_asyncio.fixture
async def factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture
def ctx(factory, tmp_path):
    return PluginContext(name="rugby", config={}, session_factory=factory,
                         media_root=str(tmp_path))


class NoApi:
    calls: list = []

    async def fetch_round(self, league_id, rnd, season):
        self.calls.append((league_id, rnd, season))
        return []

    async def search_events(self, name):
        return []


def test_title_date_repairs_stale_year_and_parses_iso():
    up = datetime(2026, 1, 24, 20, tzinfo=UTC)
    assert matcher.title_date("Sale v Northampton - PREM - 24th January 2025.mp4",
                              up).year == 2026
    assert matcher.title_date("2026 08 07 Stormers v All Blacks.mp4", None) == \
        datetime(2026, 8, 7, tzinfo=UTC)
    assert matcher.split_teams("2026 08 07 Stormers v All Blacks [Cape Town].mp4") == \
        ("Stormers", "All Blacks")
    assert matcher.split_teams("Aregentina_v_South_Africa_Mens_International.mp4") == \
        ("Aregentina", "South Africa Mens International")
    assert matcher.split_teams("2026 08 15 Bulls [Pretoria].mp4") is None


def test_ambiguous_winner_needs_review_and_prior_lifts():
    a = {"id": 1, "league_id": 1, "home_name": "Bath Rugby", "away_name": "Sale Sharks",
         "round": "3", "date": datetime(2026, 10, 1, tzinfo=UTC), "league_name": "X"}
    b = dict(a, id=2, league_id=2)
    # Same game in two leagues, both date-corroborated -> a human picks.
    assert matcher.match("Bath v Sale - 1st October 2026", None, [a, b])[2] == "needs_review"
    # Topic history for league 2 breaks the tie.
    fx, _c, st = matcher.match("Bath v Sale - 1st October 2026", None, [a, b],
                               prior_league=2)
    assert (fx["id"], st) == (2, "auto")


async def _seed_topic(factory, title="Premiership", history=3):
    """League 4414 + a topic whose `history` videos all matched it."""
    async with factory() as s:
        s.add(rm.RugbyLeague(id=4414, slug="prem", name="English Prem Rugby",
                             tracked=True))
        s.add(rm.RugbyFixture(id=1, league_id=4414, season="2025-2026", round="18",
                              date=datetime(2026, 6, 6, tzinfo=UTC),
                              home_name="Bath Rugby", away_name="Leicester Tigers"))
        ch = Channel(tg_id=5, title="RTL Patreon", is_forum=True)
        s.add(ch)
        await s.flush()
        t = Topic(channel_id=ch.id, tg_topic_id=1, title=title)
        s.add(t)
        await s.flush()
        for i in range(history):
            it = MediaItem(channel_id=ch.id, topic_id=t.id, tg_msg_id=100 + i,
                           file_name=f"old{i}.mp4", status=MediaStatus.DOWNLOADED,
                           date_posted=datetime(2026, 6, 6, tzinfo=UTC))
            s.add(it)
            await s.flush()
            s.add(rm.RugbyMatch(media_id=it.id, league_id=4414, status="auto",
                                fixture_id=1))
        item = MediaItem(channel_id=ch.id, topic_id=t.id, tg_msg_id=1,
                         file_name="Harlequins v Northampton - PREM - 12th September 2026.mp4",
                         status=MediaStatus.DOWNLOADED,
                         date_posted=datetime(2026, 9, 12, 18, tzinfo=UTC))
        s.add(item)
        await s.commit()
        return item


@pytest.mark.asyncio
async def test_unmatched_item_files_under_topic_league(ctx, factory):
    """Pre-season games aren't in the API: the topic's history decides the
    folder, split-year season by date, raw filename."""
    item = await _seed_topic(factory)
    svc = RugbyService(ctx, api=NoApi())
    assert (await svc.resolve_item(item))[2] == "none"
    assert await svc.path_for(item.id, ".mp4", item=item) == (
        "Gallagher Premiership/Season 2026/"
        "Harlequins v Northampton - PREM - 12th September 2026.mp4")


@pytest.mark.asyncio
async def test_no_fallback_without_dominant_history(ctx, factory):
    item = await _seed_topic(factory, history=2)  # below PRIOR_MIN
    svc = RugbyService(ctx, api=NoApi())
    assert await svc.path_for(item.id, ".mp4", item=item) is None


@pytest.mark.asyncio
async def test_sweep_fetches_new_season_opening_round(ctx, factory):
    """No fixture for the item's season yet: the sweep probes round 1 (and 0)
    of that season, and the fixture it stores then matches."""
    item = await _seed_topic(factory, history=0)
    ev = {"idEvent": "77", "idLeague": "4414", "strSeason": "2026-2027",
          "intRound": "1", "dateEvent": "2026-09-12",
          "strHomeTeam": "Harlequins", "strAwayTeam": "Northampton Saints"}

    class Api(NoApi):
        async def fetch_round(self, league_id, rnd, season):
            return [ev] if (rnd, season) == (1, "2026-2027") else []

    svc = RugbyService(ctx, api=Api())
    best, _conf, status, fetched = await svc.resolve_item(item)
    assert fetched and status == "auto" and best["id"] == 77


@pytest.mark.asyncio
async def test_import_then_dry_run_reconcile_moves_nothing(ctx, factory, tmp_path):
    folder = tmp_path / "Summer Internationals"
    folder.mkdir()
    video = folder / "Lions v New Zealand - 25th August 2026.mp4"
    video.write_bytes(b"x")
    (tmp_path / ".partial").mkdir()
    (tmp_path / ".partial" / "half.mp4").write_bytes(b"x")
    async with factory() as s:
        s.add(rm.RugbyLeague(id=5479, slug="f", name="Rugby Union International Friendlies",
                             tracked=True))
        s.add(rm.RugbyFixture(id=9, league_id=5479, season="2026", round="0",
                              date=datetime(2026, 8, 25, tzinfo=UTC),
                              home_name="Lions", away_name="New Zealand Rugby"))
        await s.commit()
    svc = RugbyService(ctx, api=NoApi())

    dry = await svc.import_library(dry_run=True)
    assert dry["files"] == ["Summer Internationals/Lions v New Zealand - 25th August 2026.mp4"]
    res = await svc.import_library()
    assert (res["imported"], res["matched"]) == (1, 1)
    assert (await svc.import_library())["found"] == 0  # idempotent

    plan = await svc.reconcile(dry_run=True)
    dest = (tmp_path / "Rugby Union International Friendlies" / "Season 2026" /
            "Round 00 - Lions vs New Zealand Rugby.mp4")
    assert plan["plan"][0]["to"] == str(dest)
    assert video.exists() and not dest.exists()  # dry run touched nothing

    async with factory() as s:
        item = (await s.execute(select(MediaItem))).scalar_one()
        assert item.tg_msg_id < 0 and item.raw["import_root"] == str(tmp_path)


@pytest.mark.asyncio
async def test_rescore_never_touches_confirmed(ctx, factory):
    item = await _seed_topic(factory, history=0)
    async with factory() as s:
        s.add(rm.RugbyMatch(media_id=item.id, league_id=4414, fixture_id=1,
                            status="confirmed"))
        await s.commit()
    res = await RugbyService(ctx, api=NoApi()).rematch(rescore=True)
    assert res["scanned"] == 0


def test_prune_keeps_folders_with_videos(tmp_path):
    keep = tmp_path / "A" / "Season 1"
    keep.mkdir(parents=True)
    (keep / "game.mp4").write_bytes(b"x")
    gone = tmp_path / "B" / "Season 25"
    gone.mkdir(parents=True)
    (gone / "season.nfo").write_text("x")
    (tmp_path / "B" / "tvshow.nfo").write_text("x")
    removed = filing.prune([keep, gone], [tmp_path])
    assert keep.exists() and not (tmp_path / "B").exists()
    assert str(gone) in removed and tmp_path.exists()


@pytest.mark.asyncio
async def test_non_rugby_subscription_is_ignored(ctx, factory):
    from app.db.models import Subscription
    item = await _seed_topic(factory, history=0)
    async with factory() as s:
        sub = Subscription(channel_id=item.channel_id, storage_path="/d",
                           rename_template="{title}{ext}")
        s.add(sub)
        await s.flush()
        it = await s.get(MediaItem, item.id)
        it.subscription_id = sub.id
        await s.commit()
        await s.refresh(it)
    api = NoApi()
    api.calls = []
    assert await RugbyService(ctx, api=api).match_item(it) is None
    assert api.calls == []  # no API traffic for non-rugby media
