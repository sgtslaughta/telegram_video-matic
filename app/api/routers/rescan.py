"""Subscription rescan + filter preview."""
from datetime import datetime
from types import SimpleNamespace
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_app_auth
from app.api.routers.subscriptions import _validate_regex
from app.db import repositories as repo
from app.db.models import Channel, FilterMode, SubMode, Topic
from app.sync.engine import classify
from app.sync.rescan import rescan
from app.telegram.dtos import ChannelDTO, TopicDTO

router = APIRouter(prefix="/api/subscriptions", tags=["subscriptions"],
                   dependencies=[Depends(require_app_auth)])


class RescanRequest(BaseModel):
    days: int = Field(ge=1, le=365)


class PreviewRequest(BaseModel):
    channel_id: int
    topic_id: Optional[int] = None
    filter_regex: Optional[str] = None
    filter_mode: str = FilterMode.INCLUDE
    min_size_mb: Optional[int] = None
    max_size_mb: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    schedule_days: Optional[list[str]] = None


@router.post("/preview-filter")
async def preview_filter(req: PreviewRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """Classify the latest 50 videos against an unsaved filter. Writes nothing."""
    _validate_regex(req.filter_regex)
    ch = await db.get(Channel, req.channel_id)
    if not ch:
        raise HTTPException(404, "Channel not found")
    tg = getattr(request.app.state, "tg_service", None)
    if tg is None:
        raise HTTPException(503, "Telegram not connected")
    chan = ChannelDTO(tg_id=ch.tg_id, title=ch.title, username=ch.username,
                      is_forum=ch.is_forum, photo_b64=ch.photo_b64, raw={})
    topic = None
    if req.topic_id:
        tp = await db.get(Topic, req.topic_id)
        if tp:
            topic = TopicDTO(tg_topic_id=tp.tg_topic_id, title=tp.title, channel_tg_id=ch.tg_id, raw={})
    sub = SimpleNamespace(
        enabled=True, filter_regex=req.filter_regex, filter_mode=req.filter_mode,
        min_size_mb=req.min_size_mb, max_size_mb=req.max_size_mb,
        date_from=req.date_from, date_to=req.date_to,
        mode=SubMode.SCHEDULED if req.schedule_days else SubMode.IMMEDIATE,
        schedule_days=req.schedule_days or [])
    out = []
    async for m in tg.iter_media(chan, topic, limit=50):
        status, reason = classify(sub, m)
        out.append({"tg_msg_id": m.tg_msg_id, "file_name": m.file_name,
                    "caption": (m.caption or "")[:200], "size_bytes": m.size_bytes,
                    "date_posted": m.date_posted,
                    "would": "skip" if status == "skip" else "download", "reason": reason})
    return out


@router.post("/{sub_id}/rescan")
async def rescan_subscription(sub_id: int, req: RescanRequest, request: Request,
                              db: AsyncSession = Depends(get_db)):
    """Rescan the last N days; returns {found, queued, skipped}. Runs inline."""
    sub = await repo.subscriptions.get(db, sub_id)
    if not sub:
        raise HTTPException(404, "Subscription not found")
    engine = getattr(request.app.state, "engine", None)
    if engine is None:
        raise HTTPException(503, "Sync engine not running")
    return await rescan(engine, db, sub, req.days)
