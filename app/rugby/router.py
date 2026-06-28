"""Rugby plugin HTTP API, mounted by the host under /api/plugins/rugby.

Handlers resolve the live RugbyService off the plugin host so the router stays a
thin shell over the service. Auth reuses the app-wide require_app_auth.
"""

from datetime import datetime

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


class PreviewRequest(BaseModel):
    league_id: int
    text: str


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


@router.post("/rescan")
async def rescan(request: Request, bg: BackgroundTasks):
    """Manual 'Scan now': detect leagues from every channel's topic names +
    cached titles, refresh tracked leagues, then deep-fetch all."""
    bg.add_task(_service(request).rescan)
    return {"scheduled": True}


@router.post("/leagues/{league_id}/refresh")
async def refresh_league(league_id: int, request: Request, bg: BackgroundTasks):
    bg.add_task(_service(request).deep_fetch, league_id)
    return {"scheduled": True}


@router.get("/leagues/{league_id}/fixtures")
async def fixtures(league_id: int, request: Request, season: str | None = None):
    return await _service(request).list_fixtures(league_id, season=season)


@router.post("/channels/{channel_id}/autodetect")
async def autodetect(channel_id: int, request: Request, bg: BackgroundTasks):
    """Detect leagues from a channel's topic names + cached titles, deep-fetch them."""
    svc = _service(request)
    detected = await svc.detect_channel_leagues(channel_id)
    bg.add_task(svc.autofetch_channel, channel_id)
    return {"detected": detected, "scheduled": True}


@router.get("/enrichment")
async def enrichment(channel_id: int, request: Request):
    """Match data for a channel's media, keyed by tg_msg_id (for Browse cards/drawer)."""
    return await _service(request).enrichment(channel_id)


@router.get("/enrichment/by-media")
async def enrichment_by_media(request: Request, ids: str = ""):
    """Match data keyed by media_id for a comma-separated id list (Downloads)."""
    media_ids = [int(x) for x in ids.split(",") if x.strip().isdigit()]
    return await _service(request).enrichment_by_media(media_ids)


class EnrichMessage(BaseModel):
    tg_msg_id: int
    text: str | None = None
    date: datetime | None = None


class EnrichMessages(BaseModel):
    messages: list[EnrichMessage]


@router.post("/enrichment/messages")
async def enrichment_messages(body: EnrichMessages, request: Request,
                              bg: BackgroundTasks):
    """Enrich LIVE browsed messages (not cached), keyed by tg_msg_id. Matches
    locally now; schedules a targeted single lookup for any misses so they
    appear on the next load."""
    svc = _service(request)
    msgs = [{"tg_msg_id": m.tg_msg_id, "text": m.text, "date": m.date}
            for m in body.messages]
    result = await svc.enrich_messages(msgs)
    misses = [m for m in msgs if m["tg_msg_id"] not in result]
    if misses:
        bg.add_task(svc.ondemand_fill, misses)
    return {str(k): v for k, v in result.items()}


@router.post("/preview")
async def preview(body: PreviewRequest, request: Request):
    """Dry-run match for the subscription wizard preview."""
    return await _service(request).preview(body.league_id, body.text)


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


@router.get("/subscriptions/{sub_id}")
async def get_subscription(sub_id: int, request: Request):
    """Return the league linked to this subscription (for the editor to preselect)."""
    svc = _service(request)
    return {"league_id": await svc.get_subscription_league(sub_id)}


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
