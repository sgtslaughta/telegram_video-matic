"""Parallel download keeps every connection busy (no lock-step waves) and
still yields parts in file order."""
import asyncio

import pytest

from app.telegram import fast_telethon


class FakeSender:
    def __init__(self, idx, n, parts, delays, log):
        self.idx, self.n, self.parts, self.k = idx, n, parts, 0
        self.delays, self.log = delays, log

    async def next(self):
        part = self.idx + self.k * self.n
        if part >= self.parts:
            return None
        self.k += 1
        self.log.append(("start", part))
        await asyncio.sleep(self.delays.get(part, 0.001))
        self.log.append(("done", part))
        return f"p{part}".encode()

    async def disconnect(self):
        pass


def _transferrer(n, parts, delays, log):
    t = fast_telethon.ParallelTransferrer.__new__(fast_telethon.ParallelTransferrer)
    t.loop = asyncio.get_running_loop()

    async def init(connections, file, part_count, part_size):
        t.senders = [FakeSender(i, n, parts, delays, log) for i in range(n)]
    t._init_download = init
    return t


@pytest.mark.asyncio
async def test_parts_in_order_and_no_wave_barrier():
    log = []
    # part 0 is slow; sender 1 must start its next part (3) long before 0 finishes
    t = _transferrer(3, 7, {0: 0.05}, log)
    out = [b async for b in t.download(None, 7 * 1024, part_size_kb=1, connection_count=3)]
    assert out == [f"p{i}".encode() for i in range(7)]
    # Lock-step waves would wait for slow part 0 before starting part 4.
    assert log.index(("start", 4)) < log.index(("done", 0))


def test_large_files_use_1mb_parts():
    assert fast_telethon.part_size_for(3_600 * 1024 * 1024) == 1024 * 1024


@pytest.mark.asyncio
async def test_sender_error_propagates_and_workers_stop():
    log = []
    t = _transferrer(2, 6, {}, log)

    async def boom():
        raise ConnectionError("dc gone")
    async def init(connections, file, part_count, part_size):
        t.senders = [FakeSender(i, 2, 6, {}, log) for i in range(2)]
        t.senders[1].next = boom
    t._init_download = init
    cleaned = []

    async def cleanup():
        cleaned.append(True)
    t._cleanup = cleanup
    with pytest.raises(ConnectionError):
        async for _ in t.download(None, 6 * 1024, part_size_kb=1, connection_count=2):
            pass
    assert cleaned == [True]
