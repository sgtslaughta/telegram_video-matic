"""Rugby wanted: fixtures played but not downloaded, with auto-search."""

import pytest
import pytest_asyncio
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.models import Base, Channel, Subscription, MediaItem, MediaStatus
from app.sync.plugins import PluginContext
import app.rugby.models as rm
from app.rugby.models import RugbyWantedState
from app.rugby.wanted import WantedService


@pytest_asyncio.fixture
async def factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture
def ctx(factory):
    return PluginContext(name="rugby", config={}, session_factory=factory)


class TestWantedStateModel:
    @pytest.mark.asyncio
    async def test_wanted_state_fixture_id_primary_key(self, factory):
        """RugbyWantedState.fixture_id is PK, tracks search attempts and gave_up state."""
        async with factory() as s:
            # Create a fixture first
            fx = rm.RugbyFixture(
                id=100, league_id=1, season="2025",
                date=datetime.now(timezone.utc)
            )
            s.add(fx)
            await s.flush()

            # Create wanted state
            ws = RugbyWantedState(fixture_id=100, attempts=3)
            s.add(ws)
            await s.commit()

            # Retrieve it
            row = await s.get(RugbyWantedState, 100)
            assert row.fixture_id == 100
            assert row.attempts == 3
            assert row.gave_up is False
            assert row.dismissed is False
            assert row.last_searched_at is None


class TestWantedListQuery:
    @pytest.mark.asyncio
    async def test_list_wanted_excludes_unplayed_fixtures(self, ctx, factory):
        """Fixtures with date > now-3h should not appear in wanted list."""
        now = datetime.now(timezone.utc)

        async with factory() as s:
            # Create channel, subscription + league
            ch = Channel(id=1, tg_id=100, title="Test Channel")
            lg = rm.RugbyLeague(id=1, slug="test", name="Test League")
            sub = Subscription(id=1, channel_id=1, enabled=True, storage_path="/tmp", rename_template="{original}")
            rs = rm.RugbySubscription(subscription_id=1, league_id=1)
            s.add_all([ch, lg, sub, rs])

            # Fixture played 4h ago (should include)
            fx_old = rm.RugbyFixture(
                id=10, league_id=1, season="2025",
                date=now - timedelta(hours=4),
                home_name="A", away_name="B"
            )
            # Fixture played 2h ago (should exclude)
            fx_new = rm.RugbyFixture(
                id=11, league_id=1, season="2025",
                date=now - timedelta(hours=2),
                home_name="C", away_name="D"
            )
            s.add_all([fx_old, fx_new])
            await s.commit()

        svc = WantedService(ctx)
        result = await svc.list_wanted()
        fixture_ids = [item["fixture_id"] for item in result]
        assert 10 in fixture_ids
        assert 11 not in fixture_ids

    @pytest.mark.asyncio
    async def test_list_wanted_excludes_matched_fixtures(self, ctx, factory):
        """Fixtures with auto/confirmed RugbyMatch and downloaded MediaItem exclude."""
        now = datetime.now(timezone.utc)

        async with factory() as s:
            ch = Channel(id=1, tg_id=100, title="Test Channel")
            lg = rm.RugbyLeague(id=1, slug="test", name="Test League")
            sub = Subscription(id=1, channel_id=1, enabled=True, storage_path="/tmp", rename_template="{original}")
            rs = rm.RugbySubscription(subscription_id=1, league_id=1)
            s.add_all([ch, lg, sub, rs])

            # Fixture with auto match and queued item (should exclude)
            fx_matched = rm.RugbyFixture(
                id=20, league_id=1, season="2025",
                date=now - timedelta(hours=4),
                home_name="E", away_name="F"
            )
            item = MediaItem(
                tg_msg_id=100, channel_id=1, status=MediaStatus.QUEUED,
                date_posted=now
            )
            s.add_all([fx_matched, item])
            await s.flush()

            match = rm.RugbyMatch(
                media_id=item.id, fixture_id=20, status="auto",
                confidence=0.9
            )
            s.add(match)

            # Unmatched fixture (should include)
            fx_unmatched = rm.RugbyFixture(
                id=21, league_id=1, season="2025",
                date=now - timedelta(hours=4),
                home_name="G", away_name="H"
            )
            s.add(fx_unmatched)
            await s.commit()

        svc = WantedService(ctx)
        result = await svc.list_wanted()
        fixture_ids = [item["fixture_id"] for item in result]
        assert 20 not in fixture_ids
        assert 21 in fixture_ids

    @pytest.mark.asyncio
    async def test_list_wanted_excludes_dismissed(self, ctx, factory):
        """Fixtures with dismissed=True in RugbyWantedState exclude."""
        now = datetime.now(timezone.utc)

        async with factory() as s:
            ch = Channel(id=1, tg_id=100, title="Test Channel")
            lg = rm.RugbyLeague(id=1, slug="test", name="Test League")
            sub = Subscription(id=1, channel_id=1, enabled=True, storage_path="/tmp", rename_template="{original}")
            rs = rm.RugbySubscription(subscription_id=1, league_id=1)
            s.add_all([ch, lg, sub, rs])

            fx_dismissed = rm.RugbyFixture(
                id=30, league_id=1, season="2025",
                date=now - timedelta(hours=4),
                home_name="I", away_name="J"
            )
            ws = RugbyWantedState(fixture_id=30, dismissed=True)
            s.add_all([fx_dismissed, ws])

            fx_not_dismissed = rm.RugbyFixture(
                id=31, league_id=1, season="2025",
                date=now - timedelta(hours=4),
                home_name="K", away_name="L"
            )
            s.add(fx_not_dismissed)
            await s.commit()

        svc = WantedService(ctx)
        result = await svc.list_wanted()
        fixture_ids = [item["fixture_id"] for item in result]
        assert 30 not in fixture_ids
        assert 31 in fixture_ids

    @pytest.mark.asyncio
    async def test_list_wanted_respects_subscription_window(self, ctx, factory):
        """Fixtures before subscription.date_from exclude."""
        now = datetime.now(timezone.utc)
        sub_date = now - timedelta(days=30)

        async with factory() as s:
            ch = Channel(id=1, tg_id=100, title="Test Channel")
            lg = rm.RugbyLeague(id=1, slug="test", name="Test League")
            sub = Subscription(
                id=1, channel_id=1, enabled=True, date_from=sub_date,
                storage_path="/tmp", rename_template="{original}"
            )
            rs = rm.RugbySubscription(subscription_id=1, league_id=1)
            s.add_all([ch, lg, sub, rs])

            # Within window (should include)
            fx_in = rm.RugbyFixture(
                id=40, league_id=1, season="2025",
                date=now - timedelta(days=15),
                home_name="M", away_name="N"
            )
            # Before window (should exclude)
            fx_out = rm.RugbyFixture(
                id=41, league_id=1, season="2025",
                date=now - timedelta(days=70),
                home_name="O", away_name="P"
            )
            s.add_all([fx_in, fx_out])
            await s.commit()

        svc = WantedService(ctx)
        result = await svc.list_wanted()
        fixture_ids = [item["fixture_id"] for item in result]
        assert 40 in fixture_ids
        assert 41 not in fixture_ids


