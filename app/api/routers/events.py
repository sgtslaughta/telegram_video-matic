"""Events router — paginated activity feed."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, require_app_auth
from app.api.schemas import EventRead
from app.db.repositories import events

router = APIRouter(
    prefix="/api/events",
    tags=["events"],
    dependencies=[Depends(require_app_auth)],
)


@router.get("")
async def list_events(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """GET /api/events — paginated activity feed."""
    items = await events.list(db, limit=limit, offset=offset)
    return [EventRead.from_orm(e) for e in items]
