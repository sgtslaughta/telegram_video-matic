"""Plugin platform: base class, context (DI), and host wiring."""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.models import Base, EventLevel
from app.db.repositories import events, plugins as plugins_repo
from app.sync.plugins import TVMPlugin, PluginBase, PluginContext, PluginHost


@pytest_asyncio.fixture
async def session_factory():
    """In-memory DB session factory."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:", echo=False, poolclass=StaticPool
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# --------------------------------------------------------------------------- #
# PluginBase
# --------------------------------------------------------------------------- #
class TestPluginBase:
    @pytest.mark.asyncio
    async def test_default_hooks_are_noops(self):
        """Base class supplies safe no-op hooks + empty declarations."""
        p = PluginBase(ctx=None)
        await p.on_media_discovered(None)
        await p.on_pre_download(None)
        await p.on_post_download(None, "")
        await p.on_prune(None)
        await p.on_enable()
        await p.on_disable()
        assert await p.provide_naming_tokens(None, None) == {}
        assert p.models() == []
        assert p.routers() == []
        assert p.background_tasks() == []

    def test_manifest_defaults(self):
        assert PluginBase.version
        assert PluginBase.default_config == {}


# --------------------------------------------------------------------------- #
# PluginContext (dependency injection)
# --------------------------------------------------------------------------- #
class TestPluginContext:
    @pytest.mark.asyncio
    async def test_log_writes_event(self, session_factory):
        ctx = PluginContext(name="rugby", config={}, session_factory=session_factory)
        await ctx.log(EventLevel.INFO, "rugby", "hello")
        async with session_factory() as s:
            rows = await events.list_by_kind(s, "rugby")
        assert any(e.message == "hello" for e in rows)

    @pytest.mark.asyncio
    async def test_error_log_sets_last_error(self, session_factory):
        ctx = PluginContext(name="rugby", config={}, session_factory=session_factory)
        assert ctx.health["last_error"] is None
        await ctx.log(EventLevel.ERROR, "rugby", "boom")
        assert ctx.health["last_error"] == "boom"

    @pytest.mark.asyncio
    async def test_session_yields_usable_session(self, session_factory):
        ctx = PluginContext(name="x", config={}, session_factory=session_factory)
        async with ctx.session() as s:
            await events.add(s, level=EventLevel.INFO, kind="x", message="ok")
        async with session_factory() as s:
            assert await events.list_by_kind(s, "x")

    def test_set_status(self):
        ctx = PluginContext(name="x", config={})
        ctx.set_status({"leagues": 3})
        assert ctx.health["status"] == {"leagues": 3}


# --------------------------------------------------------------------------- #
# PluginHost
# --------------------------------------------------------------------------- #
class _Recorder(PluginBase):
    name = "recorder"

    def __init__(self, ctx=None):
        super().__init__(ctx)
        self.calls = []

    async def on_media_discovered(self, item):
        self.calls.append(item)

    async def provide_naming_tokens(self, item, sub):
        return {"team": "Sale"}


class _Boom(PluginBase):
    name = "boom"

    async def on_media_discovered(self, item):
        raise RuntimeError("kaboom")

    async def provide_naming_tokens(self, item, sub):
        raise RuntimeError("kaboom")


class _Lifecycle(PluginBase):
    name = "lifecycle"

    def __init__(self, ctx=None):
        super().__init__(ctx)
        self.enabled_called = False

    async def on_enable(self):
        self.enabled_called = True


class TestPluginHostDispatch:
    @pytest.mark.asyncio
    async def test_empty_dispatch_is_noop(self):
        await PluginHost().dispatch("on_media_discovered", None)

    @pytest.mark.asyncio
    async def test_dispatch_calls_enabled_only(self):
        host = PluginHost()
        a, b = _Recorder(), _Recorder()
        host.register(a, enabled=True)
        host.register(b, enabled=False)
        await host.dispatch("on_media_discovered", "x")
        assert a.calls == ["x"] and b.calls == []

    @pytest.mark.asyncio
    async def test_dispatch_guards_exceptions(self):
        host = PluginHost()
        boom, rec = _Boom(), _Recorder()
        host.register(boom)
        host.register(rec)
        # must not raise; the healthy plugin still runs
        await host.dispatch("on_media_discovered", "x")
        assert rec.calls == ["x"]

    @pytest.mark.asyncio
    async def test_collect_naming_tokens_merges_enabled(self):
        host = PluginHost()
        host.register(_Recorder(), enabled=True)
        host.register(_Boom())  # raises -> ignored, not fatal
        tokens = await host.collect_naming_tokens("item", "sub")
        assert tokens == {"team": "Sale"}

    @pytest.mark.asyncio
    async def test_collect_naming_tokens_skips_disabled(self):
        host = PluginHost()
        host.register(_Recorder(), enabled=False)
        assert await host.collect_naming_tokens("i", "s") == {}


class TestPluginHostDiscovery:
    def test_discover_loads_plugins(self):
        """Discovery finds PluginBase subclasses without touching the DB."""
        host = PluginHost()
        host.discover()
        names = [e.name for e in host.entries]
        assert "rugby" in names

    @pytest.mark.asyncio
    async def test_sync_db_honors_stored_enabled_flag(self, session_factory):
        """A plugin disabled in the DB is not dispatched after sync_db."""
        async with session_factory() as s:
            p = await plugins_repo.upsert(s, name="recorder", version="1", config={})
            await plugins_repo.set_enabled(s, p.id, False)
        host = PluginHost()
        rec = _Recorder()
        host.register(rec, enabled=True)
        await host.sync_db(session_factory)
        await host.dispatch("on_media_discovered", "x")
        assert rec.calls == []


class TestPluginHostLifecycleAndManagement:
    @pytest.mark.asyncio
    async def test_set_enabled_flips_flag_calls_hook_and_persists(self, session_factory):
        async with session_factory() as s:
            await plugins_repo.upsert(s, name="lifecycle", version="1", config={})
        host = PluginHost()
        p = _Lifecycle()
        host.register(p, enabled=False)
        await host.set_enabled(session_factory, "lifecycle", True)
        assert host._entry("lifecycle").enabled is True
        assert p.enabled_called is True
        async with session_factory() as s:
            row = await plugins_repo.get_by_name(s, "lifecycle")
        assert row.enabled is True

    def test_all_routers_collects_from_plugins(self):
        from fastapi import APIRouter
        r = APIRouter()

        class _WithRouter(PluginBase):
            name = "withrouter"

            def routers(self):
                return [r]

        host = PluginHost()
        host.register(_WithRouter())
        assert host.all_routers() == [r]

    def test_health_reports_enabled_and_status(self):
        host = PluginHost()
        p = _Recorder(ctx=PluginContext(name="recorder", config={}))
        p.ctx.set_status({"leagues": 6})
        host.register(p, enabled=True)
        h = host.health("recorder")
        assert h["enabled"] is True and h["status"] == {"leagues": 6}
        assert host.health("missing") is None

    @pytest.mark.asyncio
    async def test_create_models_creates_declared_tables(self, session_factory):
        """create_models runs create_all for each plugin's declared tables."""
        from sqlalchemy import Column, Integer, String
        from app.db.models import Base

        class _Widget(Base):
            __tablename__ = "test_plugin_widget"
            __table_args__ = {"extend_existing": True}
            id = Column(Integer, primary_key=True)
            label = Column(String(32))

        class _ModelPlugin(PluginBase):
            name = "modelplugin"

            def models(self):
                return [_Widget]

        # Fresh engine WITHOUT this table created up front.
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
        from sqlalchemy.pool import StaticPool
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
        factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        host = PluginHost()
        host.register(_ModelPlugin())
        await host.create_models(engine)

        # Table now exists: insert + read back works.
        async with factory() as s:
            await s.execute(_Widget.__table__.insert().values(label="ok"))
            await s.commit()
            rows = (await s.execute(_Widget.__table__.select())).all()
        assert rows and rows[0].label == "ok"
