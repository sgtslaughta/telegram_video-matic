"""Downloads router — list active download jobs."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, require_app_auth
from app.api.schemas import DownloadJobRead
from app.db.repositories import downloads

router = APIRouter(
    prefix="/api/downloads",
    tags=["downloads"],
    dependencies=[Depends(require_app_auth)],
)


@router.get("/active")
async def active_downloads(db: AsyncSession = Depends(get_db)):
    """GET /api/downloads/active — list active download jobs."""
    jobs = await downloads.list_active(db)
    return [DownloadJobRead.from_orm(job) for job in jobs]
