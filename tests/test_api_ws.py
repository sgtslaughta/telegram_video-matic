"""TDD: WebSocket hub and endpoint."""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock
from fastapi import FastAPI, WebSocketDisconnect
from fastapi.testclient import TestClient
from app.api.schemas import DownloadJobRead, TelegramStatusRead, WSSnapshot
from app.api.ws import WSHub


@pytest.mark.asyncio
async def test_ws_hub_connect_disconnect():
    """Test 1: WSHub.connect adds, disconnect removes."""
    hub = WSHub()

    # Mock websocket
    ws = MagicMock()
    ws.accept = AsyncMock()
    ws.send_text = AsyncMock()

    assert len(hub.active) == 0

    await hub.connect(ws)
    assert len(hub.active) == 1
    assert ws.accept.called

    hub.disconnect(ws)
    assert len(hub.active) == 0


@pytest.mark.asyncio
async def test_ws_hub_broadcast():
    """Test 2: WSHub.broadcast sends to all active connections."""
    hub = WSHub()

    ws1 = MagicMock()
    ws1.accept = AsyncMock()
    ws1.send_text = AsyncMock()

    ws2 = MagicMock()
    ws2.accept = AsyncMock()
    ws2.send_text = AsyncMock()

    await hub.connect(ws1)
    await hub.connect(ws2)

    msg = {"kind": "test", "data": {"value": 42}}
    await hub.broadcast(msg)

    assert ws1.send_text.called
    assert ws2.send_text.called

    # Verify JSON serialization
    call_args_1 = ws1.send_text.call_args[0][0]
    assert json.loads(call_args_1) == msg


@pytest.mark.asyncio
async def test_ws_hub_broadcast_cleans_dead():
    """Test 3: WSHub.broadcast removes dead connections."""
    hub = WSHub()

    ws_dead = MagicMock()
    ws_dead.accept = AsyncMock()
    ws_dead.send_text = AsyncMock(side_effect=Exception("Dead"))

    ws_live = MagicMock()
    ws_live.accept = AsyncMock()
    ws_live.send_text = AsyncMock()

    await hub.connect(ws_dead)
    await hub.connect(ws_live)
    assert len(hub.active) == 2

    msg = {"kind": "test"}
    await hub.broadcast(msg)

    # Dead connection should be removed
    assert len(hub.active) == 1
    assert ws_live in hub.active
    assert ws_dead not in hub.active


@pytest.mark.asyncio
async def test_websocket_endpoint_snapshot(monkeypatch, caplog):
    """Test 4: websocket_endpoint sends snapshot on connect."""
    from app.api.ws import websocket_endpoint

    # Mock websocket
    ws = MagicMock()
    ws.accept = AsyncMock()
    ws.receive_text = AsyncMock(side_effect=WebSocketDisconnect(1000))
    ws.send_json = AsyncMock()

    # Mock hub (all methods mocked)
    hub = MagicMock()
    hub.active = set()
    hub.connect = AsyncMock()
    hub.disconnect = MagicMock()

    # Mock snapshot function
    snap = WSSnapshot(
        active_downloads=[],
        tg_status=TelegramStatusRead(
            status="disconnected",
            username=None,
            display_name=None,
            phone=None,
        )
    )
    snapshot_fn = AsyncMock(return_value=snap)

    # Run endpoint
    await websocket_endpoint(ws, hub, snapshot_fn)

    # Verify connect was called
    assert hub.connect.called

    # Verify snapshot was sent
    assert ws.send_json.called
    call_args = ws.send_json.call_args[0][0]
    assert call_args["kind"] == "snapshot"
    assert "active_downloads" in call_args["data"]
    assert "tg_status" in call_args["data"]

    # Verify disconnect was called
    assert hub.disconnect.called
