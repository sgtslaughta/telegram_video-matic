"""TDD: Test health, auth, and telegram routers."""
import pytest
import os
from unittest.mock import MagicMock, AsyncMock
from fastapi import Request
from app.api.auth import COOKIE_NAME, sign_session, verify_session
from app.api.routers import health, auth, telegram
from app.db.models import Account, AccountStatus
from app.api.schemas import LoginRequest, TelegramPhoneRequest, TelegramCodeRequest, TelegramPasswordRequest


# ============================================================================
# TASK 4: Health Router Tests
# ============================================================================


@pytest.mark.asyncio
async def test_health_get_ok():
    """Test 1: GET /api/health returns 200 with status ok."""
    result = await health.health()
    assert result == {"status": "ok"}


# ============================================================================
# TASK 5: Auth Router Tests
# ============================================================================


@pytest.mark.asyncio
async def test_auth_login_correct_password(monkeypatch):
    """Test 2: POST /api/auth/login with correct password sets cookie."""
    monkeypatch.setenv("TVM_APP_PASSWORD", "secret123")
    monkeypatch.setenv("TVM_SECRET_KEY", "test-secret")

    from starlette.responses import Response

    req = LoginRequest(password="secret123")
    response = Response()

    result = await auth.login(req, response)

    assert result["authenticated"] is True
    # Cookie should be set
    assert COOKIE_NAME in response.headers.get("set-cookie", "")


@pytest.mark.asyncio
async def test_auth_login_wrong_password(monkeypatch):
    """Test 3: POST /api/auth/login with wrong password returns 401."""
    monkeypatch.setenv("TVM_APP_PASSWORD", "secret123")

    from starlette.responses import Response

    req = LoginRequest(password="wrong")
    response = Response()

    with pytest.raises(Exception) as exc_info:
        await auth.login(req, response)

    assert "401" in str(exc_info.value)


@pytest.mark.asyncio
async def test_auth_me_unauthenticated(monkeypatch):
    """Test 4: GET /api/auth/me without cookie returns authenticated=false."""
    monkeypatch.setenv("TVM_APP_PASSWORD", "secret123")

    request = MagicMock(spec=Request)
    request.cookies = {}

    result = await auth.me(request)

    assert result.authenticated is False
    assert result.password_set is True


@pytest.mark.asyncio
async def test_auth_me_authenticated(monkeypatch):
    """Test 5: GET /api/auth/me with valid cookie returns authenticated=true."""
    monkeypatch.setenv("TVM_APP_PASSWORD", "secret123")
    monkeypatch.setenv("TVM_SECRET_KEY", "test-secret")

    # Create a valid cookie
    token = sign_session("secret123")

    request = MagicMock(spec=Request)
    request.cookies = {COOKIE_NAME: token}

    result = await auth.me(request)

    assert result.authenticated is True
    assert result.password_set is True


@pytest.mark.asyncio
async def test_auth_logout(monkeypatch):
    """Test 6: POST /api/auth/logout clears cookie."""
    monkeypatch.setenv("TVM_APP_PASSWORD", "secret123")

    from starlette.responses import Response

    response = Response()
    result = await auth.logout(response)

    assert result["authenticated"] is False


# ============================================================================
# TASK 6: Telegram Router Tests
# ============================================================================


@pytest.mark.asyncio
async def test_tg_status_returns_account_data(monkeypatch):
    """Test 7: GET /api/tg/status returns current account status."""
    monkeypatch.delenv("TVM_APP_PASSWORD", raising=False)

    request = MagicMock(spec=Request)
    account = Account(
        id=1,
        phone="+11234567890",
        api_id_enc="test_api_id",
        api_hash_enc="test_api_hash",
        session_enc="test_session",
        status=AccountStatus.CONNECTED,
        username="testuser",
        display_name="Test User",
    )
    service = MagicMock()
    service.account = account
    service.account_repo.get = AsyncMock(return_value=account)
    request.app.state.tg_service = service

    result = await telegram.tg_status(request)

    assert result.status == AccountStatus.CONNECTED.value
    assert result.username == "testuser"
    assert result.display_name == "Test User"


