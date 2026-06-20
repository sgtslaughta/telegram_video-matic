# tests/test_engine.py
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import StaticPool
from app.db.engine import init_engine, get_session
from app.db.models import Base, Account


@pytest_asyncio.fixture
async def engine():
    """Create in-memory test engine."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.mark.asyncio
async def test_engine_creates_tables(engine):
    """Engine can create all tables."""
    async with engine.begin() as conn:
        # Check that tables were created
        from sqlalchemy import text
        result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        tables = [row[0] for row in result]

    assert "accounts" in tables
    assert "channels" in tables
    assert "subscriptions" in tables


@pytest.mark.asyncio
async def test_get_session_dependency(engine):
    """async_sessionmaker can create sessions and execute queries."""
    from sqlalchemy.ext.asyncio import async_sessionmaker

    # Create a session factory from the test engine
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with factory() as session:
        assert isinstance(session, AsyncSession)
        # Can execute a query
        from sqlalchemy import select
        result = await session.execute(select(Account))
        accounts = result.scalars().all()
        assert accounts == []
