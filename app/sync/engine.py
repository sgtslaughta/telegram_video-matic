"""Sync engine components: filter classifier, poller, downloader, maintenance."""
import re
import os
import asyncio
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Tuple, Callable, Any
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from telethon.errors import FloodWaitError

from app.db.models import SubMode, FilterMode, MediaStatus, EventLevel, JobStatus, Channel, Topic
from app.db.repositories import subscriptions, media, events, downloads
from app.telegram.dtos import ChannelDTO, TopicDTO
from app.sync.naming import choose_target_path
from app.hashing import quick_hash


def _as_utc(dt):
    """SQLite returns naive datetimes; treat them as UTC for arithmetic."""
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


_FREQUENCY_SECONDS = {
    "1m": 60, "5m": 300, "15m": 900, "30m": 1800,
    "hourly": 3600, "daily": 86400,
}


def _sub_due(sub, now) -> bool:
    """Whether a subscription should be polled this tick, per check_frequency.
    realtime is event-driven (never polled here)."""
    freq = sub.check_frequency or "5m"
    if freq == "realtime":
        return False
    last = _as_utc(sub.last_checked_at)
    if last is None:
        return True
    elapsed = (now - last).total_seconds()
    if freq == "scheduled":
        # Captured by classify's weekday gate; just poll roughly hourly.
        return elapsed >= 3600
    return elapsed >= _FREQUENCY_SECONDS.get(freq, 300)


class _DownloadCanceled(Exception):
    """Raised mid-download when a cancel was requested (discard partial)."""


class _DownloadPaused(Exception):
    """Raised mid-download when a pause was requested (keep partial)."""


