"""Media router: list/get/download/requeue/thumb."""
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, require_app_auth
from app.api.schemas import MediaItemRead
from app.db.models import Channel
from app.db.repositories import media
import base64

router = APIRouter(prefix="/api/media", tags=["media"], dependencies=[Depends(require_app_auth)])


@router.get("")
async def list_media(
    status: str | None = Query(None),
    sub_id: int | None = Query(None),
    channel_id: int | None = Query(None),
    topic_id: int | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """GET /api/media — list media with filters and pagination."""
    items = await media.list_filtered(
        db,
        status=status,
        sub_id=sub_id,
        channel_id=channel_id,
        topic_id=topic_id,
        limit=limit,
        offset=offset,
    )
    return [MediaItemRead.from_orm(item) for item in items]


@router.post("/clear")
async def clear_media(db: AsyncSession = Depends(get_db)):
    """POST /api/media/clear — purge all media items and download jobs (keeps
    account, subscriptions, channels). Useful to reset after bad/partial scans."""
    from sqlalchemy import delete
    from app.db.models import MediaItem, DownloadJob
    await db.execute(delete(DownloadJob))
    await db.execute(delete(MediaItem))
    await db.commit()
    return {"status": "cleared"}


@router.get("/{media_id}")
async def get_media(media_id: int, db: AsyncSession = Depends(get_db)):
    """GET /api/media/{id} — get single media item."""
    item = await media.get(db, media_id)
    if not item:
        raise HTTPException(status_code=404, detail="Media not found")
    return MediaItemRead.from_orm(item)


@router.post("/{media_id}/download")
async def download_media(
    media_id: int,
    db: AsyncSession = Depends(get_db),
):
    """POST /api/media/{id}/download — manual download trigger."""
    item = await media.get(db, media_id)
    if not item:
        raise HTTPException(status_code=404, detail="Media not found")

    await media.set_status(db, media_id, "queued")
    return {"status": "queued"}


@router.post("/{media_id}/requeue")
async def requeue_media(media_id: int, db: AsyncSession = Depends(get_db)):
    """POST /api/media/{id}/requeue — reset to pending."""
    await media.set_status(db, media_id, "pending")
    return {"status": "pending"}


@router.get("/{media_id}/thumb")
async def get_thumb(media_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    """GET /api/media/{id}/thumb — serve cached thumbnail, fetching it lazily."""
    item = await media.get(db, media_id)
    if not item:
        raise HTTPException(status_code=404, detail="Media not found")

    # Lazily fetch + cache the thumbnail from Telegram on first request.
    if not item.thumb_b64:
        svc = getattr(request.app.state, "tg_service", None)
        ch = await db.get(Channel, item.channel_id)
        if svc and svc.client and ch:
            b64 = await svc.thumb_b64_for(ch.tg_id, item.tg_msg_id)
            if b64:
                item.thumb_b64 = b64
                await db.commit()

    if not item.thumb_b64:
        raise HTTPException(status_code=404, detail="Thumbnail not found")

    thumb_bytes = base64.b64decode(item.thumb_b64)
    return StreamingResponse(
        iter([thumb_bytes]),
        media_type="image/jpeg",
        headers={"Cache-Control": "public, max-age=86400"},
    )


class KeepIn(BaseModel):
    keep: bool


@router.patch("/{media_id}/keep")
async def set_keep(media_id: int, body: KeepIn, db: AsyncSession = Depends(get_db)):
    """Pin (or unpin) an item so retention never deletes it."""
    item = await media.get(db, media_id)
    if not item:
        raise HTTPException(status_code=404, detail="Media not found")
    item.keep = body.keep
    await db.commit()
    return {"id": media_id, "keep": body.keep}


@router.get("/{media_id}/stream")
async def stream(media_id: int, db: AsyncSession = Depends(get_db)):
    """Stream the downloaded file (HTTP Range supported, so the player can seek)."""
    from pathlib import Path
    from fastapi.responses import FileResponse
    item = await media.get(db, media_id)
    if not item or not item.local_path or not Path(item.local_path).is_file():
        raise HTTPException(status_code=404, detail="No downloaded file for this item")
    # Never trust the Telegram-supplied mime: only real video types play inline;
    # anything else downloads as opaque bytes. nosniff + sandbox CSP stop the
    # browser from ever treating the file as HTML on our origin.
    mime = (item.mime or "").lower()
    playable = mime.startswith("video/") and "html" not in mime and "xml" not in mime
    resp = FileResponse(item.local_path, media_type=mime if playable else "application/octet-stream",
                        filename=Path(item.local_path).name,
                        content_disposition_type="inline" if playable else "attachment")
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["Content-Security-Policy"] = "default-src 'none'; sandbox"
    return resp
