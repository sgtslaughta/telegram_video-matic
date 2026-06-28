"""Rugby plugin HTTP API, mounted by the host under /api/plugins/rugby.

Handlers resolve the live RugbyService off the plugin host so the router stays a
thin shell over the service. Auth reuses the app-wide require_app_auth.
"""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from pydantic import BaseModel

from app.api.deps import require_app_auth

router = APIRouter(
    prefix="/api/plugins/rugby",
    tags=["rugby"],
    dependencies=[Depends(require_app_auth)],
)


def _service(request: Request):
    host = getattr(request.app.state, "plugin_host", None)
    entry = host._entry("rugby") if host else None
    if entry is None:
        raise HTTPException(status_code=503, detail="Rugby plugin not loaded")
    return entry.instance.service


class MatchPatch(BaseModel):
    status: str | None = None
    fixture_id: int | None = None


class SubLeague(BaseModel):
    league_id: int | None = None


@router.get("/status")
async def status(request: Request):
    return await _service(request).status_snapshot()


@router.get("/leagues")
async def leagues(request: Request, tracked: bool | None = None):
    return await _service(request).list_leagues(tracked=tracked)


@router.post("/refresh")
async def refresh(request: Request, bg: BackgroundTasks):
    bg.add_task(_service(request).refresh_catalog)
    return {"scheduled": True}


@router.post("/leagues/{league_id}/refresh")
async def refresh_league(league_id: int, request: Request, bg: BackgroundTasks):
    bg.add_task(_service(request).deep_fetch, league_id)
    return {"scheduled": True}


@router.get("/matches")
async def matches(request: Request, status: str | None = "needs_review"):
    return await _service(request).list_matches(status=status)


@router.patch("/matches/{media_id}")
async def patch_match(media_id: int, body: MatchPatch, request: Request):
    updated = await _service(request).update_match(
        media_id, status=body.status, fixture_id=body.fixture_id)
    if updated is None:
        raise HTTPException(status_code=404, detail="Match not found")
    return updated


@router.put("/subscriptions/{sub_id}")
async def set_subscription(sub_id: int, body: SubLeague, request: Request,
                           bg: BackgroundTasks):
    # Deep fetch can be slow; run it in the background after the link is saved.
    svc = _service(request)
    if body.league_id is None:
        await svc.set_subscription_league(sub_id, None)
    else:
        await svc._set_link_only(sub_id, body.league_id)
        bg.add_task(svc.deep_fetch, body.league_id)
    return {"ok": True, "league_id": body.league_id}