class TestWantedDismiss:
    @pytest.mark.asyncio
    async def test_dismiss_fixture_marks_dismissed(self, ctx, factory):
        """dismiss_fixture sets dismissed=True in RugbyWantedState."""
        now = datetime.now(timezone.utc)

        async with factory() as s:
            ch = Channel(id=1, tg_id=100, title="Test Channel")
            lg = rm.RugbyLeague(id=1, slug="test", name="League")
            sub = Subscription(id=1, channel_id=1, enabled=True, storage_path="/tmp", rename_template="{original}")
            rs = rm.RugbySubscription(subscription_id=1, league_id=1)
            fx = rm.RugbyFixture(
                id=70, league_id=1, season="2025",
                date=now - timedelta(hours=4),
                home_name="A", away_name="B"
            )
            s.add_all([ch, lg, sub, rs, fx])
            await s.commit()

        svc = WantedService(ctx)
        await svc.dismiss_fixture(70)

        async with factory() as s:
            ws = await s.get(RugbyWantedState, 70)
            assert ws is not None
            assert ws.dismissed is True


class TestAutoSearch:
    @pytest.mark.asyncio
    async def test_auto_search_after_7_days_sets_gave_up(self, ctx, factory):
        """Fixtures missing > 7 days transition state=not_found with gave_up=True."""
        now = datetime.now(timezone.utc)

        async with factory() as s:
            ch = Channel(id=1, tg_id=100, title="Test Channel")
            lg = rm.RugbyLeague(id=1, slug="test", name="League")
            sub = Subscription(id=1, channel_id=1, enabled=True, storage_path="/tmp", rename_template="{original}")
            rs = rm.RugbySubscription(subscription_id=1, league_id=1)

            # Fixture missing for 8 days
            fx_old = rm.RugbyFixture(
                id=80, league_id=1, season="2025",
                date=now - timedelta(days=8),
                home_name="X", away_name="Y"
            )
            s.add_all([ch, lg, sub, rs, fx_old])
            await s.commit()

        svc = WantedService(ctx)
        await svc.run_auto_search(now)

        async with factory() as s:
            ws = await s.get(RugbyWantedState, 80)
            assert ws is not None
            assert ws.gave_up is True

        # Verify state is "not_found" in list_wanted
        wanted = await svc.list_wanted()
        item = next((w for w in wanted if w["fixture_id"] == 80), None)
        assert item is not None
        assert item["state"] == "not_found"

    @pytest.mark.asyncio
    async def test_auto_search_under_7_days_not_gave_up(self, ctx, factory):
        """Fixtures missing < 7 days should not set gave_up."""
        now = datetime.now(timezone.utc)

        async with factory() as s:
            ch = Channel(id=1, tg_id=100, title="Test Channel")
            lg = rm.RugbyLeague(id=1, slug="test", name="League")
            sub = Subscription(id=1, channel_id=1, enabled=True, storage_path="/tmp", rename_template="{original}")
            rs = rm.RugbySubscription(subscription_id=1, league_id=1)

            # Fixture missing for 6 days
            fx = rm.RugbyFixture(
                id=81, league_id=1, season="2025",
                date=now - timedelta(days=6),
                home_name="A", away_name="B"
            )
            s.add_all([ch, lg, sub, rs, fx])
            await s.commit()

        svc = WantedService(ctx)
        await svc.run_auto_search(now)

        async with factory() as s:
            ws = await s.get(RugbyWantedState, 81)
            # Either no state exists yet or gave_up is still False
            if ws:
                assert ws.gave_up is False


