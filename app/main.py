import pathlib
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.config import Settings
from app.crypto import init_crypto
from app.db.engine import init_engine, create_tables, get_session_factory, get_engine
from app.utils.log import log
from app.api import routers
from app.api.ws import WSHub, websocket_endpoint
from app.telegram.service import TelegramService
from app.sync.engine import SyncEngine
from app.sync.plugins import PluginHost

settings = Settings()

# ponytail: static dir path, may not exist; skip mount if not found
STATIC_DIR = pathlib.Path(__file__).parent.parent / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    # Startup
    log("Starting Telegram Video-Matic...", "INFO")
    try:
        init_crypto(settings.tvm_secret_key)
        log("Crypto initialized", "SUCCESS")
    except ValueError as e:
        log(f"Crypto init failed: {e}", "ERROR")
        raise

    try:
        await init_engine()
        log("Database engine initialized", "SUCCESS")
    except Exception as e:
        log(f"Engine init failed: {e}", "ERROR")
        raise

    try:
        await create_tables()
        log("Database schema ready", "SUCCESS")
    except Exception as e:
        log(f"Schema creation failed: {e}", "ERROR")
        raise

    # Get session factory for building services
    try:
        session_factory = await get_session_factory()
    except RuntimeError as e:
        log(f"Session factory init failed: {e}", "ERROR")
        raise
    # Expose early so plugin contexts (lazy session) and get_db can resolve it.
    app.state.session_factory = session_factory
    app.state.async_session = session_factory

    # Seed default settings rows so the Settings page has editable values.
    try:
        from app.db.repositories import settings as settings_repo
        async with session_factory() as session:
            await settings_repo.ensure_defaults(session, {
                "poll_interval_sec": settings.poll_interval_sec,
                "max_concurrent_downloads": settings.max_concurrent_downloads,
                "retention_days": settings.retention_days,
                "retention_disk_pct": settings.retention_disk_pct,
            })
    except Exception as e:
        log(f"Settings seed failed: {e}", "WARN")

    # Build WebSocket hub
    hub = WSHub()
    app.state.ws_hub = hub

    # Build event sink for logging to DB
    async def event_sink(level: str, kind: str, message: str):
        from app.db.repositories import events as events_repo
        try:
            async with session_factory() as session:
                await events_repo.add(session, level=level, kind=kind, message=message)
                await session.commit()
        except Exception as e:
            log(f"Failed to log event: {e}", "ERROR")

    # Build TelegramService with AccountRepository adapter
    from app.db.repositories.accounts import AccountRepository
    account_repo = AccountRepository(session_factory)
    try:
        tg_service = TelegramService(
            account_repo=account_repo,
            event_sink=event_sink,
            max_concurrent_downloads=settings.max_concurrent_downloads
        )
        # Load account from DB (guard: if no account/secret, leave disconnected)
        account = await account_repo.get()
        if account:
            await tg_service.load_account()
            # Restore the live connection for a saved session (shutdown marks
            # the account disconnected; reconnect so it shows connected again).
            if account.session_enc:
                try:
                    await tg_service.connect()
                except Exception as e:
                    log(f"Telegram reconnect on startup failed: {e}", "WARN")
        app.state.tg_service = tg_service
        log("Telegram service ready", "SUCCESS")
    except Exception as e:
        log(f"Telegram service init failed: {e}", "ERROR")
        app.state.tg_service = None

    # Wire the plugin host (built in create_app): apply stored enabled/config,
    # create plugin-owned tables, and run on_enable for enabled plugins.
    try:
        plugin_host = app.state.plugin_host
        await plugin_host.sync_db(session_factory)
        await plugin_host.create_models(await get_engine())
        await create_tables()  # additive reconcile for any new plugin columns
        for entry in plugin_host.entries:
            if entry.enabled:
                try:
                    await entry.instance.on_enable()
                except Exception as ex:  # noqa: BLE001
                    log(f"Plugin {entry.name} on_enable failed: {ex}", "WARN")
        log("Plugin host ready", "SUCCESS")
    except Exception as e:
        log(f"Plugin host wiring failed: {e}", "ERROR")

    # Build SyncEngine
    try:
        engine = SyncEngine(
            session_factory=session_factory,
            tg_service=app.state.tg_service,
            plugin_host=app.state.plugin_host,
            broadcast=hub.broadcast,
            poll_interval_sec=settings.poll_interval_sec,
            maintenance_interval_sec=3600,
            download_root=settings.media_root,
        )
        await engine.start()
        app.state.engine = engine
        log("Sync engine started", "SUCCESS")
    except Exception as e:
        log(f"Sync engine init failed: {e}", "ERROR")
        app.state.engine = None

    # Store session factory on app.state for get_db dependency
    app.state.async_session = session_factory

    log("App startup complete", "SUCCESS")

    yield

    # Shutdown
    log("Shutting down...", "INFO")
    try:
        if hasattr(app.state, "engine") and app.state.engine:
            await app.state.engine.stop()
            log("Sync engine stopped", "SUCCESS")
    except Exception as e:
        log(f"Engine stop error: {e}", "ERROR")

    try:
        if hasattr(app.state, "tg_service") and app.state.tg_service:
            await app.state.tg_service.disconnect()
            log("Telegram service disconnected", "SUCCESS")
    except Exception as e:
        log(f"TG service disconnect error: {e}", "ERROR")

    log("Shutdown complete", "SUCCESS")


