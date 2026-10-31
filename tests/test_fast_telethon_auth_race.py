"""Concurrent cross-DC downloads must each import their OWN exported auth.

Root cause of prod error "The provided authorization is invalid (caused by
...ImportAuthorizationRequest)": _create_sender wrote the import into the
shared client._init_request, so a concurrent download overwrote it before
the first one sent its request."""
import asyncio
from types import SimpleNamespace

import pytest
from telethon.tl.functions import InitConnectionRequest
from telethon.tl.functions.help import GetConfigRequest

from app.telegram import fast_telethon


class FakeSender:
    def __init__(self, auth_key, loggers=None):
        self.auth_key = auth_key
        self.sent_bytes = None

    async def connect(self, conn):
        await asyncio.sleep(0)

    async def send(self, req):
        # Telethon serializes when the send loop runs, i.e. after yielding.
        for _ in range(3):
            await asyncio.sleep(0)
        self.sent_bytes = req.query.query.bytes
        self.auth_key = object()


class FakeClient:
    def __init__(self):
        self._log = {}
        self._proxy = None
        self.n = 0
        self._init_request = InitConnectionRequest(
            api_id=1, device_model="d", system_version="s", app_version="a",
            system_lang_code="en", lang_pack="", lang_code="en", query=GetConfigRequest())

    async def _get_dc(self, dc_id):
        return SimpleNamespace(ip_address="1.1.1.1", port=443, id=dc_id)

    def _connection(self, *a, **k):
        return object()

    async def __call__(self, req):
        self.n += 1
        mine = self.n
        await asyncio.sleep(0)
        return SimpleNamespace(id=mine, bytes=f"auth-{mine}".encode())


@pytest.mark.asyncio
async def test_concurrent_exports_do_not_clobber_each_other(monkeypatch):
    monkeypatch.setattr(fast_telethon, "MTProtoSender", FakeSender)
    client = FakeClient()
    a = fast_telethon.ParallelTransferrer.__new__(fast_telethon.ParallelTransferrer)
    b = fast_telethon.ParallelTransferrer.__new__(fast_telethon.ParallelTransferrer)
    for t in (a, b):
        t.client, t.dc_id, t.auth_key = client, 4, None
    sa, sb = await asyncio.gather(a._create_sender(), b._create_sender())
    assert {sa.sent_bytes, sb.sent_bytes} == {b"auth-1", b"auth-2"}
    # The shared init request is never left pointing at an import.
    assert isinstance(client._init_request.query, GetConfigRequest)
