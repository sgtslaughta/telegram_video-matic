"""Real HTTP integration tests using FastAPI TestClient against create_app().

Covers auth, subscriptions, media, telegram, websocket, error cases.
Uses in-memory SQLite, mocked TelegramService, high poll_interval.
"""
import os
import pytest
import json
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from app.main import create_app
from app.db.models import Channel, Subscription, MediaItem, AccountStatus
from datetime import datetime


@pytest.fixture
def test_app():
    """Create app with in-memory DB and mocked TelegramService."""
    # Set env BEFORE any imports trigger app init
    old_db = os.environ.get("DATABASE_URL")
    old_poll = os.environ.get("POLL_INTERVAL_SEC")
    old_pwd = os.environ.get("TVM_APP_PASSWORD")

    # Temp file (not :memory:) so every connection/event-loop shares one DB —
    # ":memory:" gives each connection its own DB, so seed() and the request
    # handler saw different databases (flaky 404s).
    import tempfile
    _fd, _dbpath = tempfile.mkstemp(suffix=".sqlite")
    os.close(_fd)
    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_dbpath}"
    os.environ["POLL_INTERVAL_SEC"] = "999"
    os.environ.pop("TVM_APP_PASSWORD", None)

    # Reload engine module to pick up new DATABASE_URL
    import importlib
    import app.db.engine as engine_mod
    importlib.reload(engine_mod)

    # Create app (lifespan will run with new env)
    app = create_app()

    # Mock TelegramService after startup to prevent network calls
    mock_tg_service = MagicMock()
    mock_tg_service.account = None
    mock_tg_service.disconnect = AsyncMock()
    app.state.tg_service = mock_tg_service

    yield app

    # Remove temp DB file
    try:
        os.unlink(_dbpath)
    except OSError:
        pass

    # Restore env
    if old_db:
        os.environ["DATABASE_URL"] = old_db
    else:
        os.environ.pop("DATABASE_URL", None)
    if old_poll:
        os.environ["POLL_INTERVAL_SEC"] = old_poll
    else:
        os.environ.pop("POLL_INTERVAL_SEC", None)
    if old_pwd:
        os.environ["TVM_APP_PASSWORD"] = old_pwd
    else:
        os.environ.pop("TVM_APP_PASSWORD", None)


# =============================================================================
# Task 1: Health
# =============================================================================


def test_health_returns_200(test_app):
    """GET /api/health → 200 ok."""
    with TestClient(test_app) as client:
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


# =============================================================================
# Task 2: Auth gate
# =============================================================================


def test_auth_open_mode_no_password(test_app):
    """With no TVM_APP_PASSWORD set, protected endpoints are open (200)."""
    with TestClient(test_app) as client:
        response = client.get("/api/subscriptions")
        assert response.status_code == 200


# =============================================================================
# Task 3: Subscriptions CRUD over HTTP
# =============================================================================


