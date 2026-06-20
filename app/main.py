import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.config import Settings
from app.crypto import init_crypto
from app.db.engine import init_engine, create_tables
from app.utils.log import log

settings = Settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    # Startup
    log("Starting Telegram Video-Matic...", "INFO")
    try:
        init_crypto()
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

    log("App startup complete", "SUCCESS")

    yield

    # Shutdown
    log("Shutting down...", "INFO")


def create_app() -> FastAPI:
    """Create and configure FastAPI app."""
    app = FastAPI(
        title="Telegram Video-Matic",
        version="1.0.0",
        lifespan=lifespan,
    )

    # TODO: register routers here

    return app


app = create_app()
