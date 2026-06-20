from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import Tag, MediaTag


async def add_tag(session: AsyncSession, name: str) -> Tag:
    """Add a tag (or return existing)."""
    result = await session.execute(
        select(Tag).where(Tag.name == name)
    )
    tag = result.scalar_one_or_none()

    if not tag:
        tag = Tag(name=name)
        session.add(tag)
        await session.commit()

    return tag


async def tag_media(
    session: AsyncSession,
    media_id: int,
    tag_id: int,
) -> None:
    """Associate a tag with a media item."""
    result = await session.execute(
        select(MediaTag).where(
            (MediaTag.media_id == media_id) & (MediaTag.tag_id == tag_id)
        )
    )
    if not result.scalar_one_or_none():
        media_tag = MediaTag(media_id=media_id, tag_id=tag_id)
        session.add(media_tag)
        await session.commit()


async def list_tags(session: AsyncSession) -> list[Tag]:
    """List all tags."""
    result = await session.execute(select(Tag))
    return result.scalars().all()
