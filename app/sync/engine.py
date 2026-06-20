"""Sync engine components: filter classifier, poller, downloader, maintenance."""
import re
from datetime import datetime
from typing import Optional, Tuple

from app.db.models import SubMode, FilterMode


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