@pytest.mark.asyncio
async def test_tg_login_calls_service(monkeypatch):
    """Test 8: POST /api/tg/login delegates to service.start_login."""
    monkeypatch.delenv("TVM_APP_PASSWORD", raising=False)

    request = MagicMock(spec=Request)
    account = Account(
        id=1,
        phone="+11234567890",
        api_id_enc="test_api_id",
        api_hash_enc="test_api_hash",
        session_enc="test_session",
        status=AccountStatus.AWAITING_CODE,
        username="testuser",
        display_name="Test User",
    )
    service = MagicMock()
    service.account = account
    service.account_repo.get = AsyncMock(return_value=account)
    service.start_login = AsyncMock()
    request.app.state.tg_service = service

    req = TelegramPhoneRequest(phone="+11234567890")
    result = await telegram.tg_login(req, request)

    assert service.start_login.called
    assert result.status == AccountStatus.AWAITING_CODE.value


@pytest.mark.asyncio
async def test_tg_code_calls_service(monkeypatch):
    """Test 9: POST /api/tg/code delegates to service.submit_code."""
    monkeypatch.delenv("TVM_APP_PASSWORD", raising=False)

    request = MagicMock(spec=Request)
    account = Account(
        id=1,
        phone="+11234567890",
        api_id_enc="test_api_id",
        api_hash_enc="test_api_hash",
        session_enc="test_session",
        status=AccountStatus.CONNECTED,
        username="testuser",
        display_name="Test User",
    )
    service = MagicMock()
    service.account = account
    service.account_repo.get = AsyncMock(return_value=account)
    service.submit_code = AsyncMock()
    request.app.state.tg_service = service

    req = TelegramCodeRequest(code="12345")
    result = await telegram.tg_code(req, request)

    assert service.submit_code.called
    assert result.status == AccountStatus.CONNECTED.value


@pytest.mark.asyncio
async def test_tg_password_calls_service(monkeypatch):
    """Test 10: POST /api/tg/password delegates to service.submit_password."""
    monkeypatch.delenv("TVM_APP_PASSWORD", raising=False)

    request = MagicMock(spec=Request)
    account = Account(
        id=1,
        phone="+11234567890",
        api_id_enc="test_api_id",
        api_hash_enc="test_api_hash",
        session_enc="test_session",
        status=AccountStatus.CONNECTED,
        username="testuser",
        display_name="Test User",
    )
    service = MagicMock()
    service.account = account
    service.account_repo.get = AsyncMock(return_value=account)
    service.submit_password = AsyncMock()
    request.app.state.tg_service = service

    req = TelegramPasswordRequest(password="2fa_pwd")
    result = await telegram.tg_password(req, request)

    assert service.submit_password.called
    assert result.status == AccountStatus.CONNECTED.value


@pytest.mark.asyncio
async def test_tg_logout_calls_service(monkeypatch):
    """Test 11: POST /api/tg/logout delegates to service.logout."""
    monkeypatch.delenv("TVM_APP_PASSWORD", raising=False)

    request = MagicMock(spec=Request)
    account = Account(
        id=1,
        phone="+11234567890",
        api_id_enc="test_api_id",
        api_hash_enc="test_api_hash",
        session_enc="test_session",
        status=AccountStatus.DISCONNECTED,
        username="testuser",
        display_name="Test User",
    )
    service = MagicMock()
    service.account = account
    service.account_repo.get = AsyncMock(return_value=account)
    service.logout = AsyncMock()
    request.app.state.tg_service = service

    result = await telegram.tg_logout(request)

    assert service.logout.called
    assert result.status == AccountStatus.DISCONNECTED.value


@pytest.mark.asyncio
async def test_tg_phone_masking(monkeypatch):
    """Test 12: Telegram status response masks phone correctly."""
    monkeypatch.delenv("TVM_APP_PASSWORD", raising=False)

    request = MagicMock(spec=Request)
    account = Account(
        id=1,
        phone="+11234567890",
        api_id_enc="test_api_id",
        api_hash_enc="test_api_hash",
        session_enc="test_session",
        status=AccountStatus.CONNECTED,
        username="testuser",
        display_name="Test User",
    )
    service = MagicMock()
    service.account = account
    service.account_repo.get = AsyncMock(return_value=account)
    request.app.state.tg_service = service

    result = await telegram.tg_status(request)

    # Check phone is masked
    phone = result.phone
    assert phone is not None
    # Should be masked as +1****7890 or similar
    assert phone.startswith("+1")
    assert "*" in phone
    # Last 4 digits should be visible
    assert "90" in phone


