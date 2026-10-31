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

        async def download(self, location, size, connection_count=None, start=0):
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

    async def fake_download_file(client, doc, f, progress_callback=None, connections=None, offset=0):
        nonlocal running, peak
        running += 1
        peak = max(peak, running)
        await asyncio.sleep(0.01)
        running -= 1

    msg = SimpleNamespace(media=SimpleNamespace(document=SimpleNamespace(size=1)))
    with patch("app.telegram.service.download_file", fake_download_file):
        await asyncio.gather(*[svc.download(msg, str(tmp_path / f"{i}.bin")) for i in range(5)])
    assert peak == 5


@pytest.mark.asyncio
async def test_resume_uses_parallel_path_from_aligned_offset(tmp_path):
    """Resumed downloads used one 512 KiB stream (~2 MB/s). They must use the
    parallel path, starting at the last whole part before the partial end."""
    MiB = 1024 * 1024
    part = tmp_path / "v.bin"
    part.write_bytes(b"a" * (3 * MiB + 1234))  # partial file
    svc = TelegramService(account_repo=object())
    svc.client = object()
    seen = {}

    async def fake_download_file(client, doc, f, progress_callback=None, connections=None, offset=0):
        seen.update(offset=offset, pos=f.tell(), connections=connections)
        f.write(b"b" * (doc.size - offset))

    msg = SimpleNamespace(media=SimpleNamespace(document=SimpleNamespace(size=3600 * MiB)))
    with patch("app.telegram.service.download_file", fake_download_file):
        await svc.download(msg, str(part), offset=3 * MiB + 1234, connections=12)
    assert seen == {"offset": 3 * MiB, "pos": 3 * MiB, "connections": 12}
    assert part.stat().st_size == 3600 * MiB


@pytest.mark.asyncio
async def test_parallel_download_starts_at_offset():
    starts = []

    class S:
        def __init__(self, off): self.off = off
        async def next(self): return None
        async def disconnect(self): pass

    t = fast_telethon.ParallelTransferrer.__new__(fast_telethon.ParallelTransferrer)
    t.loop = asyncio.get_running_loop()

    async def fake_create(file, index, part_size, stride, part_count, start=0):
        starts.append(start + index * part_size)
        return S(start + index * part_size)
    t._create_download_sender = fake_create
    t._create_sender = None
    async for _ in t.download(None, 100 * 1024 * 1024, connection_count=3, start=4 * 1024 * 1024):
        pass
    assert sorted(starts) == [4 * 1024 * 1024, 5 * 1024 * 1024, 6 * 1024 * 1024]
