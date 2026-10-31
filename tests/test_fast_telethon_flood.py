"""Telegram rate-limits GetFile with short flood waits. A download must ride
them out (not fail after Telethon's 6 retries), and every connection must
back off together so the account stays under the limit."""
import asyncio
import time

import pytest
from telethon import errors

from app.telegram import fast_telethon


class FakeClient:
    """Stands in for the client (pause key) and its MTProto sender."""

    def __init__(self, floods):
        self.floods = floods  # how many sends raise FloodWait before succeeding
        self.calls = []

    async def send(self, request):
        self.calls.append(time.monotonic())
        if self.floods:
            self.floods -= 1
            raise errors.FloodWaitError(request=None, capture=1)
        return type("R", (), {"bytes": b"x"})()


def _sender(client):
    s = fast_telethon.DownloadSender.__new__(fast_telethon.DownloadSender)
    s.client, s.sender, s.request, s.stride, s.remaining = client, client, type("Q", (), {"offset": 0})(), 1, 3
    return s


@pytest.mark.asyncio
async def test_flood_waits_are_ridden_out_not_fatal(monkeypatch):
    monkeypatch.setattr(fast_telethon, "FLOOD_SLEEP_SCALE", 0.01)
    client = FakeClient(floods=8)  # more than Telethon's 6 attempts
    assert await _sender(client).next() == b"x"
    assert len(client.calls) == 9  # 8 flood waits ridden out, then success


@pytest.mark.asyncio
async def test_flood_wait_pauses_all_connections(monkeypatch):
    monkeypatch.setattr(fast_telethon, "FLOOD_SLEEP_SCALE", 0.05)
    client = FakeClient(floods=1)
    a, b = _sender(client), _sender(client)
    await a.next()  # hits a 1s (scaled to 50 ms) flood wait, sets the shared pause
    t0 = time.monotonic()
    fast_telethon._pause_until[id(client)] = time.monotonic() + 0.05
    await b.next()  # must wait for the shared pause even though it never flooded
    assert time.monotonic() - t0 >= 0.045
