"""WebSocket hub for real-time broadcasts."""
import asyncio
import json
import logging
from typing import Callable, Any
from fastapi import WebSocket, WebSocketDisconnect
from app.api.schemas import WSSnapshot

logger = logging.getLogger(__name__)


class WSHub:
    """Manage active WebSocket connections; broadcast messages."""

    def __init__(self):
        self.active: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        """Accept and register connection."""
        await websocket.accept()
        self.active.add(websocket)
        logger.debug(f"WS client connected, total: {len(self.active)}")

    def disconnect(self, websocket: WebSocket):
        """Remove disconnected connection."""
        self.active.discard(websocket)
        logger.debug(f"WS client disconnected, total: {len(self.active)}")

    async def broadcast(self, message: dict[str, Any]):
        """Send message to all connected clients as JSON."""
        if not self.active:
            return

        payload = json.dumps(message)
        disconnected = []

        for ws in self.active:
            try:
                await ws.send_text(payload)
            except Exception as e:
                logger.warning(f"Failed to broadcast to WS: {e}")
                disconnected.append(ws)

        # Clean up dead connections
        for ws in disconnected:
            self.disconnect(ws)


async def websocket_endpoint(
    websocket: WebSocket,
    hub: WSHub,
    snapshot: Callable[[], WSSnapshot],
):
    """
    /api/ws endpoint. On connect, send snapshot (active downloads + TG status).
    Then stream broadcasts. Client→server limited to ping/handshake.
    """
    await hub.connect(websocket)

    try:
        # Send snapshot
        snap = await snapshot()
        await websocket.send_json({
            "kind": "snapshot",
            "data": snap.model_dump(),
        })

        # Receive loop: handle ping, ignore others
        while True:
            try:
                data = await websocket.receive_text()
                msg = json.loads(data)
                if msg.get("kind") == "ping":
                    await websocket.send_json({"kind": "pong"})
            except json.JSONDecodeError:
                logger.warning("Invalid JSON from WS client, ignoring")
            except WebSocketDisconnect:
                raise
            except Exception as e:
                logger.warning(f"WS receive error: {e}")
                break

    except WebSocketDisconnect:
        hub.disconnect(websocket)
    except Exception as e:
        logger.error(f"WS error: {e}")
        hub.disconnect(websocket)
