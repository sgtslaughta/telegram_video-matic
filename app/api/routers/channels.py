"""Channels router: list channels and topics."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api.deps import get_db, require_app_auth
from app.api.schemas import ChannelRead, TopicRead
from app.db.models import Channel, Topic

router = APIRouter(prefix="/api/channels", tags=["channels"], dependencies=[Depends(require_app_auth)])


@router.get("")
async def list_channels(db: AsyncSession = Depends(get_db)):
    """GET /api/channels — list channels."""
    result = await db.execute(select(Channel))
    channels = result.scalars().all()
    return [ChannelRead.from_orm(ch) for ch in channels]


@router.get("/{channel_id}/topics")
async def list_topics(channel_id: int, db: AsyncSession = Depends(get_db)):
    """GET /api/channels/{id}/topics — list topics in channel."""
    result = await db.execute(select(Topic).where(Topic.channel_id == channel_id))
    topics = result.scalars().all()
    return [TopicRead.from_orm(t) for t in topics]
