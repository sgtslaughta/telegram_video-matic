from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import Account, AccountStatus
from app.crypto import encrypt, decrypt


async def get(session: AsyncSession, account_id: int) -> Account | None:
    """Get account by ID."""
    result = await session.execute(select(Account).where(Account.id == account_id))
    return result.scalar_one_or_none()


async def get_single(session: AsyncSession) -> Account | None:
    """Get the single/first Account row (app is single-account)."""
    result = await session.execute(select(Account).limit(1))
    return result.scalar_one_or_none()


async def upsert(
    session: AsyncSession,
    api_id: str,
    api_hash: str,
    session_string: str | None = None,
) -> Account:
    """Insert or update the single account row with encrypted secrets."""
    # Always update the first (and only) account
    account = await get(session, 1)

    if not account:
        account = Account(
            id=1,
            api_id_enc=encrypt(api_id),
            api_hash_enc=encrypt(api_hash),
            session_enc=encrypt(session_string) if session_string else None,
        )
        session.add(account)
    else:
        account.api_id_enc = encrypt(api_id)
        account.api_hash_enc = encrypt(api_hash)
        if session_string:
            account.session_enc = encrypt(session_string)

    await session.commit()
    return account


async def update_status(session: AsyncSession, account_id: int, status: str) -> None:
    """Update Account status and commit."""
    account = await get(session, account_id)
    if account:
        account.status = status
        await session.commit()


async def update_session(session: AsyncSession, account_id: int, session_enc: str) -> None:
    """Update Account session_enc and commit."""
    account = await get(session, account_id)
    if account:
        account.session_enc = session_enc
        await session.commit()


async def update_phone(session: AsyncSession, account_id: int, phone: str) -> None:
    """Update Account phone and commit."""
    account = await get(session, account_id)
    if account:
        account.phone = phone
        await session.commit()


class AccountRepository:
    """Adapter: wraps async session_factory and delegates to module functions."""

    def __init__(self, session_factory):
        """
        Initialize with async session factory.

        Args:
            session_factory: async_sessionmaker instance.
        """
        self._sf = session_factory

    async def get(self) -> Account | None:
        """Get the single Account row."""
        async with self._sf() as session:
            return await get_single(session)

    async def update_status(self, account_id: int, status: str) -> None:
        """Update Account status."""
        async with self._sf() as session:
            await update_status(session, account_id, status)

    async def update_session(self, account_id: int, session_enc: str) -> None:
        """Update Account session_enc."""
        async with self._sf() as session:
            await update_session(session, account_id, session_enc)

    async def update_phone(self, account_id: int, phone: str) -> None:
        """Update Account phone."""
        async with self._sf() as session:
            await update_phone(session, account_id, phone)
