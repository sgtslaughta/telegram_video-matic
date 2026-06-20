"""Sync engine components: filter classifier, poller, downloader, maintenance."""
import re
import asyncio
from datetime import datetime
from typing import Optional, Tuple, Callable, Any
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, async_sessionmaker

from app.db.models import SubMode, FilterMode, MediaStatus, EventLevel
from app.db.repositories import subscriptions, media, events


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