def test_subscriptions_post_create_201(test_app):
    """POST /api/subscriptions → 201 created."""
    with TestClient(test_app) as client:
        async def seed_channel():
            async with test_app.state.async_session() as session:
                ch = Channel(tg_id=123, title="Test Ch", is_forum=False)
                session.add(ch)
                await session.commit()
                return ch.id

        ch_id = asyncio.run(seed_channel())

        payload = {
            "channel_id": ch_id,
            "topic_id": None,
            "enabled": True,
            "storage_path": "/tmp/test",
            "rename_template": "{name}",
        }
        response = client.post("/api/subscriptions", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["channel_id"] == ch_id
        assert data["enabled"] is True


def test_subscriptions_duplicate_409(test_app):
    """POST duplicate (channel_id, topic_id) → 409."""
    with TestClient(test_app) as client:
        async def seed_channel():
            async with test_app.state.async_session() as session:
                ch = Channel(tg_id=123, title="Test Ch", is_forum=False)
                session.add(ch)
                await session.commit()
                return ch.id

        ch_id = asyncio.run(seed_channel())

        payload = {
            "channel_id": ch_id,
            "topic_id": None,
            "enabled": True,
            "storage_path": "/tmp/test",
            "rename_template": "{name}",
        }

        response = client.post("/api/subscriptions", json=payload)
        assert response.status_code == 201

        response = client.post("/api/subscriptions", json=payload)
        assert response.status_code == 409
        assert "already exists" in response.json().get("detail", "").lower()


def test_subscriptions_invalid_regex_400(test_app):
    """POST with invalid filter_regex → 400."""
    with TestClient(test_app) as client:
        async def seed_channel():
            async with test_app.state.async_session() as session:
                ch = Channel(tg_id=123, title="Test Ch", is_forum=False)
                session.add(ch)
                await session.commit()
                return ch.id

        ch_id = asyncio.run(seed_channel())

        payload = {
            "channel_id": ch_id,
            "topic_id": None,
            "enabled": True,
            "storage_path": "/tmp/test",
            "rename_template": "{name}",
            "filter_regex": "[invalid(regex",
        }
        response = client.post("/api/subscriptions", json=payload)
        assert response.status_code == 400
        assert "regex" in response.json().get("detail", "").lower()


def test_subscriptions_get_list(test_app):
    """GET /api/subscriptions lists created subscriptions."""
    with TestClient(test_app) as client:
        async def seed():
            async with test_app.state.async_session() as session:
                ch = Channel(tg_id=123, title="Test Ch", is_forum=False)
                session.add(ch)
                await session.commit()
                return ch.id

        ch_id = asyncio.run(seed())

        payload = {
            "channel_id": ch_id,
            "topic_id": None,
            "enabled": True,
            "storage_path": "/tmp/test",
            "rename_template": "{name}",
        }
        client.post("/api/subscriptions", json=payload)

        response = client.get("/api/subscriptions")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["channel_id"] == ch_id


def test_subscriptions_patch_update(test_app):
    """PATCH /api/subscriptions/{id} updates."""
    with TestClient(test_app) as client:
        async def seed():
            async with test_app.state.async_session() as session:
                ch = Channel(tg_id=123, title="Test Ch", is_forum=False)
                session.add(ch)
                await session.commit()
                s = Subscription(channel_id=ch.id, storage_path="/tmp", rename_template="{name}")
                session.add(s)
                await session.commit()
                return s.id

        sub_id = asyncio.run(seed())

        response = client.patch(
            f"/api/subscriptions/{sub_id}",
            json={"enabled": False}
        )
        assert response.status_code == 200
        assert response.json()["enabled"] is False


def test_subscriptions_delete_204(test_app):
    """DELETE /api/subscriptions/{id} → 204."""
    with TestClient(test_app) as client:
        async def seed():
            async with test_app.state.async_session() as session:
                ch = Channel(tg_id=123, title="Test Ch", is_forum=False)
                session.add(ch)
                await session.commit()
                s = Subscription(channel_id=ch.id, storage_path="/tmp", rename_template="{name}")
                session.add(s)
                await session.commit()
                return s.id

        sub_id = asyncio.run(seed())

        response = client.delete(f"/api/subscriptions/{sub_id}")
        assert response.status_code == 204

        response = client.get(f"/api/subscriptions/{sub_id}")
        assert response.status_code == 404


# =============================================================================
# Task 4: Media filtering
# =============================================================================


def test_media_get_with_status_filter(test_app):
    """GET /api/media with status filter returns matching items."""
    with TestClient(test_app) as client:
        async def seed():
            async with test_app.state.async_session() as session:
                ch = Channel(tg_id=123, title="Test Ch", is_forum=False)
                session.add(ch)
                await session.flush()
                sub = Subscription(channel_id=ch.id, storage_path="/tmp", rename_template="{name}")
                session.add(sub)
                await session.flush()
                media = MediaItem(
                    subscription_id=sub.id,
                    channel_id=ch.id,
                    tg_msg_id=1,
                    date_posted=datetime.now(),
                    status="PENDING",
                )
                session.add(media)
                await session.commit()
                return media.id

        media_id = asyncio.run(seed())

        response = client.get("/api/media?status=PENDING")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert data[0]["id"] == media_id
        assert data[0]["status"] == "PENDING"


# =============================================================================
# Task 5: Telegram status (no secrets in response)
# =============================================================================


def test_telegram_status_200_disconnected(test_app):
    """GET /api/tg/status → 200, status='disconnected', no secrets."""
    with TestClient(test_app) as client:
        response = client.get("/api/tg/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "disconnected"
        assert "api_hash" not in str(data)
        assert "api_id" not in str(data)
        assert "session" not in str(data)


# =============================================================================
# Task 6: WebSocket
# =============================================================================


def test_websocket_connect_snapshot(test_app):
    """Connect to /api/ws, receive snapshot message on connect."""
    with TestClient(test_app) as client:
        with client.websocket_connect("/api/ws") as websocket:
            data = websocket.receive_json()
            assert data["kind"] == "snapshot"
            assert "active_downloads" in data["data"]
            assert isinstance(data["data"]["active_downloads"], list)


# =============================================================================
# Task 7: Unknown routes
# =============================================================================


def test_unknown_path_404(test_app):
    """GET /api/invalid → 404."""
    with TestClient(test_app) as client:
        response = client.get("/api/invalid")
        assert response.status_code == 404


# =============================================================================
# Task 8: Integration: subscription lifecycle
# =============================================================================


def test_subscription_lifecycle(test_app):
    """Create, read, update, delete a subscription over HTTP."""
    with TestClient(test_app) as client:
        async def seed():
            async with test_app.state.async_session() as session:
                ch = Channel(tg_id=999, title="Lifecycle Ch", is_forum=False)
                session.add(ch)
                await session.commit()
                return ch.id

        ch_id = asyncio.run(seed())

        payload = {
            "channel_id": ch_id,
            "topic_id": None,
            "enabled": True,
            "storage_path": "/tmp/test",
            "rename_template": "{name}",
        }
        resp = client.post("/api/subscriptions", json=payload)
        assert resp.status_code == 201
        sub_id = resp.json()["id"]

        resp = client.get(f"/api/subscriptions/{sub_id}")
        assert resp.status_code == 200
        assert resp.json()["enabled"] is True

        resp = client.patch(f"/api/subscriptions/{sub_id}", json={"enabled": False})
        assert resp.status_code == 200
        assert resp.json()["enabled"] is False

        resp = client.delete(f"/api/subscriptions/{sub_id}")
        assert resp.status_code == 204

        resp = client.get(f"/api/subscriptions/{sub_id}")
        assert resp.status_code == 404
