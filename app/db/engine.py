# app/db/engine.py
import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool
from app.db.models import Base

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:////data/tvm.sqlite"
)

_engine = None
async_session_factory = None


async def init_engine() -> None:
    """Initialize the async SQLAlchemy engine and session factory."""
    global _engine, async_session_factory

    # Create engine
    _engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )

    # Configure SQLite-specific settings
    if "sqlite" in DATABASE_URL.lower():
        from sqlalchemy import event

        @event.listens_for(_engine.sync_engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.close()

    # Create session factory
    async_session_factory = async_sessionmaker(
        _engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )


async def get_engine():
    """Get the global engine (assumes init_engine() was called)."""
    if _engine is None:
        raise RuntimeError("Engine not initialized; call init_engine() first")
    return _engine


async def get_session_factory():
    """Get the async session factory (for building services in lifespan)."""
    if async_session_factory is None:
        raise RuntimeError("Engine not initialized; call init_engine() first")
    return async_session_factory


async def get_session() -> AsyncSession:
    """Dependency for FastAPI to get an async session."""
    if async_session_factory is None:
        raise RuntimeError("Engine not initialized; call init_engine() first")

    async with async_session_factory() as session:
        yield session


async def create_tables() -> None:
    """Create all tables (idempotent)."""
    if _engine is None:
        raise RuntimeError("Engine not initialized; call init_engine() first")

    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables() -> None:
    """Drop all tables (for testing only)."""
    if _engine is None:
        raise RuntimeError("Engine not initialized; call init_engine() first")

    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
