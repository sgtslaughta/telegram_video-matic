"""Storage router: disk usage, deletion preview, paused-cleanup confirm,
untracked files (listed for the user to decide, never auto-deleted)."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_app_auth
from app.db.models import MediaItem, MediaStatus
from app.db.repositories import settings
from app.sync import retention

router = APIRouter(prefix="/api/storage", tags=["storage"], dependencies=[Depends(require_app_auth)])

VIDEO_EXT = {".mkv", ".mp4", ".avi", ".mov", ".m4v", ".ts", ".webm", ".wmv"}
UNTRACKED_LIMIT = 500


def media_root(request: Request) -> Path:
    root = getattr(request.app.state, "media_root", None) or os.getenv("MEDIA_ROOT", "/media")
    return Path(root).resolve()


async def _tracked(db) -> set[str]:
    rows = (await db.execute(select(MediaItem.local_path).where(MediaItem.local_path.is_not(None)))).scalars()
    return {str(Path(p).resolve()) for p in rows}


def _untracked(root: Path, tracked: set[str]) -> list[dict]:
    out = []
    for dirpath, _dirs, files in os.walk(root):
        for f in files:
            p = Path(dirpath) / f
            if p.suffix.lower() in VIDEO_EXT and str(p.resolve()) not in tracked:
                try:
                    st = p.stat()
                except OSError:
                    continue
                out.append({"path": str(p.relative_to(root)), "size_bytes": st.st_size,
                            "modified": datetime.fromtimestamp(st.st_mtime, timezone.utc).isoformat()})
    return sorted(out, key=lambda u: u["path"])


@router.get("")
async def overview(request: Request, db: AsyncSession = Depends(get_db)):
    root = media_root(request)
    used, total = retention.disk(str(root))
    items = (await db.execute(select(MediaItem).where(MediaItem.status == MediaStatus.DOWNLOADED))).scalars().all()
    folders: dict[str, dict] = {}
    for i in items:
        try:
            rel = Path(i.local_path).resolve().relative_to(root).parts[:-1] if i.local_path else ()
        except ValueError:
            rel = ("(outside media root)",)
        key = "/".join(rel[:2]) or "."
        f = folders.setdefault(key, {"path": key, "count": 0, "bytes": 0})
        f["count"] += 1
        f["bytes"] += i.size_bytes or 0
    untracked = _untracked(root, await _tracked(db))
    paused = await settings.get(db, "prune_paused", default="")
    return {
        "media_root": str(root),
        "disk": {"used": used, "total": total, "pct": round(100 * used / total, 1) if total else None},
        "folders": sorted(folders.values(), key=lambda f: -f["bytes"]),
        "preview": await retention.preview(db, datetime.now(timezone.utc), days=7),
        "paused": json.loads(paused) if paused else None,
        "untracked": {"count": len(untracked), "bytes": sum(u["size_bytes"] for u in untracked),
                      "items": untracked[:UNTRACKED_LIMIT]},
    }


@router.post("/prune/confirm")
async def confirm_prune(request: Request, db: AsyncSession = Depends(get_db)):
    """Run a cleanup the mass-delete cap paused, once."""
    return await retention.run(db, str(media_root(request)), confirmed=True)


class PathIn(BaseModel):
    path: str


@router.delete("/untracked")
async def delete_untracked(body: PathIn, request: Request, db: AsyncSession = Depends(get_db)):
    root = media_root(request)
    target = (root / body.path).resolve()
    if not target.is_relative_to(root) or target == root:
        raise HTTPException(400, "Path must be inside the media folder.")
    if target.suffix.lower() not in VIDEO_EXT or not target.is_file():
        raise HTTPException(404, "No such video file.")
    if str(target) in await _tracked(db):
        raise HTTPException(409, "This file is tracked. Delete it from the library instead.")
    target.unlink()
    return {"deleted": body.path}
