from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import Account
from app.crypto import encrypt, decrypt


async def get(session: AsyncSession, account_id: int) -> Account | None:
    """Get account by ID."""
    result = await session.execute(select(Account).where(Account.id == account_id))
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
