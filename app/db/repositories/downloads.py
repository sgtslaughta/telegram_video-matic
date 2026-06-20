from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.db.models import DownloadJob, JobStatus, MediaStatus
from app.db.repositories import media


async def start(session: AsyncSession, media_id: int) -> DownloadJob:
    """Start a new download job for a media item."""
    job = DownloadJob(
        media_id=media_id,
        status=JobStatus.QUEUED,
        progress=0.0,
        bytes_done=0,
        attempt=1,
    )
    session.add(job)
    await session.commit()
    return job


async def get_or_start(session: AsyncSession, media_id: int) -> DownloadJob:
    """Reuse the latest non-terminal job for a media item (resume case), else
    start a fresh one. Avoids duplicate job rows when a paused download resumes."""
    existing = await get_latest_for_media(session, media_id)
    if existing and existing.status in (JobStatus.QUEUED, JobStatus.RUNNING, JobStatus.PAUSED):
        existing.status = JobStatus.RUNNING
        existing.error = None
        await session.commit()
        return existing
    return await start(session, media_id)


async def set_status(
    session: AsyncSession,
    job_id: int,
    status: JobStatus,
) -> DownloadJob | None:
    """Set a job's status directly (cancel/pause)."""
    job = await session.get(DownloadJob, job_id)
    if job:
        job.status = status
        await session.commit()
    return job


async def running(
    session: AsyncSession,
    job_id: int,
    bytes_total: int | None = None,
) -> DownloadJob | None:
    """Mark a job as actively downloading; record total size if known."""
    job = await session.get(DownloadJob, job_id)
    if job:
        job.status = JobStatus.RUNNING
        if bytes_total:
            job.bytes_total = bytes_total
        await session.commit()
    return job


async def update_progress(
    session: AsyncSession,
    job_id: int,
    bytes_done: int,
    eta_sec: int | None = None,
    speed_bps: int | None = None,
) -> DownloadJob | None:
    """Update download progress."""
    job = await session.get(DownloadJob, job_id)
    if job:
        job.bytes_done = bytes_done
        job.eta_sec = eta_sec
        job.speed_bps = speed_bps
        if job.bytes_total:
            job.progress = min(bytes_done / job.bytes_total, 1.0)
        await session.commit()
    return job


async def finish(
    session: AsyncSession,
    job_id: int,
    error: str | None = None,
) -> DownloadJob | None:
    """Mark download job as done or error."""
    job = await session.get(DownloadJob, job_id)
    if job:
        job.finished_at = datetime.now(datetime.now().astimezone().tzinfo)
        if error:
            job.status = JobStatus.ERROR
            job.error = error
        else:
            job.status = JobStatus.DONE
            job.progress = 1.0

        # Update associated media status
        await media.set_status(session, job.media_id, MediaStatus.DOWNLOADED if not error else MediaStatus.FAILED)

        await session.commit()
    return job


async def get(session: AsyncSession, job_id: int) -> DownloadJob | None:
    """Get download job by ID."""
    return await session.get(DownloadJob, job_id)


async def get_latest_for_media(session: AsyncSession, media_id: int) -> DownloadJob | None:
    """Get most recent download job for a media item (ordered by updated_at DESC)."""
    stmt = select(DownloadJob).where(DownloadJob.media_id == media_id).order_by(desc(DownloadJob.updated_at)).limit(1)
    result = await session.execute(stmt)
    return result.scalars().first()


async def list_active(session: AsyncSession) -> list[DownloadJob]:
    """List active (non-terminal) download jobs."""
    stmt = select(DownloadJob).where(
        DownloadJob.status.in_([JobStatus.QUEUED, JobStatus.RUNNING, JobStatus.PAUSED])
    )
    result = await session.execute(stmt)
    return result.scalars().all()
