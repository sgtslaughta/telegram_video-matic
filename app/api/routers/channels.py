"""Channels router: list channels and topics."""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api.deps import get_db, require_app_auth
from app.api.schemas import ChannelRead, TopicRead
from app.db.models import Channel, Topic
from app.db.repositories import channels as channels_repo

router = APIRouter(prefix="/api/channels", tags=["channels"], dependencies=[Depends(require_app_auth)])


@router.get("")
async def list_channels(request: Request, db: AsyncSession = Depends(get_db)):
    """GET /api/channels — sync live Telegram channels into the DB, then list them."""
    svc = getattr(request.app.state, "tg_service", None)
    if svc and svc.client:
        try:
            if not svc.client.is_connected():
                await svc.client.connect()
            for ch in await svc.list_channels():
                # raw holds a non-serializable Telethon entity → store None
                await channels_repo.upsert(
                    db, ch.tg_id, ch.title, ch.username, ch.is_forum, ch.photo_b64, None
                )
        except Exception:
            pass  # fall back to whatever is already persisted

    result = await db.execute(select(Channel))
    channels = result.scalars().all()
    return [ChannelRead.from_orm(ch) for ch in channels]


@router.get("/{channel_id}/topics")
async def list_topics(channel_id: int, db: AsyncSession = Depends(get_db)):
    """GET /api/channels/{id}/topics — list topics in channel."""
    result = await db.execute(select(Topic).where(Topic.channel_id == channel_id))
    topics = result.scalars().all()
    return [TopicRead.from_orm(t) for t in topics]
