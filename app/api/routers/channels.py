"""Channels router: list channels and topics."""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api.deps import get_db, require_app_auth
from app.api.schemas import ChannelRead, TopicRead
from app.db.models import Channel, Topic
from app.db.repositories import channels as channels_repo
from app.db.repositories import topics as topics_repo
from app.telegram.dtos import ChannelDTO

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
async def list_topics(channel_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    """GET /api/channels/{id}/topics — sync live topics into the DB, then list them."""
    svc = getattr(request.app.state, "tg_service", None)
    channel = await db.get(Channel, channel_id)
    if channel and svc and svc.client:
        try:
            if not svc.client.is_connected():
                await svc.client.connect()
            dto = ChannelDTO(
                tg_id=channel.tg_id, title=channel.title, username=channel.username,
                is_forum=channel.is_forum, photo_b64=channel.photo_b64, raw={},
            )
            for t in await svc.list_topics(dto):
                await topics_repo.upsert(db, channel_id, t.tg_topic_id, t.title, None)
        except Exception as e:
            print(f"[channels] topic sync failed for {channel_id}: {e!r}")

    result = await db.execute(select(Topic).where(Topic.channel_id == channel_id))
    topics = result.scalars().all()
    return [TopicRead.from_orm(t) for t in topics]
