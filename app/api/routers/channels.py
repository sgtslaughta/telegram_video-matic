"""Channels router: list channels and topics."""
import base64
from fastapi import APIRouter, Depends, Request, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api.deps import get_db, require_app_auth
from app.api.schemas import ChannelRead, TopicRead
from app.db.models import Channel, Topic, Subscription, MediaItem
from app.db.repositories import channels as channels_repo
from app.db.repositories import topics as topics_repo
from app.telegram.dtos import ChannelDTO, TopicDTO

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


@router.get("/{channel_id}/browse")
async def browse_channel(
    channel_id: int,
    request: Request,
    topic_id: int | None = Query(None),
    limit: int = Query(100, ge=1, le=300),
    db: AsyncSession = Depends(get_db),
):
    """GET /api/channels/{id}/browse — live media list merged with download status.

    Each item shows its real status (or 'available' if no subscription has captured
    it) and which subscription targets it.
    """
    channel = await db.get(Channel, channel_id)
    if not channel:
        return []
    svc = getattr(request.app.state, "tg_service", None)
    if not (svc and svc.client):
        return []

    # Which subscription (if any) targets this channel + topic?
    subs = (await db.execute(
        select(Subscription).where(Subscription.channel_id == channel_id)
    )).scalars().all()
    targeting = next(
        (s for s in subs if s.topic_id is None or s.topic_id == topic_id), None
    )

    # Existing captured items keyed by tg_msg_id.
    mq = select(MediaItem).where(MediaItem.channel_id == channel_id)
    if topic_id:
        mq = mq.where(MediaItem.topic_id == topic_id)
    existing = {m.tg_msg_id: m for m in (await db.execute(mq)).scalars().all()}

    chan_dto = ChannelDTO(
        tg_id=channel.tg_id, title=channel.title, username=channel.username,
        is_forum=channel.is_forum, photo_b64=channel.photo_b64, raw={},
    )
    topic_dto = None
    if topic_id:
        tp = await db.get(Topic, topic_id)
        if tp:
            topic_dto = TopicDTO(
                tg_topic_id=tp.tg_topic_id, title=tp.title,
                channel_tg_id=channel.tg_id, raw={},
            )

    out = []
    try:
        async for it in svc.browse_media(chan_dto, topic_dto, limit=limit):
            m = existing.get(it["tg_msg_id"])
            out.append({
                **it,
                "media_id": m.id if m else None,
                "status": (str(m.status) if m else "available"),
                "subscription_id": (m.subscription_id if m else (targeting.id if targeting else None)),
                "subscription_label": (targeting.storage_path if targeting else None),
            })
    except Exception as e:
        print(f"[browse] failed for channel {channel_id}: {e!r}")
    return out


@router.get("/{channel_id}/thumb/{tg_msg_id}")
async def browse_thumb(channel_id: int, tg_msg_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    """GET /api/channels/{id}/thumb/{msg} — thumbnail for a live (un-captured) message."""
    channel = await db.get(Channel, channel_id)
    svc = getattr(request.app.state, "tg_service", None)
    if not channel or not (svc and svc.client):
        raise HTTPException(status_code=404, detail="Not available")
    b64 = await svc.thumb_b64_for(channel.tg_id, tg_msg_id)
    if not b64:
        raise HTTPException(status_code=404, detail="Thumbnail not found")
    return StreamingResponse(
        iter([base64.b64decode(b64)]),
        media_type="image/jpeg",
        headers={"Cache-Control": "public, max-age=86400"},
    )


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