# ============================================================================
# TASK 7: Channels Router Tests
# ============================================================================


@pytest.mark.asyncio
async def test_channels_list_from_db():
    """Test: GET /api/channels returns channels from DB."""
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    from sqlalchemy.pool import StaticPool
    from app.db.models import Base, Channel
    from app.api.routers.channels import list_channels

    # Setup: real in-memory DB
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Insert test channel
    async with SessionLocal() as session:
        ch = Channel(tg_id=123, title="Test Channel", username="test_ch", is_forum=False)
        session.add(ch)
        await session.commit()

    # Test the endpoint function directly (no live service → DB-only path)
    request = MagicMock(spec=Request)
    request.app.state.tg_service = None
    async with SessionLocal() as session:
        result = await list_channels(request, session)

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0].title == "Test Channel"

    await engine.dispose()


@pytest.mark.asyncio
async def test_channels_list_topics_from_db():
    """Test: GET /api/channels/{id}/topics returns topics from DB."""
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    from sqlalchemy.pool import StaticPool
    from app.db.models import Base, Channel, Topic
    from app.api.routers.channels import list_topics

    # Setup: real in-memory DB
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Insert test channel and topic
    async with SessionLocal() as session:
        ch = Channel(tg_id=123, title="Test Channel", is_forum=True)
        session.add(ch)
        await session.flush()
        t = Topic(channel_id=ch.id, tg_topic_id=1, title="General")
        session.add(t)
        await session.commit()
        channel_id = ch.id

    # Test the endpoint function directly (no live service → DB-only path)
    request = MagicMock(spec=Request)
    request.app.state.tg_service = None
    async with SessionLocal() as session:
        result = await list_topics(channel_id, request, session)

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0].title == "General"

    await engine.dispose()


# ============================================================================
# TASK 8: Subscriptions Router Tests
# ============================================================================


@pytest.mark.asyncio
async def test_sub_list_empty():
    """Test 13: GET /api/subscriptions on empty DB returns empty list."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    from sqlalchemy.pool import StaticPool
    from app.db.models import Base
    from app.api.routers import subscriptions

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    app = FastAPI()
    app.include_router(subscriptions.router)

    async def mock_get_db():
        async with SessionLocal() as session:
            yield session

    app.dependency_overrides[subscriptions.get_db] = mock_get_db

    client = TestClient(app)
    response = client.get("/api/subscriptions")

    assert response.status_code == 200
    assert response.json() == []

    await engine.dispose()


@pytest.mark.asyncio
async def test_sub_create_and_list():
    """Test 14: POST /api/subscriptions creates, GET lists it."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient


# ============================================================================
# TASK 8: Subscriptions Router Tests
# ============================================================================


@pytest.mark.asyncio
async def test_sub_list_empty():
    """Test 13: GET /api/subscriptions on empty DB returns empty list."""
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    from sqlalchemy.pool import StaticPool
    from app.db.models import Base
    from app.api.routers.subscriptions import list_subscriptions

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with SessionLocal() as session:
        result = await list_subscriptions(session)

    assert result == []
    await engine.dispose()


@pytest.mark.asyncio
async def test_sub_create_and_list():
    """Test 14: POST creates subscription, GET lists it."""
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    from sqlalchemy.pool import StaticPool
    from app.db.models import Base, Channel
    from app.api.routers.subscriptions import create_subscription, list_subscriptions
    from app.api.schemas import SubscriptionCreateRequest

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Create channel
    async with SessionLocal() as session:
        ch = Channel(tg_id=123, title="Test Channel", is_forum=False)
        session.add(ch)
        await session.commit()

    # Create subscription
    async with SessionLocal() as session:
        req = SubscriptionCreateRequest(
            channel_id=1,
            topic_id=None,
            enabled=True,
            storage_path="/tmp/test",
            rename_template="{name}",
        )
        result = await create_subscription(req, session)

    assert result.channel_id == 1
    assert result.enabled is True

    # List subscriptions
    async with SessionLocal() as session:
        items = await list_subscriptions(session)

    assert len(items) == 1

    await engine.dispose()