class _FakeTg:
    """Minimal TelegramService stand-in for search/grab."""

    def __init__(self, dtos):
        self.client = object()
        self.dtos = dtos
        self.searches = []

    async def iter_media(self, chan, topic, since_msg_id=None, *, search=None, limit=None, since_date=None):
        self.searches.append(search)
        for d in self.dtos:
            if search and search.lower() in (d.caption or "").lower():
                yield d

    async def get_message(self, chan, msg_id):
        return next((d for d in self.dtos if d.tg_msg_id == msg_id), None)


def _dto(msg_id, caption, when):
    from app.telegram.dtos import MediaDTO
    return MediaDTO(tg_msg_id=msg_id, channel_tg_id=100, topic_tg_id=None, caption=caption,
                    file_name=f"{msg_id}.mkv", mime="video/mp4", size_bytes=10, duration_sec=60,
                    date_posted=when, thumb_b64=None, reactions={}, comments_count=0, raw={})


async def _seed(factory, when):
    async with factory() as s:
        s.add_all([Channel(id=1, tg_id=100, title="C"), rm.RugbyLeague(id=1, slug="p", name="Prem"),
                   Subscription(id=1, channel_id=1, enabled=True, storage_path="/tmp", rename_template="{original}"),
                   rm.RugbySubscription(subscription_id=1, league_id=1),
                   rm.RugbyFixture(id=90, league_id=1, season="2025", round="4", date=when,
                                   home_name="Bath Rugby", away_name="Gloucester Rugby")])
        await s.commit()


class TestSearchGrab:
    @pytest.mark.asyncio
    async def test_search_scores_and_grab_queues_with_confirmed_match(self, factory):
        when = datetime(2026, 10, 25, 15, tzinfo=timezone.utc)
        await _seed(factory, when)
        tg = _FakeTg([_dto(7, "Bath vs Gloucester Round 4 full match", when + timedelta(hours=3)),
                      _dto(8, "Gloucester highlights 2019", when - timedelta(days=2000))])
        ctx = PluginContext(name="rugby", config={}, session_factory=factory, tg_getter=lambda: tg)
        svc = WantedService(ctx)
        cands = await svc.search_fixture(90)
        assert cands[0]["tg_msg_id"] == 7 and cands[0]["confidence"] > cands[-1]["confidence"]
        assert cands[0]["already_tracked"] is False
        res = await svc.grab_fixture(90, 1, 7)
        async with factory() as s:
            item = await s.get(MediaItem, res["media_id"])
            m = (await s.execute(select(rm.RugbyMatch).where(rm.RugbyMatch.media_id == item.id))).scalar_one()
        assert item.status == MediaStatus.PENDING and item.subscription_id == 1
        assert m.status == "confirmed" and m.fixture_id == 90
        assert item.content_date is not None

    @pytest.mark.asyncio
    async def test_grab_requeues_skipped_item(self, factory):
        when = datetime(2026, 10, 25, 15, tzinfo=timezone.utc)
        await _seed(factory, when)
        async with factory() as s:
            s.add(MediaItem(id=5, channel_id=1, tg_msg_id=7, date_posted=when, status=MediaStatus.SKIPPED,
                            skip_reason="regex"))
            await s.commit()
        ctx = PluginContext(name="rugby", config={}, session_factory=factory, tg_getter=lambda: _FakeTg([]))
        await WantedService(ctx).grab_fixture(90, 1, 7)
        async with factory() as s:
            item = await s.get(MediaItem, 5)
        assert item.status == MediaStatus.PENDING and item.skip_reason is None

    @pytest.mark.asyncio
    async def test_search_without_telegram_raises(self, factory):
        await _seed(factory, datetime(2026, 10, 25, tzinfo=timezone.utc))
        ctx = PluginContext(name="rugby", config={}, session_factory=factory)
        with pytest.raises(RuntimeError):
            await WantedService(ctx).search_fixture(90)
