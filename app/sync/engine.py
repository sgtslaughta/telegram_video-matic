"""Sync engine components: filter classifier, poller, downloader, maintenance."""
import re
import asyncio
import tempfile
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Tuple, Callable, Any
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, async_sessionmaker
from telethon.errors import FloodWaitError

from app.db.models import SubMode, FilterMode, MediaStatus, EventLevel, JobStatus
from app.db.repositories import subscriptions, media, events, downloads
from app.sync.naming import detect_season_episode, render_path

# ponytail: regex compiled once, explicit season/episode pattern detection
_SE_PATTERN = re.compile(r'(S\d+E\d+|\d+x\d+|Season\s+\d+.*Episode\s+\d+)', re.IGNORECASE)


def classify(subscription, media, today: Optional[str] = None) -> Tuple[str, Optional[str]]:
    """
    Pure filter classifier: decides keep vs. skip for a media item under a subscription.

    Gates applied in order:
    1. Enabled: subscription.enabled must be True
    2. Schedule: if SubMode.scheduled, today's weekday must be in subscription.schedule_days
    3. Regex: if filter_regex is set, must match (include) or not match (exclude)
    4. Size: size_bytes must be within min_size_mb and max_size_mb bounds

    Args:
        subscription: Object with enabled, mode, schedule_days, filter_regex, filter_mode,
                     min_size_mb, max_size_mb attributes
        media: Object with file_name, caption, size_bytes attributes
        today: Optional 3-char weekday (e.g., "mon", "tue") for deterministic testing.
               If None, computed from datetime.now().

    Returns:
        Tuple[str, str | None]: ("keep", None) or ("skip", reason_string)
    """

    # Gate 1: Enabled check
    if not subscription.enabled:
        return ("skip", "Subscription disabled")

    # Gate 2: Schedule check
    if subscription.mode == SubMode.SCHEDULED:
        if today is None:
            today = datetime.now().strftime("%A").lower()[:3]
        if today not in subscription.schedule_days:
            return ("skip", f"Not scheduled for {today}")

    # Gate 3: Regex filter
    if subscription.filter_regex:
        # Combine file_name and caption for regex search
        text = (media.file_name or "") + " " + (media.caption or "")

        if subscription.filter_mode == FilterMode.INCLUDE:
            if not re.search(subscription.filter_regex, text, re.IGNORECASE):
                return ("skip", f"Does not match filter: {subscription.filter_regex}")
        elif subscription.filter_mode == FilterMode.EXCLUDE:
            if re.search(subscription.filter_regex, text, re.IGNORECASE):
                return ("skip", f"Matches exclude filter: {subscription.filter_regex}")

    # Gate 4: Size bounds
    if subscription.min_size_mb is not None and media.size_bytes:
        if media.size_bytes < subscription.min_size_mb * 1024 * 1024:
            return ("skip", f"Below minimum size {subscription.min_size_mb} MB")

    if subscription.max_size_mb is not None and media.size_bytes:
        if media.size_bytes > subscription.max_size_mb * 1024 * 1024:
            return ("skip", f"Exceeds maximum size {subscription.max_size_mb} MB")

    # All gates passed
    return ("keep", None)