@pytest.mark.asyncio
async def test_sub_create_duplicate_409():
    """Test 15: POST duplicate (channel_id, topic_id) returns 409."""
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    from sqlalchemy.pool import StaticPool
    from fastapi import HTTPException
    from app.db.models import Base, Channel
    from app.api.routers.subscriptions import create_subscription
    from app.api.schemas import SubscriptionCreateRequest

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Create channel
    async with SessionLocal() as session:
        ch = Channel(tg_id=123, title="Test Channel", is_forum=False)
        session.add(ch)
        await session.commit()

    # Create first subscription
    async with SessionLocal() as session:
        req = SubscriptionCreateRequest(
            channel_id=1,
            topic_id=None,
            enabled=True,
            storage_path="/tmp/test",
            rename_template="{name}",
        )
        await create_subscription(req, session)

    # Try to create duplicate
    async with SessionLocal() as session:
        req = SubscriptionCreateRequest(
            channel_id=1,
            topic_id=None,
            enabled=True,
            storage_path="/tmp/test",
            rename_template="{name}",
        )
        try:
            await create_subscription(req, session)
            assert False, "Should have raised 409"
        except HTTPException as e:
            assert e.status_code == 409
            assert "already exists" in e.detail

    await engine.dispose()


@pytest.mark.asyncio
async def test_sub_create_invalid_regex_400():
    """Invalid filter_regex is rejected by the router with HTTP 400 (not 422)."""
    from fastapi import HTTPException
    from app.api.routers.subscriptions import _validate_regex

    try:
        _validate_regex("[invalid(regex")
        assert False, "Should have raised HTTPException"
    except HTTPException as e:
        assert e.status_code == 400
        assert "filter_regex" in e.detail


@pytest.mark.asyncio
async def test_sub_get_single():
    """Test 17: GET /api/subscriptions/{id} returns single subscription."""
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    from sqlalchemy.pool import StaticPool
    from fastapi import HTTPException
    from app.db.models import Base, Channel
    from app.db.repositories import subscriptions as sub_repo
    from app.api.routers.subscriptions import get_subscription

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with SessionLocal() as session:
        ch = Channel(tg_id=123, title="Test Channel", is_forum=False)
        session.add(ch)
        await session.commit()
        await sub_repo.create(
            session, channel_id=1, topic_id=None, storage_path="/tmp/test", rename_template="{name}"
        )

    async with SessionLocal() as session:
        result = await get_subscription(1, session)

    assert result.id == 1
    assert result.channel_id == 1

    await engine.dispose()


@pytest.mark.asyncio
async def test_sub_patch_update():
    """Test 18: PATCH updates subscription."""
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    from sqlalchemy.pool import StaticPool
    from app.db.models import Base, Channel
    from app.db.repositories import subscriptions as sub_repo
    from app.api.routers.subscriptions import update_subscription
    from app.api.schemas import SubscriptionUpdateRequest

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with SessionLocal() as session:
        ch = Channel(tg_id=123, title="Test Channel", is_forum=False)
        session.add(ch)
        await session.commit()
        await sub_repo.create(
            session, channel_id=1, topic_id=None, storage_path="/tmp/test", rename_template="{name}"
        )

    async with SessionLocal() as session:
        req = SubscriptionUpdateRequest(enabled=False)
        result = await update_subscription(1, req, session)

    assert result.enabled is False

    await engine.dispose()


@pytest.mark.asyncio
async def test_sub_patch_invalid_regex_400():
    """PATCH with invalid filter_regex is rejected by the router with HTTP 400."""
    from fastapi import HTTPException
    from app.api.routers.subscriptions import _validate_regex

    try:
        _validate_regex("[invalid(regex")
        assert False, "Should have raised HTTPException"
    except HTTPException as e:
        assert e.status_code == 400


