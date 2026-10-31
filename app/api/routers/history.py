"""History feed + failed ("wanted") downloads."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_app_auth
from app.db.models import DownloadJob, Event, MediaItem, MediaStatus

router = APIRouter(prefix="/api", tags=["history"], dependencies=[Depends(require_app_auth)])


def _event_kind(e: Event) -> str:
    msg = e.message or ""
    if e.kind == "download":
        if e.level == "success":
            return "downloaded"
        if msg.startswith("Download failed after"):
            return "failed"
    elif e.kind == "prune":
        return "deleted"
    elif e.kind == "rugby" and msg.startswith("Matched"):
        return "matched"
    return "other"


@router.get("/history")
async def history(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    media_id: int | None = None,
    kind: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Newest-first per-media history: events (with media_id) + skipped items.

    ponytail: two queries over-fetched to limit+offset each and merged in
    Python; ceiling = limit+offset <= ~1000 rows per source. `kind` filters
    after mapping, so a filtered page can be short of `limit`.
    """
    n = limit + offset
    eq = (select(Event, MediaItem.file_name).join(MediaItem, MediaItem.id == Event.media_id)
          .where(Event.media_id.is_not(None)))
    sq = select(MediaItem).where(MediaItem.status == MediaStatus.SKIPPED)
    if media_id is not None:
        eq, sq = eq.where(Event.media_id == media_id), sq.where(MediaItem.id == media_id)
    rows = []
    for e, fname in (await db.execute(eq.order_by(desc(Event.created_at), desc(Event.id)).limit(n))).all():
        rows.append({"at": e.created_at, "kind": _event_kind(e), "media_id": e.media_id,
                     "file_name": fname, "message": e.message, "level": str(e.level)})
    for m in (await db.execute(sq.order_by(desc(MediaItem.created_at)).limit(n))).scalars():
        rows.append({"at": m.created_at, "kind": "skipped", "media_id": m.id,
                     "file_name": m.file_name, "message": m.skip_reason or "Filtered", "level": "info"})
    if kind:
        rows = [r for r in rows if r["kind"] == kind]
    rows.sort(key=lambda r: r["at"], reverse=True)
    return rows[offset:offset + limit]


@router.get("/wanted/failed")
async def wanted_failed(db: AsyncSession = Depends(get_db)):
    """Failed media with the latest download job's error + attempt."""
    items = (await db.execute(select(MediaItem).where(MediaItem.status == MediaStatus.FAILED)
                              .order_by(desc(MediaItem.updated_at)))).scalars().all()
    out = []
    for m in items:
        job = (await db.execute(select(DownloadJob).where(DownloadJob.media_id == m.id)
                                .order_by(desc(DownloadJob.id)).limit(1))).scalar_one_or_none()
        out.append({"media_id": m.id, "file_name": m.file_name, "caption": (m.caption or "")[:200],
                    "size_bytes": m.size_bytes, "date_posted": m.date_posted,
                    "subscription_id": m.subscription_id,
                    "error": job.error if job else None, "attempt": job.attempt if job else 0,
                    "last_attempt_at": job.updated_at if job else None})
    return out
