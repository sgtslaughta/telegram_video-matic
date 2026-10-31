"""Rescan the last N days of a subscription's channel/topic."""
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.db.models import EventLevel, MediaItem, MediaStatus
from app.db.repositories import events, media
from app.sync.engine import classify


async def rescan(engine, session, sub, days: int) -> dict:
    """Upsert + classify messages posted in the last `days` days.

    Items already in the DB are left untouched. Mirrors SyncEngine._poll_one_sub.
    """
    chan, topic = await engine._sub_dtos(session, sub)
    since = datetime.now(timezone.utc) - timedelta(days=days)
    found = queued = skipped = 0
    async for dto in engine.tg_service.iter_media(chan, topic, since_date=since):
        exists = (await session.execute(
            select(MediaItem.id).where(MediaItem.channel_id == sub.channel_id,
                                       MediaItem.tg_msg_id == dto.tg_msg_id)
        )).first()
        if exists:
            continue
        item = await media.upsert_from_tg_dto(session, dto, sub.id, sub.channel_id, sub.topic_id)
        found += 1
        status, reason = classify(sub, item)
        item.skip_reason = reason if status == "skip" else None
        if status == "skip":
            await media.set_status(session, item.id, MediaStatus.SKIPPED)
            skipped += 1
        else:
            await media.set_status(session, item.id, MediaStatus.PENDING)
            queued += 1
        try:
            await engine.plugin_host.dispatch("on_media_discovered", item)
        except Exception as e:
            await events.add(session, level=EventLevel.WARNING, kind="plugin",
                             message=f"Plugin error on_media_discovered: {e}")
    if found:
        await events.add(session, level=EventLevel.INFO, kind="sync", subscription_id=sub.id,
                         message=f"Rescan {days}d: found {found}, queued {queued}, skipped {skipped}")
    await session.commit()
    return {"found": found, "queued": queued, "skipped": skipped}
