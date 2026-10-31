"""1.6.0 notifier: trigger classification + spam control."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from app.notify.notifier import Notifier, Target, classify_event

T0 = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)


class Clock:
    def __init__(self):
        self.now = T0

    def __call__(self):
        return self.now

    def advance(self, **kw):
        self.now += timedelta(**kw)


def _ev(level, kind, message, media_id=None):
    return SimpleNamespace(level=level, kind=kind, message=message, media_id=media_id, subscription_id=None)


def _notifier(triggers=("download_complete", "download_failed", "telegram", "unmatched", "disk_low"), **kw):
    sent = []
    clock = Clock()

    async def send(url, title, body, attach=None):
        sent.append((url, title, body))
        return True

    n = Notifier(session_factory=None, send=send, clock=clock, **kw)
    n.targets = [Target(id="t1", name="Phone", url="pover://x", triggers=list(triggers))]
    return n, sent, clock


def test_classify():
    assert classify_event(_ev("success", "download", "Downloaded a.mkv")) == "download_complete"
    assert classify_event(_ev("error", "download", "Download failed after 3 attempts: x")) == "download_failed"
    assert classify_event(_ev("error", "download", "Download error: transient")) is None
    assert classify_event(_ev("info", "rugby", "No fixture match for “x”")) == "unmatched"
    assert classify_event(_ev("info", "rugby", "Needs review — A vs B (60%)")) == "unmatched"
    assert classify_event(_ev("success", "rugby", "Matched A vs B (100%)")) is None
    assert classify_event(_ev("info", "sync", "queued 3")) is None


@pytest.mark.asyncio
async def test_arrivals_batch_into_one_message():
    n, sent, clock = _notifier()
    for i in range(3):
        n.on_event(_ev("success", "download", f"Downloaded m{i}.mkv"))
    await n.tick(connected=True, disk_pct=10)
    assert sent == []  # window still open
    clock.advance(seconds=121)
    await n.tick(connected=True, disk_pct=10)
    assert len(sent) == 1
    assert "3" in sent[0][1] and "m2.mkv" in sent[0][2]


@pytest.mark.asyncio
async def test_target_only_gets_subscribed_triggers():
    n, sent, clock = _notifier(triggers=("download_failed",))
    n.on_event(_ev("success", "download", "Downloaded a.mkv"))
    clock.advance(seconds=121)
    await n.tick(connected=True, disk_pct=10)
    assert sent == []


@pytest.mark.asyncio
async def test_telegram_down_after_5_minutes_then_recovered():
    n, sent, clock = _notifier()
    await n.tick(connected=False, disk_pct=10)
    clock.advance(minutes=4)
    await n.tick(connected=False, disk_pct=10)
    assert sent == []  # blip tolerance
    clock.advance(minutes=2)
    await n.tick(connected=False, disk_pct=10)
    assert len(sent) == 1 and "disconnected" in sent[0][1].lower()
    clock.advance(minutes=1)
    await n.tick(connected=False, disk_pct=10)
    assert len(sent) == 1  # no repeat
    await n.tick(connected=True, disk_pct=10)
    assert len(sent) == 2 and "reconnected" in sent[1][1].lower()


@pytest.mark.asyncio
async def test_short_blip_sends_nothing():
    n, sent, clock = _notifier()
    await n.tick(connected=False, disk_pct=10)
    clock.advance(minutes=2)
    await n.tick(connected=True, disk_pct=10)
    assert sent == []


@pytest.mark.asyncio
async def test_reminders_at_1h_6h_24h():
    n, sent, clock = _notifier()
    await n.tick(connected=False, disk_pct=10)
    clock.advance(minutes=5)
    await n.tick(connected=False, disk_pct=10)
    counts = []
    for _ in range(26 * 12):  # 26h in 5-min ticks
        clock.advance(minutes=5)
        await n.tick(connected=False, disk_pct=10)
        counts.append(len(sent))
    assert len(sent) == 4  # first + 1h + 6h + 24h


@pytest.mark.asyncio
async def test_disk_low_alerts_once_and_clears():
    n, sent, clock = _notifier(disk_low_pct=90)
    await n.tick(connected=True, disk_pct=95)
    await n.tick(connected=True, disk_pct=95)
    assert len(sent) == 1 and "disk" in sent[0][1].lower()
    await n.tick(connected=True, disk_pct=50)
    await n.tick(connected=True, disk_pct=95)
    assert len(sent) == 2


@pytest.mark.asyncio
async def test_hourly_cap_folds_overflow():
    n, sent, clock = _notifier()
    for i in range(12):
        n.on_event(_ev("error", "download", f"Download failed after 3 attempts: {i}"))
        clock.advance(seconds=121)
        await n.tick(connected=True, disk_pct=10)
    assert len(sent) == 10
    clock.advance(hours=1)
    n.on_event(_ev("error", "download", "Download failed after 3 attempts: late"))
    clock.advance(seconds=121)
    await n.tick(connected=True, disk_pct=10)
    assert len(sent) == 11 and "+2 more" in sent[-1][2]


@pytest.mark.asyncio
async def test_quiet_hours_hold_arrivals_but_not_errors():
    n, sent, clock = _notifier(quiet=(23, 7), tz=timezone.utc)
    clock.now = T0.replace(hour=23, minute=30)
    n.on_event(_ev("success", "download", "Downloaded late.mkv"))
    clock.advance(seconds=121)
    await n.tick(connected=True, disk_pct=10)
    assert sent == []
    await n.tick(connected=True, disk_pct=99)  # error-class passes
    assert len(sent) == 1
    clock.now = T0.replace(hour=7, minute=1) + timedelta(days=1)
    await n.tick(connected=True, disk_pct=99)
    assert any("late.mkv" in b for _, _, b in sent)
