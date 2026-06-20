"""Downloads router — list active jobs; cancel/pause/resume."""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, require_app_auth
from app.api.schemas import DownloadJobRead
from app.db.models import JobStatus, MediaStatus
from app.db.repositories import downloads, media

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


async def _job_or_404(db: AsyncSession, job_id: int):
    job = await downloads.get(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/{job_id}/cancel")
async def cancel_download(job_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    """POST — cancel a download (abort in-flight, discard partial)."""
    job = await _job_or_404(db, job_id)
    engine = getattr(request.app.state, "engine", None)
    if engine:
        engine.request_cancel(job.media_id)
    # If it wasn't actively running, settle the state directly.
    if job.status != JobStatus.RUNNING:
        await downloads.set_status(db, job.id, JobStatus.CANCELED)
        await media.set_status(db, job.media_id, MediaStatus.SKIPPED)
    return {"status": "canceling" if job.status == JobStatus.RUNNING else "canceled"}


@router.post("/{job_id}/pause")
async def pause_download(job_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    """POST — pause a download (abort in-flight, keep partial for resume)."""
    job = await _job_or_404(db, job_id)
    engine = getattr(request.app.state, "engine", None)
    if engine:
        engine.request_pause(job.media_id)
    if job.status != JobStatus.RUNNING:
        await downloads.set_status(db, job.id, JobStatus.PAUSED)
        await media.set_status(db, job.media_id, MediaStatus.PAUSED)
    return {"status": "pausing" if job.status == JobStatus.RUNNING else "paused"}


@router.post("/{job_id}/resume")
async def resume_download(job_id: int, db: AsyncSession = Depends(get_db)):
    """POST — resume a paused download: requeue so the downloader picks it up."""
    job = await _job_or_404(db, job_id)
    await downloads.set_status(db, job.id, JobStatus.QUEUED)
    await media.set_status(db, job.media_id, MediaStatus.PENDING)
    return {"status": "queued"}
