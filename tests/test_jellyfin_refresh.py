"""1.6.0: Jellyfin refresh is debounced so a burst of imports = one refresh."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from app.notify.jellyfin import JellyfinRefresher


@pytest.mark.asyncio
async def test_burst_of_downloads_triggers_one_refresh():
    calls = []
    now = [datetime(2026, 11, 1, tzinfo=timezone.utc)]

    async def post(url, headers):
        calls.append((url, headers))

    j = JellyfinRefresher(post=post, clock=lambda: now[0])
    j.url, j.api_key, j.library_id = "http://jf:8096", "k", ""
    for _ in range(8):
        j.on_event(SimpleNamespace(level="success", kind="download", message="Downloaded x"))
    j.on_event(SimpleNamespace(level="info", kind="prune", message="Pruned (age > 90 days)"))
    await j.tick()
    assert calls == []  # quiet period not elapsed
    now[0] += timedelta(seconds=61)
    await j.tick()
    await j.tick()
    assert calls == [("http://jf:8096/Library/Refresh", {"X-Emby-Token": "k"})]


@pytest.mark.asyncio
async def test_library_scoped_refresh_and_disabled_when_unset():
    calls = []
    now = [datetime(2026, 11, 1, tzinfo=timezone.utc)]

    async def post(url, headers):
        calls.append(url)

    j = JellyfinRefresher(post=post, clock=lambda: now[0])
    j.on_event(SimpleNamespace(level="success", kind="download", message="Downloaded x"))
    now[0] += timedelta(seconds=61)
    await j.tick()
    assert calls == []  # not configured
    j.url, j.api_key, j.library_id = "http://jf:8096/", "k", "abc"
    j.on_event(SimpleNamespace(level="success", kind="download", message="Downloaded x"))
    now[0] += timedelta(seconds=61)
    await j.tick()
    assert calls == ["http://jf:8096/Items/abc/Refresh?Recursive=true"]