def _write_jellyfin_nfo(target_full, item, show_title, season, episode) -> None:
    """Write a Kodi/Jellyfin .nfo next to the video. episodedetails when a
    season/episode was detected (+ tvshow.nfo at the series root), else movie."""
    from xml.sax.saxutils import escape
    title = escape(str(item.caption or item.file_name or target_full.stem or ""))
    plot = escape(str(item.caption or ""))
    aired = item.date_posted.date().isoformat() if item.date_posted else ""
    runtime = int((item.duration_sec or 0) / 60)
    nfo = target_full.with_suffix(".nfo")

    if season is not None and episode is not None:
        nfo.write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            f"<episodedetails>\n  <title>{title}</title>\n"
            f"  <season>{escape(str(season))}</season>\n"
            f"  <episode>{escape(str(episode))}</episode>\n"
            f"  <plot>{plot}</plot>\n  <aired>{aired}</aired>\n"
            f"  <runtime>{runtime}</runtime>\n</episodedetails>\n",
            encoding="utf-8",
        )
        # tvshow.nfo at the series root (grandparent = show folder above Season X)
        series_root = target_full.parent.parent
        tv = series_root / "tvshow.nfo"
        if series_root.exists() and not tv.exists():
            tv.write_text(
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                f"<tvshow>\n  <title>{escape(str(show_title))}</title>\n</tvshow>\n",
                encoding="utf-8",
            )
    else:
        nfo.write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            f"<movie>\n  <title>{title}</title>\n  <plot>{plot}</plot>\n"
            f"  <premiered>{aired}</premiered>\n  <runtime>{runtime}</runtime>\n</movie>\n",
            encoding="utf-8",
        )


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

    # Gate 5: Timeframe window (skip media outside [date_from, date_to]).
    # Coerce all to UTC-aware — date_posted is aware (Telethon) but the sub's
    # dates come back naive from SQLite, so a raw compare would crash.
    posted = _as_utc(getattr(media, "date_posted", None))
    if posted is not None:
        date_from = _as_utc(getattr(subscription, "date_from", None))
        date_to = _as_utc(getattr(subscription, "date_to", None))
        if date_from is not None and posted < date_from:
            return ("skip", f"Posted before {date_from.date()}")
        if date_to is not None and posted > date_to:
            return ("skip", f"Posted after {date_to.date()}")

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
        maintenance_interval_sec: int = 3600,
        download_root: str = "/downloads",
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
        self.maintenance_interval_sec = maintenance_interval_sec
        self.download_root = download_root
        self._tasks = []
        self._stop_event = asyncio.Event()
        # media_id -> "cancel" | "pause"; checked cooperatively during download.
        self._control: dict[int, str] = {}

    def request_cancel(self, media_id: int) -> None:
        """Signal an in-flight download to abort and discard its partial."""
        self._control[media_id] = "cancel"

    def request_pause(self, media_id: int) -> None:
        """Signal an in-flight download to stop but keep its partial for resume."""
        self._control[media_id] = "pause"

    async def _poll_one_sub(self, session: AsyncSession, sub) -> None:
        """Fetch + classify new media for a single subscription.

        Per-item filter skips are NOT logged as events (routine + floods the
        feed); the SKIPPED status is visible in Browse. One summary is logged
        per poll when anything was queued or skipped."""
        last_msg_id = await media.get_max_tg_msg_id(session, sub.channel_id, sub.topic_id)
        chan_dto, topic_dto = await self._sub_dtos(session, sub)
        queued = skipped = 0
        async for media_dto in self.tg_service.iter_media(chan_dto, topic_dto, since_msg_id=last_msg_id):
            item = await media.upsert_from_tg_dto(session, media_dto, sub.id, sub.channel_id, sub.topic_id)
            status, _reason = classify(sub, item)
            if status == "skip":
                await media.set_status(session, item.id, MediaStatus.SKIPPED)
                skipped += 1
            else:
                await media.set_status(session, item.id, MediaStatus.PENDING)
                queued += 1
            try:
                await self.plugin_host.dispatch("on_media_discovered", item)
            except Exception as e:
                await events.add(session, level=EventLevel.WARNING, kind="plugin",
                                 message=f"Plugin error on_media_discovered: {e}")
        if queued:
            label = sub.name or (chan_dto.title if chan_dto else f"sub {sub.id}")
            await events.add(session, level=EventLevel.INFO, kind="sync",
                             subscription_id=sub.id,
                             message=f"{label}: queued {queued} new"
                                     + (f", skipped {skipped} (filtered)" if skipped else ""))
        await session.commit()

    async def _poller_once(self, session: AsyncSession) -> None:
        """One poller tick: poll each due subscription per its check_frequency.

        realtime subs are skipped here (handled by live events). Each sub is
        polled only when its interval has elapsed since last_checked_at.
        """
        try:
            subs = await subscriptions.list(session, enabled_only=True)
            now = datetime.now(timezone.utc)
            for sub in subs:
                if not _sub_due(sub, now):
                    continue
                try:
                    await self._poll_one_sub(session, sub)
                    sub.last_checked_at = now
                    await session.commit()
                except Exception as e:
                    await events.add(session, level=EventLevel.ERROR, kind="sync",
                                     subscription_id=sub.id, message=f"Sync error: {e}")
                    await session.commit()
        except Exception as e:
            await events.add(session, level=EventLevel.ERROR, kind="sync",
                             message=f"Poller error: {e}")
            await session.commit()

    async def _on_new_message(self, event) -> None:
        """Live-event handler: a new message arrived. Poll any realtime subs on
        that channel immediately so the media is queued within ~a second."""
        try:
            chat_id = getattr(event, "chat_id", None)
            if chat_id is None:
                return
            async with self.session_factory() as session:
                subs = await subscriptions.list(session, enabled_only=True)
                for sub in subs:
                    if (sub.check_frequency or "5m") != "realtime":
                        continue
                    chan = await session.get(Channel, sub.channel_id)
                    if not chan or chan.tg_id != chat_id:
                        continue
                    try:
                        await self._poll_one_sub(session, sub)
                    except Exception as e:
                        await events.add(session, level=EventLevel.ERROR, kind="realtime",
                                         subscription_id=sub.id, message=f"Realtime error: {e}")
                        await session.commit()
        except Exception:
            pass  # never let a bad event kill the update loop

    async def _downloader(self) -> None:
        """Concurrent download manager: keeps up to N downloads running at once
        (N = max_concurrent_downloads setting). Each claimed item runs in its own
        task with its own DB session, so 3 files genuinely download in parallel."""
        from app.db.repositories import settings as settings_repo
        active: dict[int, asyncio.Task] = {}
        self._dl_active = active
        try:
            while not self._stop_event.is_set():
                try:
                    try:
                        async with self.session_factory() as s:
                            raw = await settings_repo.get(s, "max_concurrent_downloads", default="3")
                        max_concurrent = int(raw) if raw else 3
                    except Exception:
                        max_concurrent = 3

                    # Reap finished tasks
                    for iid in [i for i, t in active.items() if t.done()]:
                        active.pop(iid, None)

                    slots = max_concurrent - len(active)
                    if slots > 0:
                        async with self.session_factory() as session:
                            claimed = await media.claim_pending(session, limit=slots)
                        for item in claimed:
                            active[item.id] = asyncio.create_task(self._download_item(item.id))
                except Exception as e:
                    try:
                        async with self.session_factory() as session:
                            await events.add(session, level=EventLevel.ERROR, kind="sync",
                                             message=f"Downloader error: {e}")
                            await session.commit()
                    except Exception:
                        pass

                # Re-check often so freed slots refill quickly.
                try:
                    await asyncio.wait_for(self._stop_event.wait(), timeout=1)
                    break
                except asyncio.TimeoutError:
                    pass
        finally:
            # Shutdown/cancel: stop in-flight downloads (partials kept, resumed next start)
            for t in active.values():
                t.cancel()

    async def _download_item(self, item_id: int) -> None:
        """Download one media item (own session). Spawned concurrently by the
        downloader pool; bounded by max_concurrent_downloads."""
        max_attempts = 5
        base_backoff = 5
        max_backoff = 3600
        async with self.session_factory() as session:
            item = await media.get(session, item_id)
            if not item:
                return

            # Backoff elapsed-time gate for retried items
            latest_job = await downloads.get_latest_for_media(session, item.id)
            if latest_job and latest_job.attempt > 1 and latest_job.status == JobStatus.QUEUED:
                backoff_sec = min(2 ** latest_job.attempt * base_backoff, max_backoff)
                elapsed = (datetime.now(timezone.utc) - _as_utc(latest_job.updated_at)).total_seconds()
                if elapsed < backoff_sec:
                    await media.set_status(session, item.id, MediaStatus.PENDING)
                    await session.commit()
                    return

            if True:
                if True:
                        try:
                            # Subscription is optional (ad-hoc downloads have none).
                            sub = await subscriptions.get(session, item.subscription_id) if item.subscription_id else None
                            channel = await session.get(Channel, item.channel_id)
                            if not channel:
                                await media.set_status(session, item.id, MediaStatus.FAILED)
                                await events.add(
                                    session,
                                    level=EventLevel.ERROR,
                                    kind="download",
                                    media_id=item.id,
                                    message="Channel not found",
                                )
                                await session.commit()
                                return

                            # Reuse a paused/queued job (resume) or start fresh.
                            job = await downloads.get_or_start(session, item.id)
                            await downloads.running(session, job.id, item.size_bytes)

                            # Stable partial path so a paused download can resume
                            # from its byte offset instead of restarting.
                            partial_dir = Path(self.download_root) / ".partial"
                            partial_dir.mkdir(parents=True, exist_ok=True)
                            temp_file = str(partial_dir / f"{item.id}.part")
                            resume_offset = os.path.getsize(temp_file) if os.path.exists(temp_file) else 0

                            try:  # Download attempt
                                # Throttle broadcast to ~1 Hz; track last sample for speed/ETA.
                                last_broadcast_time = [None]
                                last_db_time = [None]  # DB-persist throttle (slower than broadcast)
                                last_bytes = [0]
                                ema_speed = [None]  # smoothed bytes/sec

                                async def on_progress(current_bytes, total_bytes):
                                    """Progress callback: cancel/pause check + ~1 Hz throttle + speed/ETA."""
                                    action = self._control.get(item.id)
                                    if action == "cancel":
                                        raise _DownloadCanceled()
                                    if action == "pause":
                                        raise _DownloadPaused()
                                    now = datetime.now(timezone.utc)
                                    prev = last_broadcast_time[0]
                                    if prev is None or (now - prev).total_seconds() >= 1.0:
                                        speed_bps = None
                                        eta_sec = None
                                        if prev is not None:
                                            dt = (now - prev).total_seconds()
                                            delta = current_bytes - last_bytes[0]
                                            if dt > 0 and delta >= 0:
                                                inst = delta / dt
                                                # EMA smooths the bursty parallel transfer so the
                                                # displayed rate doesn't spike/drop each second.
                                                ema_speed[0] = inst if ema_speed[0] is None else (
                                                    0.4 * inst + 0.6 * ema_speed[0]
                                                )
                                                speed_bps = int(ema_speed[0])
                                                if speed_bps > 0 and total_bytes:
                                                    eta_sec = int((total_bytes - current_bytes) / speed_bps)
                                        last_broadcast_time[0] = now
                                        last_bytes[0] = current_bytes
                                        # Persist to the DB at most every ~5s to ease SQLite
                                        # write pressure under concurrent downloads; the WS
                                        # broadcast below still fires every ~1s for the live UI.
                                        if (last_db_time[0] is None
                                                or (now - last_db_time[0]).total_seconds() >= 5.0):
                                            last_db_time[0] = now
                                            await downloads.update_progress(
                                                session, job.id, current_bytes,
                                                eta_sec=eta_sec, speed_bps=speed_bps,
                                            )
                                        await self.broadcast({
                                            "kind": "download_progress",
                                            "job_id": job.id,
                                            "media_id": item.id,
                                            "status": "running",
                                            "progress": current_bytes / total_bytes if total_bytes else 0,
                                            "bytes_done": current_bytes,
                                            "bytes_total": total_bytes,
                                            "speed_bps": speed_bps,
                                            "eta_sec": eta_sec,
                                        })

                                # Download from Telegram (resolve message by channel+id)
                                await self.tg_service.download_by_id(
                                    channel.tg_id,
                                    item.tg_msg_id,
                                    temp_file,
                                    on_progress=on_progress,
                                    offset=resume_offset,
                                )

                                # Quick content hash -> dedup: if an identical file
                                # is already on disk (renamed, or grabbed by another
                                # sub), relink instead of storing a second copy.
                                file_hash = await asyncio.to_thread(quick_hash, temp_file)
                                dup = (await media.find_downloaded_by_hash(session, file_hash, exclude_id=item.id)
                                       if file_hash else None)
                                if dup and dup.local_path and Path(dup.local_path).exists():
                                    Path(temp_file).unlink(missing_ok=True)
                                    item.local_path = dup.local_path
                                    item.content_hash = file_hash
                                    item.downloaded_at = datetime.now(timezone.utc)
                                    await media.set_status(session, item.id, MediaStatus.DOWNLOADED)
                                    self._control.pop(item.id, None)
                                    await downloads.finish(session, job.id, error=None)
                                    await events.add(session, level=EventLevel.INFO, kind="download",
                                                     media_id=item.id,
                                                     message=f"Deduplicated → existing file {dup.local_path}")
                                    await session.commit()
                                    return

                                # Naming: plugins may contribute tokens (e.g. rugby
                                # league/season/teams) that trigger the template even
                                # without an S##E## marker. choose_target_path merges
                                # them and decides template-vs-original.
                                extra = (await self.plugin_host.collect_naming_tokens(item, sub)
                                         if (self.plugin_host and sub) else {})
                                target_path, season, episode, use_template = choose_target_path(
                                    item, sub, extra)

                                storage_base = sub.storage_path if sub else self.download_root
                                target_full = Path(storage_base) / target_path

                                # Move file into place. Offloaded to a thread: a
                                # cross-filesystem move becomes a full copy, which would
                                # otherwise block the shared event loop (and the API).
                                target_full.parent.mkdir(parents=True, exist_ok=True)
                                await asyncio.to_thread(shutil.move, temp_file, str(target_full))

                                # Jellyfin/Kodi .nfo sidecar (opt-in per sub)
                                if sub and sub.jellyfin_metadata:
                                    try:
                                        show_title = sub.name or (channel.title if channel else "")
                                        _write_jellyfin_nfo(
                                            target_full, item, show_title,
                                            season if use_template else None,
                                            episode if use_template else None,
                                        )
                                    except Exception as e:
                                        await events.add(session, level=EventLevel.WARNING,
                                                         kind="jellyfin", media_id=item.id,
                                                         message=f"NFO write failed: {e}")

                                # Update DB: mark as downloaded
                                item.local_path = str(target_full)
                                item.content_hash = file_hash
                                item.downloaded_at = datetime.now(timezone.utc)
                                await media.set_status(session, item.id, MediaStatus.DOWNLOADED)

                                # Finish job
                                self._control.pop(item.id, None)
                                await downloads.finish(session, job.id, error=None)
                                await events.add(
                                    session, level=EventLevel.SUCCESS, kind="download",
                                    subscription_id=item.subscription_id, media_id=item.id,
                                    message=f"Downloaded {item.file_name or target_full.name}",
                                )

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

                            except _DownloadCanceled:
                                # Discard the partial; mark canceled, no retry.
                                self._control.pop(item.id, None)
                                Path(temp_file).unlink(missing_ok=True)
                                await downloads.set_status(session, job.id, JobStatus.CANCELED)
                                await media.set_status(session, item.id, MediaStatus.SKIPPED)
                                await session.commit()

                            except _DownloadPaused:
                                # Keep the partial so resume continues from offset.
                                self._control.pop(item.id, None)
                                await downloads.set_status(session, job.id, JobStatus.PAUSED)
                                await media.set_status(session, item.id, MediaStatus.PAUSED)
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

    def _relink_by_hash(self, item) -> str | None:
        """Find item's file under a new name (renamed/moved) by content hash.
        Searches the file's directory tree, size-filtered. None if not found.
        ponytail: synchronous rglob; fine for hourly maintenance, one dir."""
        if not item.content_hash or not item.local_path or not item.size_bytes:
            return None
        base = Path(item.local_path).parent
        if not base.exists():
            base = Path(self.download_root)
            if not base.exists():
                return None
        for f in base.rglob("*"):
            try:
                if not f.is_file() or f.stat().st_size != item.size_bytes:
                    continue
            except OSError:
                continue
            if quick_hash(f) == item.content_hash:
                return str(f)
        return None

    async def _maintenance_pass(self, session) -> None:
        """Single pass of maintenance: drift detection and pruning.

        - Missing-file drift: DOWNLOADED items with missing local_path → PENDING + event
        - Gap drift: full iter_media reconcile finds missing media → insert + classify → PENDING/SKIPPED
        - Age pruning: DOWNLOADED items older than retention_days → delete file, status=SKIPPED
        - Disk% pruning: when disk usage >= retention_disk_pct, delete oldest DOWNLOADED files
        - Orphan tolerance: files on disk not in DB are never touched (no directory scan)
        """
        # 1. Missing-file drift: DOWNLOADED items with missing local_path.
        # Before re-downloading, try to find the file under a new name (renamed/
        # moved) by content hash and relink — avoids re-fetching.
        downloaded = await media.list_by_status(session, MediaStatus.DOWNLOADED)
        for item in downloaded:
            if item.local_path and not Path(item.local_path).exists():
                relinked = self._relink_by_hash(item)
                if relinked:
                    item.local_path = relinked
                    await events.add(
                        session, level=EventLevel.INFO, kind="drift", media_id=item.id,
                        message=f"Renamed file relinked: {relinked}",
                    )
                    continue
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
                chan_dto, topic_dto = await self._sub_dtos(session, sub)
                async for media_dto in self.tg_service.iter_media(
                    chan_dto, topic_dto, since_msg_id=None
                ):
                    # Check if already stored
                    existing = await media.get_by_tg_msg_id(
                        session, sub.channel_id, media_dto.tg_msg_id
                    )
                    if not existing:
                        # New gap item: use the DB FK ids from the subscription,
                        # NOT the Telegram topic id on the DTO (FK -> topics.id).
                        item = await media.upsert_from_tg(
                            session,
                            channel_id=sub.channel_id,
                            topic_id=sub.topic_id,
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
                        status, _reason = classify(sub, item)

                        if status == "skip":
                            # Routine filter skip — no per-item event (floods feed).
                            await media.set_status(session, item.id, MediaStatus.SKIPPED)
                        else:
                            await media.set_status(session, item.id, MediaStatus.PENDING)
                            gap_count += 1  # count only items actually queued

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

        # Emit summary event only if NEW items were actually queued
        if gap_count > 0:
            await events.add(
                session,
                level=EventLevel.INFO,
                kind="drift",
                message=f"Gap reconcile: queued {gap_count} new media item(s)",
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

        # 5. Per-subscription pruning: optional retention_days + disk quota.
        for sub in await subscriptions.list(session):
            items = await media.list_downloaded_for_sub(session, sub.id)  # oldest first
            if not items:
                continue

            def _prune(item, reason):
                if item.local_path and Path(item.local_path).exists():
                    Path(item.local_path).unlink()

            # 5a. Per-sub age retention (if enabled for this sub)
            if sub.retention_days:
                sub_cutoff = datetime.now(timezone.utc) - timedelta(days=sub.retention_days)
                for item in list(items):
                    if item.downloaded_at and _as_utc(item.downloaded_at) < sub_cutoff:
                        _prune(item, "age")
                        await media.set_local_path(session, item.id, None)
                        await media.set_status(session, item.id, MediaStatus.SKIPPED)
                        await events.add(session, level=EventLevel.INFO, kind="prune",
                                         media_id=item.id, subscription_id=sub.id,
                                         message=f"Pruned (sub age > {sub.retention_days}d)")
                        items.remove(item)

            # 5b. Per-sub disk quota: delete oldest until under max_total_gb
            if sub.max_total_gb:
                quota = sub.max_total_gb * 1024 ** 3
                total = sum((i.size_bytes or 0) for i in items)
                for item in list(items):
                    if total <= quota:
                        break
                    _prune(item, "quota")
                    await media.set_local_path(session, item.id, None)
                    await media.set_status(session, item.id, MediaStatus.SKIPPED)
                    await events.add(session, level=EventLevel.INFO, kind="prune",
                                     media_id=item.id, subscription_id=sub.id,
                                     message=f"Pruned (quota > {sub.max_total_gb}GB)")
                    total -= (item.size_bytes or 0)

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

            # Tick at a fast base cadence; per-sub check_frequency gates actual
            # polling. min(poll_interval_sec, 30) keeps 1-minute subs responsive.
            try:
                tick = min(self.poll_interval_sec, 30)
                await asyncio.wait_for(self._stop_event.wait(), timeout=tick)
                break  # stop event set -> exit loop promptly
            except asyncio.TimeoutError:
                pass  # interval elapsed normally -> next iteration
            except asyncio.CancelledError:
                raise

    async def _maintenance(self) -> None:
        """Loop: run maintenance periodically (hourly).

        Repeatedly calls _maintenance_pass(), catching exceptions to keep loop alive.
        """
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

            # Wait for the interval OR an early stop signal, whichever first.
            try:
                await asyncio.wait_for(
                    self._stop_event.wait(), timeout=self.maintenance_interval_sec
                )
                break  # stop event set -> exit loop promptly
            except asyncio.TimeoutError:
                pass  # interval elapsed normally -> next iteration
            except asyncio.CancelledError:
                raise

    async def start(self) -> None:
        """Start the sync engine: launch poller, downloader, and maintenance loops.

        Creates three long-running asyncio tasks that run until stop() is called.
        Each loop catches exceptions internally to prevent the task from dying.
        """
        self._stop_event.clear()

        # Requeue downloads interrupted by a previous shutdown/crash: items left
        # at queued/downloading never resume (the downloader only claims pending).
        try:
            from sqlalchemy import update
            from app.db.models import MediaItem, DownloadJob, JobStatus
            async with self.session_factory() as session:
                await session.execute(
                    update(MediaItem)
                    .where(MediaItem.status.in_([MediaStatus.QUEUED, MediaStatus.DOWNLOADING]))
                    .values(status=MediaStatus.PENDING)
                )
                # Orphaned jobs from a prior run aren't actually downloading: cancel
                # them so they vanish from the active list (media is requeued above).
                await session.execute(
                    update(DownloadJob)
                    .where(DownloadJob.status.in_([JobStatus.QUEUED, JobStatus.RUNNING]))
                    .values(status=JobStatus.CANCELED)
                )
                await session.commit()
        except Exception:
            pass

        self._tasks = [
            asyncio.create_task(self._poller()),
            asyncio.create_task(self._downloader()),
            asyncio.create_task(self._maintenance()),
        ]

        # Register the live-events handler for realtime subscriptions.
        try:
            if hasattr(self.tg_service, "register_new_message_handler"):
                self.tg_service.register_new_message_handler(self._on_new_message)
        except Exception as e:
            print(f"[engine] realtime handler registration failed: {e!r}")

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

    async def _sub_dtos(self, session, sub) -> Tuple[ChannelDTO, Optional[TopicDTO]]:
        """Build Channel/Topic DTOs (with Telegram ids) from a subscription's DB rows.

        iter_media needs tg ids, not the DB FK ids stored on the subscription.
        """
        ch = await session.get(Channel, sub.channel_id)
        chan_dto = ChannelDTO(
            tg_id=ch.tg_id, title=ch.title, username=ch.username,
            is_forum=ch.is_forum, photo_b64=ch.photo_b64, raw={},
        )
        topic_dto = None
        if sub.topic_id:
            tp = await session.get(Topic, sub.topic_id)
            if tp:
                topic_dto = TopicDTO(
                    tg_topic_id=tp.tg_topic_id, title=tp.title,
                    channel_tg_id=ch.tg_id, raw={},
                )
        return chan_dto, topic_dto

    async def scan_subscription(self, sub_id: int) -> None:
        """Scan a single subscription: one pass of per-subscription poller logic.

        Fetches new media from Telegram for this subscription, classifies (keep/skip),
        and updates DB. Reuses _poller_once logic.

        Args:
            sub_id: Subscription ID to scan

        Raises:
            RuntimeError: If subscription not found or TG service not ready
        """
        try:
            async with self.session_factory() as session:
                sub = await subscriptions.get(session, sub_id)
                if not sub:
                    raise RuntimeError(f"Subscription {sub_id} not found")

                if not self.tg_service:
                    raise RuntimeError("Telegram service not available")

                # Get max stored tg_msg_id for incremental fetch
                last_msg_id = await media.get_max_tg_msg_id(
                    session, sub.channel_id, sub.topic_id
                )

                # Fetch new media from TelegramService
                chan_dto, topic_dto = await self._sub_dtos(session, sub)
                async for media_dto in self.tg_service.iter_media(
                    chan_dto, topic_dto, since_msg_id=last_msg_id
                ):
                    # Upsert into DB
                    item = await media.upsert_from_tg_dto(session, media_dto, sub.id, sub.channel_id, sub.topic_id)

                    # Classify: keep or skip (skips are silent — see _poll_one_sub)
                    status, _reason = classify(sub, item)

                    if status == "skip":
                        await media.set_status(session, item.id, MediaStatus.SKIPPED)
                    else:
                        await media.set_status(session, item.id, MediaStatus.PENDING)

                    # Dispatch to plugins (wrapped to prevent bad plugins crashing)
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
            async with self.session_factory() as session:
                await events.add(
                    session,
                    level=EventLevel.ERROR,
                    kind="sync",
                    subscription_id=sub_id,
                    message=f"Scan subscription error: {e}",
                )
                await session.commit()
            raise

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
