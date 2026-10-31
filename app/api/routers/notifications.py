"""Notifications router: Apprise targets, spam options, Jellyfin refresh."""
import json
import uuid
from typing import Optional
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_app_auth
from app.crypto import decrypt, encrypt
from app.db.repositories import settings
from app.notify.notifier import TRIGGERS, apprise_send, target_public

router = APIRouter(prefix="/api/notifications", tags=["notifications"],
                   dependencies=[Depends(require_app_auth)])


class TargetIn(BaseModel):
    id: Optional[str] = None
    name: str = Field(min_length=1, max_length=80)
    url: Optional[str] = None  # omit to keep the stored URL
    triggers: list[str] = []


class QuietIn(BaseModel):
    enabled: bool = False
    start: int = Field(23, ge=0, le=23)
    end: int = Field(7, ge=0, le=23)


class OptionsIn(BaseModel):
    quiet: QuietIn = QuietIn()
    disk_low_pct: int = Field(95, ge=50, le=100)
    public_url: str = ""


class JellyfinIn(BaseModel):
    url: str = ""
    library_id: str = ""
    api_key: Optional[str] = None  # omit/empty to keep the stored key


class TestIn(BaseModel):
    id: Optional[str] = None
    url: Optional[str] = None


async def _targets(db) -> list[dict]:
    return json.loads(await settings.get(db, "notify_targets", default="[]") or "[]")


async def _reload(request: Request) -> None:
    st = request.app.state
    if getattr(st, "notifier", None):
        await st.notifier.load()
    if getattr(st, "jellyfin", None):
        await st.jellyfin.load(st.async_session)


@router.get("")
async def get_config(db: AsyncSession = Depends(get_db)):
    opts = json.loads(await settings.get(db, "notify_options", default="{}") or "{}")
    jf = json.loads(await settings.get(db, "jellyfin", default="{}") or "{}")
    return {
        "triggers": list(TRIGGERS),
        "targets": [target_public(t) for t in await _targets(db)],
        "options": OptionsIn(**opts).model_dump(),
        "jellyfin": {"url": jf.get("url", ""), "library_id": jf.get("library_id", ""),
                     "api_key_set": bool(jf.get("api_key_enc"))},
    }


@router.put("/targets")
async def put_targets(body: list[TargetIn], request: Request, db: AsyncSession = Depends(get_db)):
    existing = {t["id"]: t for t in await _targets(db)}
    out = []
    for t in body:
        bad = set(t.triggers) - set(TRIGGERS)
        if bad:
            raise HTTPException(422, f"Unknown triggers: {sorted(bad)}")
        prev = existing.get(t.id or "")
        if t.url:
            url_enc, scheme = encrypt(t.url.strip()), t.url.split("://", 1)[0]
        elif prev:
            url_enc, scheme = prev["url_enc"], prev.get("scheme", "")
        else:
            raise HTTPException(422, f"Target '{t.name}' needs a URL")
        out.append({"id": t.id or uuid.uuid4().hex[:12], "name": t.name, "url_enc": url_enc,
                    "scheme": scheme, "triggers": t.triggers})
    await settings.set(db, "notify_targets", json.dumps(out))
    await _reload(request)
    return [target_public(t) for t in out]


@router.put("/options")
async def put_options(body: OptionsIn, request: Request, db: AsyncSession = Depends(get_db)):
    await settings.set(db, "notify_options", body.model_dump_json())
    await _reload(request)
    return body


@router.put("/jellyfin")
async def put_jellyfin(body: JellyfinIn, request: Request, db: AsyncSession = Depends(get_db)):
    prev = json.loads(await settings.get(db, "jellyfin", default="{}") or "{}")
    # Keep the stored key only for the same origin: otherwise editing just the
    # URL would send the saved key to a new host.
    same_origin = urlsplit(body.url.strip())[:2] == urlsplit(prev.get("url", ""))[:2]
    key_enc = encrypt(body.api_key) if body.api_key else (prev.get("api_key_enc", "") if same_origin else "")
    await settings.set(db, "jellyfin", json.dumps(
        {"url": body.url.strip(), "library_id": body.library_id.strip(), "api_key_enc": key_enc}))
    await _reload(request)
    return {"url": body.url, "library_id": body.library_id, "api_key_set": bool(key_enc)}


@router.post("/test")
async def test_target(body: TestIn, db: AsyncSession = Depends(get_db)):
    url = body.url
    if not url and body.id:
        match = next((t for t in await _targets(db) if t["id"] == body.id), None)
        if not match:
            raise HTTPException(404, "Target not found")
        url = decrypt(match["url_enc"])
    if not url:
        raise HTTPException(422, "Provide a target id or url")
    ok = await apprise_send(url, "Test from Telegram Video-matic", "Notifications are working.")
    if not ok:
        raise HTTPException(502, "Apprise could not deliver. Check the URL and the service's credentials.")
    return {"ok": True}


@router.post("/jellyfin/test")
async def test_jellyfin(request: Request):
    jf = getattr(request.app.state, "jellyfin", None)
    if not jf or not (jf.url and jf.api_key):
        raise HTTPException(422, "Set the Jellyfin URL and API key first.")
    try:
        await jf.refresh()
    except Exception as e:
        code = getattr(getattr(e, "response", None), "status_code", None)
        raise HTTPException(502, f"Jellyfin refresh failed ({code or type(e).__name__}). "
                                 "Check the URL and API key.")
    return {"ok": True}
