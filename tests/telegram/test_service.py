import pytest
from unittest.mock import AsyncMock, MagicMock
from app.telegram.service import TelegramService
from app.db.models import Account, AccountStatus
from app.crypto import encrypt, decrypt


@pytest.fixture
def mock_client():
    """Mocked Telethon client."""
    client = AsyncMock()
    client.connect = AsyncMock(return_value=None)
    client.disconnect = AsyncMock(return_value=None)
    client.is_user_authorized = AsyncMock(return_value=True)
    return client


@pytest.fixture
def mock_account_repo():
    """Mocked AccountRepository."""
    repo = AsyncMock()
    return repo


@pytest.mark.asyncio
async def test_telegram_service_build_client_from_encrypted_session(mock_client, mock_account_repo):
    """Build Telethon client from decrypted StringSession stored in Account."""
    # Create a fake Account with encrypted session
    account = Account(
        id=1,
        api_id_enc=encrypt("123456"),
        api_hash_enc=encrypt("abcdef123456"),
        session_enc=encrypt("some_session_string"),
        phone="+1234567890",
        username="testuser",
        user_id=987654,
        display_name="Test User",
        status=AccountStatus.CONNECTED
    )
    mock_account_repo.get.return_value = account

    # Create service with mocked client factory (bypasses StringSession validation)
    def mock_client_factory(session, api_id, api_hash):
        # In tests, we ignore the session object and return the mock client
        return mock_client

    service = TelegramService(
        account_repo=mock_account_repo,
        client_factory=mock_client_factory
    )

    await service.load_account()

    # Verify the service stores the account and built a client
    assert service.account == account
    assert service.client is mock_client


@pytest.mark.asyncio
async def test_telegram_service_connect_success(mock_client, mock_account_repo):
    """Connect to Telegram; set status to connected if authorized."""
    account = Account(
        id=1,
        api_id_enc=encrypt("123456"),
        api_hash_enc=encrypt("abcdef123456"),
        session_enc=encrypt("some_session_string"),
        phone="+1234567890",
        username="testuser",
        user_id=987654,
        display_name="Test User",
        status=AccountStatus.DISCONNECTED
    )
    mock_account_repo.get.return_value = account
    mock_account_repo.update_status = AsyncMock()

    def mock_client_factory(session, api_id, api_hash):
        return mock_client

    service = TelegramService(
        account_repo=mock_account_repo,
        client_factory=mock_client_factory
    )
    service.client = mock_client
    service.account = account

    await service.connect()

    mock_client.connect.assert_called_once()
    mock_account_repo.update_status.assert_called_once_with(
        account.id, AccountStatus.CONNECTED
    )


@pytest.mark.asyncio
async def test_telegram_service_disconnect_persists_session(mock_client, mock_account_repo):
    """On disconnect, persist encrypted session and update status."""
    account = Account(
        id=1,
        api_id_enc=encrypt("123456"),
        api_hash_enc=encrypt("abcdef123456"),
        session_enc=encrypt("some_session_string"),
        phone="+1234567890",
        username="testuser",
        user_id=987654,
        display_name="Test User",
        status=AccountStatus.CONNECTED
    )
    mock_account_repo.get.return_value = account
    mock_account_repo.update_session = AsyncMock()
    mock_account_repo.update_status = AsyncMock()

    # Mock client.session.save() and get_session_string()
    mock_session = MagicMock()
    mock_session.save = MagicMock()
    mock_session.get_session_string = MagicMock(return_value="new_session_string")
    mock_client.session = mock_session

    def mock_client_factory(session, api_id, api_hash):
        return mock_client

    service = TelegramService(
        account_repo=mock_account_repo,
        client_factory=mock_client_factory
    )
    service.client = mock_client
    service.account = account

    await service.disconnect()

    mock_client.disconnect.assert_called_once()
    mock_account_repo.update_session.assert_called_once()
    mock_account_repo.update_status.assert_called_once_with(
        account.id, AccountStatus.DISCONNECTED
    )
