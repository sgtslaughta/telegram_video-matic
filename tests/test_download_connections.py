"""Connections-per-download is a live setting, and the concurrent-downloads
setting is no longer capped by a fixed startup semaphore."""
import asyncio
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.sync.engine import connections_setting
from app.telegram import fast_telethon
from app.telegram.service import TelegramService


@pytest.mark.parametrize("raw,expected", [(None, 20), ("8", 8), ("0", 1), ("99", 32), ("x", 20)])
def test_connections_setting_clamped(raw, expected):
    assert connections_setting(raw) == expected


@pytest.mark.asyncio
async def test_download_file_passes_connection_count():
    seen = {}

    class FakeT:
        def __init__(self, client, dc_id):
            pass

        async def download(self, location, size, connection_count=None):
            seen["n"] = connection_count
            yield b"x"

    loc = SimpleNamespace(size=1)
    with patch.object(fast_telethon, "ParallelTransferrer", FakeT), \
         patch.object(fast_telethon.utils, "get_input_location", return_value=(2, loc)):
        out = type("O", (), {"write": lambda s, b: None, "tell": lambda s: 1})()
        await fast_telethon.download_file(object(), loc, out, connections=7)
    assert seen["n"] == 7


@pytest.mark.asyncio
async def test_service_has_no_fixed_download_cap(tmp_path):
    """Five downloads at once must all run (the engine pool is the only bound)."""
    svc = TelegramService(account_repo=object(), max_concurrent_downloads=3)
    svc.client = object()
    running, peak = 0, 0

    async def fake_download_file(client, doc, f, progress_callback=None, connections=None):
        nonlocal running, peak
        running += 1
        peak = max(peak, running)
        await asyncio.sleep(0.01)
        running -= 1

    msg = SimpleNamespace(media=SimpleNamespace(document=SimpleNamespace(size=1)))
    with patch("app.telegram.service.download_file", fake_download_file):
        await asyncio.gather(*[svc.download(msg, str(tmp_path / f"{i}.bin")) for i in range(5)])
    assert peak == 5
