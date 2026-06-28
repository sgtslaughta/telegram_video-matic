"""Filesystem browse router — lists directories for the storage-path picker.

Read-only and sandboxed to MEDIA_ROOT: paths are resolved (collapsing `..` and
symlinks) and rejected unless they stay within MEDIA_ROOT, so the API can never
enumerate the container filesystem outside the mounted media volume.
"""
import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import require_app_auth

router = APIRouter(
    prefix="/api/fs",
    tags=["fs"],
    dependencies=[Depends(require_app_auth)],
)


def _media_root() -> Path:
    """The sandbox root. Matches the app's media_root default (config.py)."""
    return Path(os.getenv("MEDIA_ROOT", "/downloads")).resolve()


def _safe_resolve(path: str | None) -> Path:
    """Resolve `path` (default: MEDIA_ROOT) and guarantee it stays inside the
    sandbox root. Raises 400 on traversal/symlink escape."""
    root = _media_root()
    target = Path(path).resolve() if path else root
    if target != root and root not in target.parents:
        raise HTTPException(status_code=400, detail="Path is outside the media root")
    return target


@router.get("/dirs")
async def list_dirs(path: str | None = Query(None)):
    """GET /api/fs/dirs?path= — immediate subdirectories of `path` (defaults to
    MEDIA_ROOT). Hidden dirs (dotfiles, e.g. .partial) are omitted."""
    target = _safe_resolve(path)
    if not target.is_dir():
        raise HTTPException(status_code=404, detail="Directory not found")
    try:
        dirs = sorted(
            e.name for e in os.scandir(target)
            if e.is_dir() and not e.name.startswith(".")
        )
    except OSError as e:
        raise HTTPException(status_code=400, detail=str(e))
    root = _media_root()
    return {
        "root": str(root),
        "path": str(target),
        "parent": None if target == root else str(target.parent),
        "dirs": dirs,
    }
