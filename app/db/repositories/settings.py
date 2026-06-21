from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import Setting


async def get(
    session: AsyncSession,
    key: str,
    default: str | None = None,
) -> str | None:
    """Get setting value by key."""
    result = await session.execute(
        select(Setting).where(Setting.key == key)
    )
    setting = result.scalar_one_or_none()
    return setting.value if setting else default


async def set(
    session: AsyncSession,
    key: str,
    value: str,
) -> Setting:
    """Set or update a setting."""
    result = await session.execute(
        select(Setting).where(Setting.key == key)
    )
    setting = result.scalar_one_or_none()

    if not setting:
        setting = Setting(key=key, value=value)
        session.add(setting)
    else:
        setting.value = value

    await session.commit()
    return setting


async def list(session: AsyncSession) -> list[Setting]:
    """List all settings."""
    result = await session.execute(select(Setting))
    return result.scalars().all()


async def ensure_defaults(session: AsyncSession, defaults: dict) -> None:
    """Insert any missing settings with default values (won't overwrite existing)."""
    existing = {s.key for s in await list(session)}
    added = False
    for key, value in defaults.items():
        if key not in existing:
            session.add(Setting(key=key, value=str(value)))
            added = True
    if added:
        await session.commit()