def create_app() -> FastAPI:
    """Create and configure FastAPI app."""
    app = FastAPI(
        title="Telegram Video-Matic",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Register all routers (each has /api prefix already)
    app.include_router(routers.health.router)
    app.include_router(routers.auth.router)
    app.include_router(routers.telegram.router)
    app.include_router(routers.channels.router)
    app.include_router(routers.subscriptions.router)
    app.include_router(routers.media.router)
    app.include_router(routers.downloads.router)
    app.include_router(routers.events.router)
    app.include_router(routers.settings.router)
    app.include_router(routers.plugins.router)

    # Build the plugin host HERE (not in lifespan) so plugin-contributed routers
    # can be mounted at startup — FastAPI can't add routes after startup. The
    # context's session factory is resolved lazily (set during lifespan).
    from app.sync.plugins import PluginContext

    def _ctx_factory(name, config):
        return PluginContext(
            name=name, config=config, settings=settings,
            media_root=settings.media_root,
            session_factory=lambda: app.state.async_session(),
        )

    plugin_host = PluginHost(ctx_factory=_ctx_factory)
    try:
        plugin_host.discover()
    except Exception as e:  # noqa: BLE001
        log(f"Plugin discovery failed: {e}", "ERROR")
    app.state.plugin_host = plugin_host
    for plugin_router in plugin_host.all_routers():
        app.include_router(plugin_router)

    # Mount WebSocket endpoint at /api/ws with snapshot provider
    from fastapi import WebSocket as WSType
    @app.websocket("/api/ws")
    async def ws_endpoint_wrapper(websocket: WSType):
        from app.api.schemas import WSSnapshot, DownloadJobRead
        from app.db.repositories import downloads as downloads_repo

        async def snapshot_provider():
            """Build snapshot from active downloads + TG status."""
            try:
                # Get active downloads
                async with app.state.async_session() as session:
                    active = await downloads_repo.list_active(session)
                    active_downloads = [DownloadJobRead.from_orm(j) for j in active]

                # Get TG status
                tg_status = None
                if hasattr(app.state, "tg_service") and app.state.tg_service and app.state.tg_service.account:
                    from app.api.schemas import TelegramStatusRead
                    tg_status = TelegramStatusRead.from_orm(app.state.tg_service.account)

                return WSSnapshot(active_downloads=active_downloads, tg_status=tg_status)
            except Exception as e:
                log(f"Snapshot build error: {e}", "ERROR")
                return WSSnapshot(active_downloads=[])

        await websocket_endpoint(websocket, app.state.ws_hub, snapshot_provider)

    # Serve the built SPA: hashed assets via StaticFiles, everything else falls
    # back to index.html so client-side routes (e.g. /subscriptions) work on
    # deep-link / refresh. Unmatched /api paths still 404 as JSON.
    if STATIC_DIR.exists():
        assets_dir = STATIC_DIR / "assets"
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")
        index_file = STATIC_DIR / "index.html"

        static_root = STATIC_DIR.resolve()

        @app.get("/{full_path:path}")
        async def spa_fallback(full_path: str):
            if full_path.startswith("api"):
                raise HTTPException(status_code=404, detail="Not found")
            # Serve a real file only if it resolves to within STATIC_DIR
            # (guards against path traversal via ../ in the request path).
            try:
                candidate = (STATIC_DIR / full_path).resolve()
            except (OSError, RuntimeError):
                return FileResponse(str(index_file))
            if full_path and candidate.is_file() and static_root in candidate.parents:
                return FileResponse(str(candidate))
            return FileResponse(str(index_file))
    else:
        log(f"Static dir not found at {STATIC_DIR}, skipping SPA mount", "WARN")

    return app


app = create_app()