@pytest.mark.asyncio
async def test_sub_delete():
    """Test 20: DELETE deletes subscription."""
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    from sqlalchemy.pool import StaticPool
    from fastapi import HTTPException
    from app.db.models import Base, Channel
    from app.db.repositories import subscriptions as sub_repo
    from app.api.routers.subscriptions import delete_subscription, get_subscription

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with SessionLocal() as session:
        ch = Channel(tg_id=123, title="Test Channel", is_forum=False)
        session.add(ch)
        await session.commit()
        await sub_repo.create(
            session, channel_id=1, topic_id=None, storage_path="/tmp/test", rename_template="{name}"
        )

    async with SessionLocal() as session:
        await delete_subscription(1, session)

    async with SessionLocal() as session:
        try:
            await get_subscription(1, session)
            assert False, "Should have raised 404"
        except HTTPException as e:
            assert e.status_code == 404

    await engine.dispose()


@pytest.mark.asyncio
async def test_sub_scan():
    """Test 21: POST /scan returns 200 when engine available."""
    from unittest.mock import AsyncMock, MagicMock
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    from sqlalchemy.pool import StaticPool
    from app.db.models import Base, Channel
    from app.db.repositories import subscriptions as sub_repo
    from app.api.routers.subscriptions import scan_subscription

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with SessionLocal() as session:
        ch = Channel(tg_id=123, title="Test Channel", is_forum=False)
        session.add(ch)
        await session.commit()
        await sub_repo.create(
            session, channel_id=1, topic_id=None, storage_path="/tmp/test", rename_template="{name}"
        )

    # Mock request with engine
    request = MagicMock()
    mock_engine = AsyncMock()
    mock_engine.scan_subscription = AsyncMock()
    request.app.state.engine = mock_engine

    async with SessionLocal() as session:
        result = await scan_subscription(1, request, session)

    assert result["status"] == "scanning"
    assert mock_engine.scan_subscription.called

    await engine.dispose()


# ============================================================================
# TASK 10: Downloads Router Tests
# ============================================================================


@pytest.mark.asyncio
async def test_downloads_list_active():
    """Test: GET /api/downloads/active returns active jobs."""
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    from sqlalchemy.pool import StaticPool
    from app.db.models import Base, DownloadJob, JobStatus, Channel, MediaItem
    from app.api.schemas import DownloadJobRead

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Insert test data
    async with SessionLocal() as session:
        ch = Channel(tg_id=123, title="Test Channel", is_forum=False)
        session.add(ch)
        await session.flush()
        media = MediaItem(
            channel_id=ch.id,
            tg_msg_id=1,
            date_posted=__import__("datetime").datetime.now(),
        )
        session.add(media)
        await session.flush()
        job = DownloadJob(media_id=media.id, status=JobStatus.RUNNING)
        session.add(job)
        await session.commit()

    # Test the function
    from app.db.repositories.downloads import list_active
    async with SessionLocal() as session:
        result = await list_active(session)

    assert len(result) == 1
    assert result[0].status == JobStatus.RUNNING

    await engine.dispose()


# ============================================================================
# TASK 11: Settings Router Tests
# ============================================================================


@pytest.mark.asyncio
async def test_settings_list_all():
    """Test: GET /api/settings returns all settings."""
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    from sqlalchemy.pool import StaticPool
    from app.db.models import Base, Setting
    from app.db.repositories.settings import list

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Insert test settings
    async with SessionLocal() as session:
        s1 = Setting(key="poll_interval_sec", value="60")
        s2 = Setting(key="theme", value="dark")
        session.add_all([s1, s2])
        await session.commit()

    # Test the function
    async with SessionLocal() as session:
        result = await list(session)

    assert len(result) == 2
    assert any(s.key == "poll_interval_sec" for s in result)

    await engine.dispose()


@pytest.mark.asyncio
async def test_settings_patch():
    """Test: PATCH /api/settings updates settings."""
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    from sqlalchemy.pool import StaticPool
    from app.db.models import Base, Setting
    from app.db.repositories.settings import set, list

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Insert test setting
    async with SessionLocal() as session:
        s = Setting(key="poll_interval_sec", value="60")
        session.add(s)
        await session.commit()

    # Update it
    async with SessionLocal() as session:
        await set(session, "poll_interval_sec", "300")

    # Verify
    async with SessionLocal() as session:
        result = await list(session)
        setting = [s for s in result if s.key == "poll_interval_sec"][0]

    assert setting.value == "300"

    await engine.dispose()


# ============================================================================
# TASK 12: Events Router Tests
# ============================================================================


