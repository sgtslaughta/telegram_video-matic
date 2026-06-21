"""Test suite for subscription filter classifier (Task 3: Filtering)."""
import pytest
from datetime import timedelta
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Optional

from app.sync.engine import classify
from app.db.models import SubMode, FilterMode


# Mock Subscription and MediaDTO for testing
@dataclass
class MockSubscription:
    """Minimal subscription for testing."""
    enabled: bool = True
    mode: str = SubMode.IMMEDIATE
    schedule_days: Optional[list] = None
    filter_regex: Optional[str] = None
    filter_mode: str = FilterMode.INCLUDE
    min_size_mb: Optional[int] = None
    max_size_mb: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


@dataclass
class MockMedia:
    """Minimal media for testing."""
    file_name: Optional[str] = None
    caption: Optional[str] = None
    size_bytes: Optional[int] = None
    date_posted: Optional[datetime] = None


class TestClassifyEnabledGate:
    """Gate 1: Enabled check."""

    def test_classify_disabled_subscription(self):
        """Disabled subscription → skip."""
        sub = MockSubscription(enabled=False)
        media = MockMedia(file_name="test.mkv", size_bytes=100*1024*1024)
        decision, reason = classify(sub, media)
        assert decision == "skip"
        assert reason == "Subscription disabled"

    def test_classify_enabled_subscription(self):
        """Enabled subscription passes enabled gate."""
        sub = MockSubscription(enabled=True, mode=SubMode.IMMEDIATE)
        media = MockMedia(file_name="test.mkv", size_bytes=100*1024*1024)
        decision, reason = classify(sub, media)
        # Should pass enabled gate and reach other gates; all other defaults pass
        assert decision == "keep"
        assert reason is None


class TestClassifyScheduleGate:
    """Gate 2: Schedule gate."""

    def test_classify_schedule_immediate(self):
        """SubMode.immediate always passes schedule gate."""
        sub = MockSubscription(enabled=True, mode=SubMode.IMMEDIATE)
        media = MockMedia(file_name="test.mkv", size_bytes=100*1024*1024)
        decision, reason = classify(sub, media)
        assert decision == "keep"
        assert reason is None

    def test_classify_schedule_scheduled_match(self):
        """Scheduled mode with matching weekday passes."""
        sub = MockSubscription(
            enabled=True,
            mode=SubMode.SCHEDULED,
            schedule_days=["mon", "wed"]
        )
        media = MockMedia(file_name="test.mkv", size_bytes=100*1024*1024)
        # Monday = 0, inject as "mon"
        decision, reason = classify(sub, media, today="mon")
        assert decision == "keep"
        assert reason is None

    def test_classify_schedule_scheduled_no_match(self):
        """Scheduled mode with non-matching weekday skips."""
        sub = MockSubscription(
            enabled=True,
            mode=SubMode.SCHEDULED,
            schedule_days=["mon"]
        )
        media = MockMedia(file_name="test.mkv", size_bytes=100*1024*1024)
        decision, reason = classify(sub, media, today="fri")
        assert decision == "skip"
        assert "Not scheduled for fri" in reason


class TestClassifyRegexGate:
    """Gate 3: Regex filter gate."""

    def test_classify_regex_include_match(self):
        """Include filter matches → keep."""
        sub = MockSubscription(
            enabled=True,
            mode=SubMode.IMMEDIATE,
            filter_regex="anime",
            filter_mode=FilterMode.INCLUDE
        )
        media = MockMedia(file_name="My.Anime.Show.mkv", size_bytes=100*1024*1024)
        decision, reason = classify(sub, media)
        assert decision == "keep"
        assert reason is None

    def test_classify_regex_include_no_match(self):
        """Include filter doesn't match → skip."""
        sub = MockSubscription(
            enabled=True,
            mode=SubMode.IMMEDIATE,
            filter_regex="anime",
            filter_mode=FilterMode.INCLUDE
        )
        media = MockMedia(file_name="Movie.mkv", size_bytes=100*1024*1024)
        decision, reason = classify(sub, media)
        assert decision == "skip"
        assert "Does not match filter" in reason

    def test_classify_regex_exclude_match(self):
        """Exclude filter matches → skip."""
        sub = MockSubscription(
            enabled=True,
            mode=SubMode.IMMEDIATE,
            filter_regex="trailer",
            filter_mode=FilterMode.EXCLUDE
        )
        media = MockMedia(file_name="Movie.trailer.mkv", size_bytes=100*1024*1024)
        decision, reason = classify(sub, media)
        assert decision == "skip"
        assert "Matches exclude filter" in reason

    def test_classify_regex_exclude_no_match(self):
        """Exclude filter doesn't match → keep."""
        sub = MockSubscription(
            enabled=True,
            mode=SubMode.IMMEDIATE,
            filter_regex="trailer",
            filter_mode=FilterMode.EXCLUDE
        )
        media = MockMedia(file_name="Movie.mkv", size_bytes=100*1024*1024)
        decision, reason = classify(sub, media)
        assert decision == "keep"
        assert reason is None

    def test_classify_regex_include_match_caption(self):
        """Include filter matches caption."""
        sub = MockSubscription(
            enabled=True,
            mode=SubMode.IMMEDIATE,
            filter_regex="anime",
            filter_mode=FilterMode.INCLUDE
        )
        media = MockMedia(file_name="show.mkv", caption="New anime episode", size_bytes=100*1024*1024)
        decision, reason = classify(sub, media)
        assert decision == "keep"
        assert reason is None

    def test_classify_regex_case_insensitive(self):
        """Regex matching is case-insensitive."""
        sub = MockSubscription(
            enabled=True,
            mode=SubMode.IMMEDIATE,
            filter_regex="ANIME",
            filter_mode=FilterMode.INCLUDE
        )
        media = MockMedia(file_name="My.anime.Show.mkv", size_bytes=100*1024*1024)
        decision, reason = classify(sub, media)
        assert decision == "keep"
        assert reason is None

    def test_classify_regex_none_filter(self):
        """None filter_regex means no regex gate (passes through)."""
        sub = MockSubscription(
            enabled=True,
            mode=SubMode.IMMEDIATE,
            filter_regex=None,
            filter_mode=FilterMode.INCLUDE
        )
        media = MockMedia(file_name="anything.mkv", size_bytes=100*1024*1024)
        decision, reason = classify(sub, media)
        assert decision == "keep"
        assert reason is None


