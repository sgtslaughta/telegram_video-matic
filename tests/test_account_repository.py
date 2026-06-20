"""Integration tests for AccountRepository adapter."""
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from app.db.models import Base, Account, AccountStatus
from app.db.repositories import accounts
from app.db.repositories.accounts import AccountRepository
from app.crypto import encrypt, decrypt


@pytest_asyncio.fixture
async def session_factory():
    """Create in-memory test async_sessionmaker."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    yield factory


@pytest.mark.asyncio
async def test_account_repository_get_returns_single_account(session_factory):
    """AccountRepository.get() returns the single Account row."""
    # Insert a single account via module function
    async with session_factory() as s:
        acc = await accounts.upsert(
            session=s,
            api_id="123456",
            api_hash="abc123hash",
            session_string="test_session",
        )
        account_id = acc.id

    # Create repo and call get()
    repo = AccountRepository(session_factory)
    result = await repo.get()

    assert result is not None
    assert result.id == account_id
    assert result.api_id_enc == acc.api_id_enc


@pytest.mark.asyncio
async def test_account_repository_update_status(session_factory):
    """AccountRepository.update_status() persists status change."""
    # Setup: create account
    async with session_factory() as s:
        acc = await accounts.upsert(
            session=s,
            api_id="123456",
            api_hash="abc123hash",
            session_string=None,
        )
        account_id = acc.id

    # Verify initial status
    async with session_factory() as s:
        fetched = await accounts.get(s, account_id)
        assert fetched.status == AccountStatus.DISCONNECTED

    # Use repo to update status
    repo = AccountRepository(session_factory)
    await repo.update_status(account_id, AccountStatus.CONNECTED)

    # Verify persisted
    async with session_factory() as s:
        fetched = await accounts.get(s, account_id)
        assert fetched.status == AccountStatus.CONNECTED


@pytest.mark.asyncio
async def test_account_repository_update_session(session_factory):
    """AccountRepository.update_session() persists encrypted session."""
    # Setup: create account
    async with session_factory() as s:
        acc = await accounts.upsert(
            session=s,
            api_id="123456",
            api_hash="abc123hash",
            session_string=None,
        )
        account_id = acc.id
        assert acc.session_enc is None

    # Use repo to update session
    repo = AccountRepository(session_factory)
    new_session_encrypted = encrypt("new_session_string")
    await repo.update_session(account_id, new_session_encrypted)

    # Verify persisted
    async with session_factory() as s:
        fetched = await accounts.get(s, account_id)
        assert fetched.session_enc == new_session_encrypted
        # Decrypt to verify round-trip
        decrypted = decrypt(fetched.session_enc)
        assert decrypted == "new_session_string"


@pytest.mark.asyncio
async def test_account_repository_update_phone(session_factory):
    """AccountRepository.update_phone() persists phone number."""
    # Setup: create account
    async with session_factory() as s:
        acc = await accounts.upsert(
            session=s,
            api_id="123456",
            api_hash="abc123hash",
            session_string=None,
        )
        account_id = acc.id
        assert acc.phone is None

    # Use repo to update phone
    repo = AccountRepository(session_factory)
    await repo.update_phone(account_id, "+15551234567")

    # Verify persisted
    async with session_factory() as s:
        fetched = await accounts.get(s, account_id)
        assert fetched.phone == "+15551234567"