@pytest.mark.asyncio
async def test_events_list_paginated():
    """Test: GET /api/events returns paginated events."""
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    from sqlalchemy.pool import StaticPool
    from app.db.models import Base, Event
    from app.db.repositories.events import list, add

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Insert test events
    async with SessionLocal() as session:
        for i in range(5):
            await add(session, level="INFO", kind="test", message=f"Event {i}")

    # Test pagination
    async with SessionLocal() as session:
        result = await list(session, limit=2, offset=0)

    assert len(result) == 2

    # Test offset
    async with SessionLocal() as session:
        result = await list(session, limit=2, offset=2)

    assert len(result) == 2

    await engine.dispose()


# ============================================================================
# TASK 13: Plugins Router Tests
# ============================================================================


@pytest.mark.asyncio
async def test_plugins_list():
    """Test: GET /api/plugins returns list of plugins."""
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    from sqlalchemy.pool import StaticPool
    from app.db.models import Base, Plugin
    from app.db.repositories.plugins import list

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Insert test plugin
    async with SessionLocal() as session:
        p = Plugin(name="test_plugin", version="1.0", enabled=True)
        session.add(p)
        await session.commit()

    # Test the function
    from app.db.repositories.plugins import list as list_plugins
    async with SessionLocal() as session:
        result = await list_plugins(session)

    assert len(result) == 1
    assert result[0].name == "test_plugin"

    await engine.dispose()


@pytest.mark.asyncio
async def test_plugins_patch():
    """Test: PATCH /api/plugins/{name} updates plugin."""
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    from sqlalchemy.pool import StaticPool
    from app.db.models import Base, Plugin
    from app.db.repositories.plugins import list as list_plugins, get_by_name, update

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Insert test plugin
    async with SessionLocal() as session:
        p = Plugin(name="test_plugin", version="1.0", enabled=False)
        session.add(p)
        await session.commit()

    # Update it
    async with SessionLocal() as session:
        plugin = await get_by_name(session, "test_plugin")
        await update(session, plugin.id, enabled=True)

    # Verify
    async with SessionLocal() as session:
        result = await list_plugins(session)
        plugin = result[0]

    assert plugin.enabled is True

    await engine.dispose()


@pytest.mark.asyncio
async def test_plugins_patch_enable_runs_host_lifecycle():
    """PATCH enabled=true persists AND drives the host (lifecycle + dispatch gate)."""
    from types import SimpleNamespace
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    from sqlalchemy.pool import StaticPool
    from app.db.models import Base, Plugin
    from app.db.repositories.plugins import get_by_name
    from app.sync.plugins import PluginBase, PluginContext, PluginHost
    from app.api.routers.plugins import patch_plugin
    from app.api.schemas import PluginPatchRequest

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as s:
        s.add(Plugin(name="rec", version="1.0", enabled=False))
        await s.commit()

    enabled_flag = {"v": False}

    class _Rec(PluginBase):
        name = "rec"
        async def on_enable(self):
            enabled_flag["v"] = True

    host = PluginHost()
    host.register(_Rec(PluginContext(name="rec", config={})), enabled=False)
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(
        plugin_host=host, session_factory=factory)))

    async with factory() as db:
        await patch_plugin("rec", PluginPatchRequest(enabled=True), request, db)

    assert enabled_flag["v"] is True
    assert host._entry("rec").enabled is True
    async with factory() as s:
        assert (await get_by_name(s, "rec")).enabled is True
    await engine.dispose()


# ============================================================================
# TASK 14: Real-Wiring Test (App Factory + Lifespan)
# ============================================================================


def test_app_factory_can_create():
    """
    Real-wiring test: verify create_app() builds app with routers registered.
    """
    from app.main import create_app

    app = create_app()

    # Verify app is created
    assert app is not None
    assert app.title == "Telegram Video-Matic"

    # Verify routers are registered via the OpenAPI schema (stable across
    # FastAPI versions; app.routes uses lazy _IncludedRouter wrappers in 0.138+).
    routes_info = list(app.openapi()["paths"].keys())

    # Should have health endpoint
    assert any("/api/health" in path for path in routes_info)
    # Should have subscriptions endpoint
    assert any("/api/subscriptions" in path for path in routes_info)
    # Should have auth endpoints
    assert any("/api/auth" in path for path in routes_info)