class TestClassifySizeGate:
    """Gate 4: Size bounds gate."""

    def test_classify_size_within_bounds(self):
        """Size within min/max bounds → keep."""
        sub = MockSubscription(
            enabled=True,
            mode=SubMode.IMMEDIATE,
            min_size_mb=100,
            max_size_mb=500
        )
        media = MockMedia(file_name="test.mkv", size_bytes=200*1024*1024)
        decision, reason = classify(sub, media)
        assert decision == "keep"
        assert reason is None

    def test_classify_size_below_minimum(self):
        """Size below minimum → skip."""
        sub = MockSubscription(
            enabled=True,
            mode=SubMode.IMMEDIATE,
            min_size_mb=500
        )
        media = MockMedia(file_name="test.mkv", size_bytes=100*1024*1024)
        decision, reason = classify(sub, media)
        assert decision == "skip"
        assert "Below minimum size" in reason

    def test_classify_size_exceeds_maximum(self):
        """Size exceeds maximum → skip."""
        sub = MockSubscription(
            enabled=True,
            mode=SubMode.IMMEDIATE,
            max_size_mb=500
        )
        media = MockMedia(file_name="test.mkv", size_bytes=1000*1024*1024)
        decision, reason = classify(sub, media)
        assert decision == "skip"
        assert "Exceeds maximum size" in reason

    def test_classify_size_none_size_bytes(self):
        """None size_bytes passes size gate."""
        sub = MockSubscription(
            enabled=True,
            mode=SubMode.IMMEDIATE,
            min_size_mb=100
        )
        media = MockMedia(file_name="test.mkv", size_bytes=None)
        decision, reason = classify(sub, media)
        assert decision == "keep"
        assert reason is None

    def test_classify_size_none_min_max(self):
        """None min/max size skips size gate."""
        sub = MockSubscription(
            enabled=True,
            mode=SubMode.IMMEDIATE,
            min_size_mb=None,
            max_size_mb=None
        )
        media = MockMedia(file_name="test.mkv", size_bytes=999999999999)
        decision, reason = classify(sub, media)
        assert decision == "keep"
        assert reason is None


class TestClassifyAllGatesPassing:
    """Integration: all gates pass."""

    def test_classify_all_gates_pass(self):
        """All gates pass → keep with no reason."""
        sub = MockSubscription(
            enabled=True,
            mode=SubMode.IMMEDIATE,
            schedule_days=["mon", "wed"],
            filter_regex="anime",
            filter_mode=FilterMode.INCLUDE,
            min_size_mb=100,
            max_size_mb=500
        )
        media = MockMedia(
            file_name="My.Anime.Show.mkv",
            caption="New episode",
            size_bytes=200*1024*1024
        )
        decision, reason = classify(sub, media)
        assert decision == "keep"
        assert reason is None

    def test_classify_gate_order_enabled_first(self):
        """Disabled subscription skips before other gates."""
        sub = MockSubscription(
            enabled=False,
            mode=SubMode.SCHEDULED,
            schedule_days=["invalid"],
            filter_regex="[invalid-regex",
            min_size_mb=99999
        )
        media = MockMedia(file_name="test.mkv", size_bytes=1)
        decision, reason = classify(sub, media)
        assert decision == "skip"
        assert "Subscription disabled" in reason


