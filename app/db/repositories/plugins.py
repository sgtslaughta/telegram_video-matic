from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import Plugin


async def upsert(
    session: AsyncSession,
    name: str,
    version: str,
    config: dict | None = None,
) -> Plugin:
    """Insert or update plugin."""
    result = await session.execute(
        select(Plugin).where(Plugin.name == name)
    )
    plugin = result.scalar_one_or_none()

    if not plugin:
        plugin = Plugin(name=name, version=version, config=config)
        session.add(plugin)
    else:
        plugin.version = version
        plugin.config = config

    await session.commit()
    return plugin


async def set_enabled(
    session: AsyncSession,
    plugin_id: int,
    enabled: bool,
) -> Plugin | None:
    """Enable or disable plugin."""
    plugin = await session.get(Plugin, plugin_id)
    if plugin:
        plugin.enabled = enabled
        await session.commit()
    return plugin
