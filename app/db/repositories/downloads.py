from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
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