class TestClassifyEdgeCases:
    """Edge cases and corner scenarios."""

    def test_classify_empty_file_name_and_caption(self):
        """Empty/None file_name and caption."""
        sub = MockSubscription(
            enabled=True,
            mode=SubMode.IMMEDIATE,
            filter_regex="test"
        )
        media = MockMedia(file_name=None, caption=None, size_bytes=100*1024*1024)
        decision, reason = classify(sub, media)
        assert decision == "skip"
        assert "Does not match filter" in reason

    def test_classify_scheduled_with_today_param(self):
        """Inject today parameter for deterministic schedule test."""
        sub = MockSubscription(
            enabled=True,
            mode=SubMode.SCHEDULED,
            schedule_days=["mon", "tue", "wed"]
        )
        media = MockMedia(file_name="test.mkv", size_bytes=100*1024*1024)
        decision, reason = classify(sub, media, today="tue")
        assert decision == "keep"
        assert reason is None

    def test_classify_min_size_at_boundary(self):
        """Size exactly at minimum boundary."""
        sub = MockSubscription(
            enabled=True,
            mode=SubMode.IMMEDIATE,
            min_size_mb=100
        )
        # Exactly 100 MB
        media = MockMedia(file_name="test.mkv", size_bytes=100*1024*1024)
        decision, reason = classify(sub, media)
        assert decision == "keep"
        assert reason is None

    def test_classify_max_size_at_boundary(self):
        """Size exactly at maximum boundary."""
        sub = MockSubscription(
            enabled=True,
            mode=SubMode.IMMEDIATE,
            max_size_mb=500
        )
        # Exactly 500 MB
        media = MockMedia(file_name="test.mkv", size_bytes=500*1024*1024)
        decision, reason = classify(sub, media)
        assert decision == "keep"
        assert reason is None


class TestClassifyTimeframeGate:
    """Gate 5: Timeframe window (date_from/date_to)."""

    def _dt(self, y, m, d):
        return datetime(y, m, d, tzinfo=timezone.utc)

    def test_before_date_from_skipped(self):
        sub = MockSubscription(date_from=self._dt(2026, 6, 1))
        media = MockMedia(size_bytes=10, date_posted=self._dt(2026, 5, 15))
        decision, reason = classify(sub, media)
        assert decision == "skip"
        assert "before" in reason

    def test_after_date_to_skipped(self):
        sub = MockSubscription(date_to=self._dt(2026, 6, 1))
        media = MockMedia(size_bytes=10, date_posted=self._dt(2026, 6, 15))
        decision, reason = classify(sub, media)
        assert decision == "skip"
        assert "after" in reason

    def test_within_window_kept(self):
        sub = MockSubscription(date_from=self._dt(2026, 6, 1), date_to=self._dt(2026, 6, 30))
        media = MockMedia(size_bytes=10, date_posted=self._dt(2026, 6, 15))
        assert classify(sub, media) == ("keep", None)

    def test_no_window_keeps_everything(self):
        sub = MockSubscription()
        media = MockMedia(size_bytes=10, date_posted=self._dt(2020, 1, 1))
        assert classify(sub, media) == ("keep", None)


class TestSubDue:
    """Per-subscription capture frequency gating (_sub_due)."""

    def _sub(self, freq, last_min_ago=None):
        from types import SimpleNamespace
        last = None
        if last_min_ago is not None:
            last = datetime.now(timezone.utc) - timedelta(minutes=last_min_ago)
        return SimpleNamespace(check_frequency=freq, last_checked_at=last, schedule_days=[])

    def test_realtime_never_polled(self):
        from app.sync.engine import _sub_due
        assert _sub_due(self._sub("realtime"), datetime.now(timezone.utc)) is False

    def test_never_checked_is_due(self):
        from app.sync.engine import _sub_due
        assert _sub_due(self._sub("5m"), datetime.now(timezone.utc)) is True

    def test_interval_not_elapsed(self):
        from app.sync.engine import _sub_due
        assert _sub_due(self._sub("hourly", last_min_ago=10), datetime.now(timezone.utc)) is False

    def test_interval_elapsed(self):
        from app.sync.engine import _sub_due
        assert _sub_due(self._sub("5m", last_min_ago=10), datetime.now(timezone.utc)) is True


def test_classify_timeframe_mixed_tz():
    """date_posted aware + sub date naive (SQLite) must not crash."""
    from app.sync.engine import classify
    from datetime import datetime as _dt, timezone as _tz
    sub = MockSubscription(date_from=_dt(2026, 6, 1))  # naive
    media = MockMedia(size_bytes=10, date_posted=_dt(2026, 5, 1, tzinfo=_tz.utc))  # aware
    assert classify(sub, media) == ("skip", "Posted before 2026-06-01")
