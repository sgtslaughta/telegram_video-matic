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

    # Test the endpoint function directly
    async with SessionLocal() as session:
        result = await list_channels(session)

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

    # Test the endpoint function directly
    async with SessionLocal() as session:
        result = await list_topics(channel_id, session)

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
