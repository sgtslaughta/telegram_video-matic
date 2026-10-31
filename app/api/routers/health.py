"""Health check router: reports the sync worker, not just the web server."""
from datetime import datetime, timezone

from fastapi import APIRouter, Request, Response

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
async def health(request: Request, response: Response):
    """GET /api/health — 503 when Telegram is down or polling has stalled, so
    Docker marks the container unhealthy instead of hiding a dead poller."""
    state = request.app.state
    engine = getattr(state, "engine", None)
    client = getattr(getattr(state, "tg_service", None), "client", None)
    if engine is None or client is None:
        return {"status": "ok", "telegram": "unconfigured"}
    last = engine.last_ok_poll_at
    body = {
        "status": "ok",
        "telegram": "connected" if client.is_connected() else "disconnected",
        "last_ok_poll_at": last.isoformat() if last else None,
    }
    age = (datetime.now(timezone.utc) - last).total_seconds() if last else None
    if body["telegram"] == "disconnected":
        body["status"] = "down"
    elif age is None or age > 3 * engine.poll_interval_sec:
        body["status"] = "stale"
    if body["status"] != "ok":
        response.status_code = 503
    return body