class SyncEngine:
    """Autonomous sync engine: poller, downloader, maintenance."""

    def __init__(
        self,
        session_factory: async_sessionmaker,
        tg_service: Any,
        plugin_host: Any,
        broadcast: Optional[Callable] = None,
        poll_interval_sec: int = 60,
    ):
        """Initialize SyncEngine.

        Args:
            session_factory: async_sessionmaker for DB sessions
            tg_service: TelegramService instance
            plugin_host: PluginHost instance
            broadcast: Optional async callable for WebSocket progress
            poll_interval_sec: Poller sleep interval (seconds)
        """
        self.session_factory = session_factory
        self.tg_service = tg_service
        self.plugin_host = plugin_host
        self.broadcast = broadcast or (lambda x: None)
        self.poll_interval_sec = poll_interval_sec
        self._tasks = []
        self._stop_event = asyncio.Event()

    async def _poller_once(self, session: AsyncSession) -> None:
        """Single pass of the poller: fetch media for enabled subscriptions.

        Args:
            session: Active database session
        """
        try:
            # Get all enabled subscriptions
            subs = await subscriptions.list(session, enabled_only=True)

            for sub in subs:
                try:
                    # Get max stored tg_msg_id for incremental fetch
                    last_msg_id = await media.get_max_tg_msg_id(
                        session, sub.channel_id, sub.topic_id
                    )

                    # Fetch new media from TelegramService
                    async for media_dto in self.tg_service.iter_media(
                        sub.channel_id, sub.topic_id, since_msg_id=last_msg_id
                    ):
                        # Upsert into DB
                        item = await media.upsert_from_tg_dto(session, media_dto, sub.id)

                        # Classify: keep or skip
                        status, reason = classify(sub, item)

                        if status == "skip":
                            await media.set_status(session, item.id, MediaStatus.SKIPPED)
                            await events.add(
                                session,
                                level=EventLevel.INFO,
                                kind="filter",
                                subscription_id=sub.id,
                                media_id=item.id,
                                message=reason,
                            )
                        else:
                            await media.set_status(session, item.id, MediaStatus.PENDING)

                        # Dispatch to plugins (wrapped to prevent bad plugins crashing loop)
                        try:
                            await self.plugin_host.dispatch("on_media_discovered", item)
                        except Exception as e:
                            await events.add(
                                session,
                                level=EventLevel.WARNING,
                                kind="plugin",
                                message=f"Plugin error on_media_discovered: {e}",
                            )

                    await session.commit()

                except Exception as e:
                    # Log subscription error but continue to next subscription
                    await events.add(
                        session,
                        level=EventLevel.ERROR,
                        kind="sync",
                        subscription_id=sub.id,
                        message=f"Sync error: {e}",
                    )
                    await session.commit()

        except Exception as e:
            # Global error (e.g., can't fetch subscriptions)
            await events.add(
                session,
                level=EventLevel.ERROR,
                kind="sync",
                message=f"Poller error: {e}",
            )
            await session.commit()

    async def _downloader(self) -> None:
        """Download manager: claims pending media, downloads, renames, moves into place.

        Flow:
        1. Claim pending media items (pending→queued atomic flip)
        2. For each item:
           a. Start download job
           b. Get message from Telegram
           c. Download file with progress callback
           d. Render target path using subscription template + season/episode detection
           e. Move file into place
           f. Update media status→downloaded, set local_path
           g. Finish job (success)
           h. Dispatch on_post_download hook
        3. On download/move error:
           a. Increment attempt counter
           b. If attempt <= max_attempts (5): sleep(min(2^attempt*5, 3600)) and retry
           c. If FloodWaitError: pause without incrementing attempt, retry
           d. If attempt > max_attempts: status→failed, log event, finish job with error
        """
        max_concurrent = 3  # TODO: read from config
        max_attempts = 5
        base_backoff = 5
        max_backoff = 3600

        while not self._stop_event.is_set():
            try:
                async with self.session_factory() as session:
                    # Claim pending media
                    claimed = await media.claim_pending(session, limit=max_concurrent)

                    for item in claimed:
                        # FIX 2: Check backoff elapsed-time gate for retried items
                        latest_job = await downloads.get_latest_for_media(session, item.id)
                        if latest_job and latest_job.attempt > 1 and latest_job.status == JobStatus.QUEUED:
                            # This item has been retried; check if backoff window has elapsed
                            backoff_sec = min(2 ** latest_job.attempt * base_backoff, max_backoff)
                            elapsed = (datetime.now(timezone.utc) - latest_job.updated_at).total_seconds()
                            if elapsed < backoff_sec:
                                # Backoff window not yet elapsed; release this item and try next
                                await media.set_status(session, item.id, MediaStatus.PENDING)
                                await session.commit()
                                continue

                        try:
                            # Get subscription and validate
                            sub = await subscriptions.get(session, item.subscription_id)
                            if not sub:
                                await media.set_status(session, item.id, MediaStatus.FAILED)
                                await events.add(
                                    session,
                                    level=EventLevel.ERROR,
                                    kind="download",
                                    media_id=item.id,
                                    message="Subscription not found",
                                )
                                await session.commit()
                                continue

                            # Start job
                            job = await downloads.start(session, item.id)

                            # Create temp file for download
                            temp_file = tempfile.mktemp(suffix=".tmp")

                            try:  # Download attempt
                                # Throttle broadcast: track last broadcast time
                                last_broadcast_time = [None]

                                async def on_progress(current_bytes, total_bytes):
                                    """Progress callback with ~1 Hz throttle."""
                                    now = datetime.now(timezone.utc)
                                    if last_broadcast_time[0] is None or \
                                       (now - last_broadcast_time[0]).total_seconds() >= 1.0:
                                        last_broadcast_time[0] = now
                                        await self.broadcast({
                                            "type": "download_progress",
                                            "job_id": job.id,
                                            "media_id": item.id,
                                            "progress": current_bytes / total_bytes if total_bytes else 0,
                                            "bytes_done": current_bytes,
                                            "bytes_total": total_bytes,
                                        })

                                # Download from Telegram
                                await self.tg_service.download(
                                    item.tg_msg_id,
                                    temp_file,
                                    on_progress=on_progress
                                )

                                # FIX 1: Explicit season/episode detection decision
                                # Check if filename/caption has S/E pattern
                                text = item.file_name or item.caption or ""
                                has_pattern = bool(_SE_PATTERN.search(text))
                                use_template = bool(sub.season_detection) and has_pattern

                                if use_template:
                                    # Pattern found and detection enabled: use template with season/episode
                                    season, episode = detect_season_episode(text)
                                    title = item.file_name.rsplit(".", 1)[0] if item.file_name else "unknown"
                                    ext = "." + item.file_name.rsplit(".", 1)[-1] if item.file_name else ""

                                    tokens = {
                                        "channel": sub.channel.title or "Unknown",
                                        "topic": sub.topic.title if sub.topic else "General",
                                        "season": season,
                                        "episode": episode,
                                        "title": title,
                                        "ext": ext,
                                        "original": item.file_name or "unknown",
                                        "date": item.date_posted.isoformat() if item.date_posted else "",
                                    }
                                    target_path = render_path(sub.rename_template, tokens)
                                else:
                                    # No pattern found OR detection disabled: keep original filename
                                    target_path = item.file_name or f"{item.tg_msg_id}"

                                target_full = Path(sub.storage_path) / target_path

                                # Move file into place
                                target_full.parent.mkdir(parents=True, exist_ok=True)
                                shutil.move(temp_file, str(target_full))

                                # Update DB: mark as downloaded
                                item.local_path = str(target_full)
                                item.downloaded_at = datetime.now(timezone.utc)
                                await media.set_status(session, item.id, MediaStatus.DOWNLOADED)

                                # Finish job
                                await downloads.finish(session, job.id, error=None)

                                # Dispatch plugin hook
                                try:
                                    await self.plugin_host.dispatch(
                                        "on_post_download",
                                        item,
                                        str(target_full)
                                    )
                                except Exception as e:
                                    # Log but don't fail the download
                                    await events.add(
                                        session,
                                        level=EventLevel.WARNING,
                                        kind="plugin",
                                        message=f"Plugin error on_post_download: {e}",
                                    )

                                await session.commit()

                            except FloodWaitError as e:
                                # FloodWait: pause without incrementing attempt (acceptable to block here)
                                await asyncio.sleep(min(e.seconds, 60))
                                # Mark job back to queued for retry (same attempt)
                                job.status = JobStatus.QUEUED
                                await session.commit()

                            except Exception as e:
                                # FIX 2: Non-blocking retry with elapsed-time backoff gate
                                job_db = await downloads.get(session, job.id)
                                if job_db:
                                    job_db.attempt += 1

                                    if job_db.attempt > max_attempts:
                                        # Final failure: mark as failed
                                        await media.set_status(session, item.id, MediaStatus.FAILED)
                                        job_db.error = str(e)
                                        await downloads.finish(session, job.id, error=str(e))
                                        await events.add(
                                            session,
                                            level=EventLevel.ERROR,
                                            kind="download",
                                            media_id=item.id,
                                            message=f"Download failed after {max_attempts} attempts: {e}",
                                        )
                                    else:
                                        # Non-final failure: set media back to PENDING for next cycle
                                        # ponytail: retries deferred to next poller cycle, backoff gated by elapsed-time check
                                        await media.set_status(session, item.id, MediaStatus.PENDING)
                                        job_db.status = JobStatus.QUEUED
                                        job_db.error = str(e)
                                        # NO asyncio.sleep here; next cycle will check elapsed time

                                    # Clean up temp file
                                    try:
                                        Path(temp_file).unlink(missing_ok=True)
                                    except Exception:
                                        pass

                                    await session.commit()

                        except Exception as e:
                            # Item-level error: log but continue to next item
                            await events.add(
                                session,
                                level=EventLevel.ERROR,
                                kind="download",
                                media_id=item.id,
                                message=f"Download error: {e}",
                            )
                            await session.commit()

            except Exception as e:
                # Outer error: log and continue
                async with self.session_factory() as session:
                    await events.add(
                        session,
                        level=EventLevel.ERROR,
                        kind="sync",
                        message=f"Downloader error: {e}",
                    )
                    await session.commit()

            # Sleep before next cycle
            await asyncio.sleep(1)

    async def _maintenance_pass(self, session) -> None:
        """Single pass of maintenance: drift detection and pruning.

        - Missing-file drift: DOWNLOADED items with missing local_path → PENDING + event
        - Gap drift: full iter_media reconcile finds missing media → insert + classify → PENDING/SKIPPED
        - Age pruning: DOWNLOADED items older than retention_days → delete file, status=SKIPPED
        - Disk% pruning: when disk usage >= retention_disk_pct, delete oldest DOWNLOADED files
        - Orphan tolerance: files on disk not in DB are never touched (no directory scan)
        """
        # 1. Missing-file drift: DOWNLOADED items with missing local_path
        downloaded = await media.list_by_status(session, MediaStatus.DOWNLOADED)
        for item in downloaded:
            if item.local_path and not Path(item.local_path).exists():
                await media.set_status(session, item.id, MediaStatus.PENDING)
                await events.add(
                    session,
                    level=EventLevel.WARNING,
                    kind="drift",
                    media_id=item.id,
                    message="File missing on disk, re-queued",
                )

        # 2. Gap drift: full reconcile for each enabled subscription
        gap_count = 0
        subs = await subscriptions.list(session, enabled_only=True)
        for sub in subs:
            try:
                # Full iter_media (no incremental)
                async for media_dto in self.tg_service.iter_media(
                    sub.channel_id, sub.topic_id, since_msg_id=None
                ):
                    # Check if already stored
                    existing = await media.get_by_tg_msg_id(
                        session, sub.channel_id, media_dto.tg_msg_id
                    )
                    if not existing:
                        # New gap item: upsert via lower-level function using channel_id (DB ID, not tg_id)
                        item = await media.upsert_from_tg(
                            session,
                            channel_id=sub.channel_id,
                            topic_id=media_dto.topic_tg_id,
                            subscription_id=sub.id,
                            tg_msg_id=media_dto.tg_msg_id,
                            caption=media_dto.caption,
                            file_name=media_dto.file_name,
                            mime=media_dto.mime,
                            size_bytes=media_dto.size_bytes,
                            duration_sec=media_dto.duration_sec,
                            date_posted=media_dto.date_posted,
                            thumb_b64=media_dto.thumb_b64,
                            raw=media_dto.raw,
                        )
                        status, reason = classify(sub, item)

                        if status == "skip":
                            await media.set_status(session, item.id, MediaStatus.SKIPPED)
                            await events.add(
                                session,
                                level=EventLevel.INFO,
                                kind="filter",
                                subscription_id=sub.id,
                                media_id=item.id,
                                message=reason,
                            )
                        else:
                            await media.set_status(session, item.id, MediaStatus.PENDING)

                        gap_count += 1

                await session.commit()

            except Exception as e:
                # Log subscription error but continue to next subscription
                await events.add(
                    session,
                    level=EventLevel.ERROR,
                    kind="sync",
                    subscription_id=sub.id,
                    message=f"Gap reconcile error: {e}",
                )
                await session.commit()

        # Emit summary event if gap items found
        if gap_count > 0:
            await events.add(
                session,
                level=EventLevel.INFO,
                kind="drift",
                message=f"Gap reconcile: recovered {gap_count} missing media items",
            )

        # 3. Age pruning: delete DOWNLOADED items older than retention_days
        from app.db.repositories import settings
        retention_days = await settings.get(session, "retention_days", default="90")
        try:
            retention_days = int(retention_days) if retention_days else 90
        except (ValueError, TypeError):
            retention_days = 90

        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
        old_items = await media.list_downloaded_before(session, cutoff)
        for item in old_items:
            if item.local_path and Path(item.local_path).exists():
                Path(item.local_path).unlink()
            await media.set_local_path(session, item.id, None)
            await media.set_status(session, item.id, MediaStatus.SKIPPED)
            await events.add(
                session,
                level=EventLevel.INFO,
                kind="prune",
                media_id=item.id,
                message=f"Pruned (age > {retention_days} days)",
            )

        # 4. Disk % pruning: delete oldest DOWNLOADED files until under threshold
        retention_pct = await settings.get(session, "retention_disk_pct", default="80")
        try:
            retention_pct = int(retention_pct) if retention_pct else 80
        except (ValueError, TypeError):
            retention_pct = 80

        usage = shutil.disk_usage("/")
        used_pct = 100 * usage.used / usage.total

        if used_pct >= retention_pct:
            oldest_items = await media.list_downloaded_oldest_first(session)
            for item in oldest_items:
                if item.local_path and Path(item.local_path).exists():
                    Path(item.local_path).unlink()
                await media.set_local_path(session, item.id, None)
                await media.set_status(session, item.id, MediaStatus.SKIPPED)
                await events.add(
                    session,
                    level=EventLevel.INFO,
                    kind="prune",
                    media_id=item.id,
                    message="Pruned (disk usage)",
                )

                # Re-check disk usage
                usage = shutil.disk_usage("/")
                used_pct = 100 * usage.used / usage.total
                if used_pct < retention_pct:
                    break

        await session.commit()

    async def _poller(self) -> None:
        """Loop: poll for new media at poll_interval_sec.

        Repeatedly calls _poller_once(), catching exceptions to keep loop alive.
        """
        while not self._stop_event.is_set():
            try:
                async with self.session_factory() as session:
                    await self._poller_once(session)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                # Log unexpected error but continue looping
                try:
                    async with self.session_factory() as session:
                        await events.add(
                            session,
                            level=EventLevel.ERROR,
                            kind="sync",
                            message=f"Poller loop error: {e}",
                        )
                        await session.commit()
                except Exception:
                    pass

            # Sleep until next poll interval
            try:
                await asyncio.sleep(self.poll_interval_sec)
            except asyncio.CancelledError:
                raise

    async def _maintenance(self) -> None:
        """Loop: run maintenance periodically (hourly).

        Repeatedly calls _maintenance_pass(), catching exceptions to keep loop alive.
        """
        maintenance_interval_sec = 3600  # 1 hour
        while not self._stop_event.is_set():
            try:
                async with self.session_factory() as session:
                    await self._maintenance_pass(session)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                # Log unexpected error but continue looping
                try:
                    async with self.session_factory() as session:
                        await events.add(
                            session,
                            level=EventLevel.ERROR,
                            kind="sync",
                            message=f"Maintenance loop error: {e}",
                        )
                        await session.commit()
                except Exception:
                    pass

            # Sleep until next maintenance cycle
            try:
                await asyncio.sleep(maintenance_interval_sec)
            except asyncio.CancelledError:
                raise

    async def start(self) -> None:
        """Start the sync engine: launch poller, downloader, and maintenance loops.

        Creates three long-running asyncio tasks that run until stop() is called.
        Each loop catches exceptions internally to prevent the task from dying.
        """
        self._stop_event.clear()
        self._tasks = [
            asyncio.create_task(self._poller()),
            asyncio.create_task(self._downloader()),
            asyncio.create_task(self._maintenance()),
        ]

        # Log startup
        try:
            async with self.session_factory() as session:
                await events.add(
                    session,
                    level=EventLevel.SUCCESS,
                    kind="sync",
                    message="Sync engine started",
                )
                await session.commit()
        except Exception:
            pass

    async def stop(self) -> None:
        """Stop the sync engine: cancel all running tasks gracefully.

        Sets the stop event to signal loops to exit, then waits for tasks to finish
        (with timeout), cancelling any that don't finish in time. Cleans up gracefully
        with no orphan tasks or warnings.
        """
        # Signal all loops to stop
        self._stop_event.set()

        # Wait for tasks to finish (with timeout per task)
        timeout_sec = 30
        for task in self._tasks:
            try:
                await asyncio.wait_for(task, timeout=timeout_sec)
            except asyncio.TimeoutError:
                # Task didn't finish in time, cancel it
                task.cancel()
                try:
                    await asyncio.wait_for(task, timeout=5)
                except (asyncio.TimeoutError, asyncio.CancelledError):
                    pass
            except asyncio.CancelledError:
                pass
            except Exception:
                # Ignore other exceptions (task already failed)
                pass

        # Log shutdown
        try:
            async with self.session_factory() as session:
                await events.add(
                    session,
                    level=EventLevel.SUCCESS,
                    kind="sync",
                    message="Sync engine stopped",
                )
                await session.commit()
        except Exception:
            pass
