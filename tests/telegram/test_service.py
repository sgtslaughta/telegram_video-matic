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

    # Mock client.session.save() and save()
    mock_session = MagicMock()
    mock_session.save = MagicMock()
    mock_session.save = MagicMock(return_value="new_session_string")
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


# ============================================================================
# Task 4: Login state machine tests
# ============================================================================

@pytest.mark.asyncio
async def test_start_login_phone(mock_client, mock_account_repo):
    """start_login(phone) → awaiting_code; store phone_code_hash in memory."""
    account = Account(
        id=1,
        api_id_enc=encrypt("123456"),
        api_hash_enc=encrypt("abcdef123456"),
        session_enc=None,
        phone=None,
        username=None,
        user_id=None,
        display_name=None,
        status=AccountStatus.DISCONNECTED
    )
    mock_account_repo.get.return_value = account
    mock_account_repo.update_status = AsyncMock()
    mock_account_repo.update_phone = AsyncMock()

    # Mock send_code_request
    mock_sent_code = MagicMock()
    mock_sent_code.phone_code_hash = "abc123def456"
    mock_client.send_code_request = AsyncMock(return_value=mock_sent_code)

    def mock_client_factory(session, api_id, api_hash):
        return mock_client

    service = TelegramService(
        account_repo=mock_account_repo,
        client_factory=mock_client_factory
    )
    service.client = mock_client
    service.account = account

    await service.start_login("+1234567890")

    mock_client.send_code_request.assert_called_once_with("+1234567890")
    assert service._phone_code_hash == "abc123def456"
    mock_account_repo.update_status.assert_called_with(account.id, AccountStatus.AWAITING_CODE)
    mock_account_repo.update_phone.assert_called_once_with(account.id, "+1234567890")


@pytest.mark.asyncio
async def test_submit_code_success(mock_client, mock_account_repo):
    """submit_code(code) → authorized → connected. Persist session."""
    from telethon.errors import SessionPasswordNeededError

    account = Account(
        id=1,
        api_id_enc=encrypt("123456"),
        api_hash_enc=encrypt("abcdef123456"),
        session_enc=None,
        phone="+1234567890",
        username=None,
        user_id=None,
        display_name=None,
        status=AccountStatus.AWAITING_CODE
    )
    mock_account_repo.get.return_value = account
    mock_account_repo.update_status = AsyncMock()
    mock_account_repo.update_session = AsyncMock()

    mock_me = MagicMock()
    mock_me.username = "testuser"
    mock_me.id = 987654
    mock_me.first_name = "Test"
    mock_client.sign_in = AsyncMock(return_value=mock_me)
    mock_client.is_user_authorized = AsyncMock(return_value=True)
    mock_client.session.save = MagicMock(return_value="new_session_string")

    def mock_client_factory(session, api_id, api_hash):
        return mock_client

    service = TelegramService(
        account_repo=mock_account_repo,
        client_factory=mock_client_factory
    )
    service.client = mock_client
    service._phone_code_hash = "abc123def456"
    service.account = account

    await service.submit_code("123456")

    mock_client.sign_in.assert_called_once_with("+1234567890", "123456", phone_code_hash="abc123def456")
    # Session persisted
    mock_account_repo.update_session.assert_called_once()
    # Status → connected
    mock_account_repo.update_status.assert_called_with(account.id, AccountStatus.CONNECTED)


@pytest.mark.asyncio
async def test_submit_code_requires_password(mock_client, mock_account_repo):
    """submit_code(code) → SessionPasswordNeededError → awaiting_password."""
    from telethon.errors import SessionPasswordNeededError

    account = Account(
        id=1,
        api_id_enc=encrypt("123456"),
        api_hash_enc=encrypt("abcdef123456"),
        session_enc=None,
        phone="+1234567890",
        username=None,
        user_id=None,
        display_name=None,
        status=AccountStatus.AWAITING_CODE
    )
    mock_account_repo.get.return_value = account
    mock_account_repo.update_status = AsyncMock()

    mock_client.sign_in = AsyncMock(side_effect=SessionPasswordNeededError(None))

    def mock_client_factory(session, api_id, api_hash):
        return mock_client

    service = TelegramService(
        account_repo=mock_account_repo,
        client_factory=mock_client_factory
    )
    service.client = mock_client
    service._phone_code_hash = "abc123def456"
    service.account = account

    await service.submit_code("123456")

    # Status → awaiting_password
    mock_account_repo.update_status.assert_called_with(account.id, AccountStatus.AWAITING_PASSWORD)


@pytest.mark.asyncio
async def test_submit_password(mock_client, mock_account_repo):
    """submit_password(pw) → connected. Persist session."""
    account = Account(
        id=1,
        api_id_enc=encrypt("123456"),
        api_hash_enc=encrypt("abcdef123456"),
        session_enc=None,
        phone="+1234567890",
        username=None,
        user_id=None,
        display_name=None,
        status=AccountStatus.AWAITING_PASSWORD
    )
    mock_account_repo.get.return_value = account
    mock_account_repo.update_status = AsyncMock()
    mock_account_repo.update_session = AsyncMock()

    mock_me = MagicMock()
    mock_me.username = "testuser"
    mock_me.id = 987654
    mock_me.first_name = "Test"
    mock_client.sign_in = AsyncMock(return_value=mock_me)
    mock_client.session.save = MagicMock(return_value="new_session_string")

    def mock_client_factory(session, api_id, api_hash):
        return mock_client

    service = TelegramService(
        account_repo=mock_account_repo,
        client_factory=mock_client_factory
    )
    service.client = mock_client
    service.account = account

    await service.submit_password("mypassword")

    mock_client.sign_in.assert_called_once_with(password="mypassword")
    # Session persisted
    mock_account_repo.update_session.assert_called_once()
    # Status → connected
    mock_account_repo.update_status.assert_called_with(account.id, AccountStatus.CONNECTED)


@pytest.mark.asyncio
async def test_logout(mock_client, mock_account_repo):
    """logout() → calls client.log_out(), clears session, status → disconnected."""
    account = Account(
        id=1,
        api_id_enc=encrypt("123456"),
        api_hash_enc=encrypt("abcdef123456"),
        session_enc=encrypt("some_session"),
        phone="+1234567890",
        username="testuser",
        user_id=987654,
        display_name="Test",
        status=AccountStatus.CONNECTED
    )
    mock_account_repo.get.return_value = account
    mock_account_repo.update_status = AsyncMock()
    mock_account_repo.update_session = AsyncMock()

    mock_client.log_out = AsyncMock(return_value=True)

    def mock_client_factory(session, api_id, api_hash):
        return mock_client

    service = TelegramService(
        account_repo=mock_account_repo,
        client_factory=mock_client_factory
    )
    service.client = mock_client
    service.account = account

    await service.logout()

    mock_client.log_out.assert_called_once()
    # Session cleared
    mock_account_repo.update_session.assert_called_once_with(account.id, None)
    # Status → disconnected
    mock_account_repo.update_status.assert_called_with(account.id, AccountStatus.DISCONNECTED)


# ============================================================================
# Task 5: Read-only fetch methods tests
# ============================================================================

@pytest.mark.asyncio
async def test_list_channels(mock_client, mock_account_repo):
    """list_channels() → [ChannelDTO] from dialogs (Channel types only)."""
    from telethon.tl.types import Channel

    account = Account(
        id=1,
        api_id_enc=encrypt("123456"),
        api_hash_enc=encrypt("abcdef123456"),
        session_enc=encrypt("some_session"),
        phone="+1234567890",
        username="testuser",
        user_id=987654,
        display_name="Test",
        status=AccountStatus.CONNECTED
    )
    mock_account_repo.get.return_value = account

    # Mock dialogs with real Channel types
    mock_channel_1 = MagicMock(spec=Channel)
    mock_channel_1.id = 123456
    mock_channel_1.title = "Channel 1"
    mock_channel_1.username = "channel1"
    mock_channel_1.forum = False
    mock_channel_1.photo = None

    mock_channel_2 = MagicMock(spec=Channel)
    mock_channel_2.id = 654321
    mock_channel_2.title = "Channel 2"
    mock_channel_2.username = "channel2"
    mock_channel_2.forum = True
    mock_channel_2.photo = None

    mock_dialog_1 = MagicMock()
    mock_dialog_1.entity = mock_channel_1

    mock_dialog_2 = MagicMock()
    mock_dialog_2.entity = mock_channel_2

    mock_client.get_dialogs = AsyncMock(return_value=[mock_dialog_1, mock_dialog_2])

    def mock_client_factory(session, api_id, api_hash):
        return mock_client

    service = TelegramService(
        account_repo=mock_account_repo,
        client_factory=mock_client_factory
    )
    service.client = mock_client

    channels = await service.list_channels(limit=100)

    assert len(channels) == 2
    assert channels[0].tg_id == 123456
    assert channels[0].title == "Channel 1"
    assert channels[0].is_forum is False
    assert channels[1].tg_id == 654321
    assert channels[1].is_forum is True


@pytest.mark.asyncio
async def test_list_topics_forum_channel(mock_account_repo):
    """list_topics(channel) → [TopicDTO] for forum channel."""
    from telethon.tl.functions.messages import GetForumTopicsRequest

    account = Account(
        id=1,
        api_id_enc=encrypt("123456"),
        api_hash_enc=encrypt("abcdef123456"),
        session_enc=encrypt("some_session"),
        phone="+1234567890",
        username="testuser",
        user_id=987654,
        display_name="Test",
        status=AccountStatus.CONNECTED
    )
    mock_account_repo.get.return_value = account

    # Mock forum topics response
    mock_topic_1 = MagicMock()
    mock_topic_1.id = 1
    mock_topic_1.title = "General"

    mock_topic_2 = MagicMock()
    mock_topic_2.id = 2
    mock_topic_2.title = "News"

    mock_response = MagicMock()
    mock_response.topics = [mock_topic_1, mock_topic_2]

    # Create a properly mocked client that supports async __call__
    mock_client = AsyncMock()
    mock_client.return_value = mock_response
    mock_client.side_effect = None

    def mock_client_factory(session, api_id, api_hash):
        return mock_client

    service = TelegramService(
        account_repo=mock_account_repo,
        client_factory=mock_client_factory
    )
    service.client = mock_client

    from app.telegram.dtos import ChannelDTO
    channel_dto = ChannelDTO(
        tg_id=123456,
        title="Forum Channel",
        username="forumchan",
        is_forum=True,
        photo_b64=None,
        raw={}
    )

    topics = await service.list_topics(channel_dto)

    assert len(topics) == 2
    assert topics[0].tg_topic_id == 1
    assert topics[0].title == "General"
    assert topics[1].tg_topic_id == 2
    assert topics[1].title == "News"


@pytest.mark.asyncio
async def test_list_topics_non_forum_synthetic_general(mock_client, mock_account_repo):
    """list_topics(non_forum_channel) → [TopicDTO(General)]."""
    account = Account(
        id=1,
        api_id_enc=encrypt("123456"),
        api_hash_enc=encrypt("abcdef123456"),
        session_enc=encrypt("some_session"),
        phone="+1234567890",
        username="testuser",
        user_id=987654,
        display_name="Test",
        status=AccountStatus.CONNECTED
    )
    mock_account_repo.get.return_value = account

    def mock_client_factory(session, api_id, api_hash):
        return mock_client

    service = TelegramService(
        account_repo=mock_account_repo,
        client_factory=mock_client_factory
    )
    service.client = mock_client

    from app.telegram.dtos import ChannelDTO
    channel_dto = ChannelDTO(
        tg_id=123456,
        title="Regular Channel",
        username="regularchan",
        is_forum=False,
        photo_b64=None,
        raw={}
    )

    topics = await service.list_topics(channel_dto)

    # Should return synthetic General topic
    assert len(topics) == 1
    assert topics[0].tg_topic_id == 1
    assert topics[0].title == "General"


@pytest.mark.asyncio
async def test_iter_media_yields_media_dtos(mock_client, mock_account_repo):
    """iter_media(channel, topic) yields MediaDTO for video/document media."""
    from datetime import datetime
    from telethon.tl.types import MessageMediaDocument, DocumentAttributeFilename, DocumentAttributeVideo

    account = Account(
        id=1,
        api_id_enc=encrypt("123456"),
        api_hash_enc=encrypt("abcdef123456"),
        session_enc=encrypt("some_session"),
        phone="+1234567890",
        username="testuser",
        user_id=987654,
        display_name="Test",
        status=AccountStatus.CONNECTED
    )
    mock_account_repo.get.return_value = account

    # Mock message with video document
    mock_msg = MagicMock()
    mock_msg.id = 999
    mock_msg.message = "Test video"
    mock_msg.text = None
    mock_msg.date = datetime(2026, 6, 20, 12, 0, 0)

    # Use real MessageMediaDocument spec
    mock_media = MagicMock(spec=MessageMediaDocument)
    mock_doc = MagicMock()
    mock_doc.mime_type = "video/mp4"
    mock_doc.size = 1024000

    # Create proper attribute mocks
    file_attr = MagicMock(spec=DocumentAttributeFilename)
    file_attr.file_name = "video.mp4"

    video_attr = MagicMock(spec=DocumentAttributeVideo)
    video_attr.duration = 60

    mock_doc.attributes = [file_attr, video_attr]
    mock_media.document = mock_doc
    mock_msg.media = mock_media

    mock_msg.reactions = MagicMock()
    mock_msg.reactions.results = [
        MagicMock(reaction=MagicMock(emoticon="👍"), count=5)
    ]
    mock_msg.replies = MagicMock()
    mock_msg.replies.replies = 3

    async def mock_iter_messages(*args, **kwargs):
        yield mock_msg

    mock_client.iter_messages = mock_iter_messages

    def mock_client_factory(session, api_id, api_hash):
        return mock_client

    service = TelegramService(
        account_repo=mock_account_repo,
        client_factory=mock_client_factory
    )
    service.client = mock_client

    from app.telegram.dtos import ChannelDTO, TopicDTO
    channel_dto = ChannelDTO(
        tg_id=123456,
        title="Test Channel",
        username="testchan",
        is_forum=True,
        photo_b64=None,
        raw={}
    )
    topic_dto = TopicDTO(
        tg_topic_id=1,
        title="General",
        channel_tg_id=123456,
        raw={}
    )

    media_list = []
    async for media in service.iter_media(channel_dto, topic_dto):
        media_list.append(media)

    assert len(media_list) == 1
    media = media_list[0]
    assert media.tg_msg_id == 999
    assert media.file_name == "video.mp4"
    assert media.mime == "video/mp4"
    assert media.size_bytes == 1024000


@pytest.mark.asyncio
async def test_fetch_thumb_returns_base64(mock_client, mock_account_repo):
    """fetch_thumb(message) → base64 string of smallest thumbnail."""
    account = Account(
        id=1,
        api_id_enc=encrypt("123456"),
        api_hash_enc=encrypt("abcdef123456"),
        session_enc=encrypt("some_session"),
        phone="+1234567890",
        username="testuser",
        user_id=987654,
        display_name="Test",
        status=AccountStatus.CONNECTED
    )
    mock_account_repo.get.return_value = account

    mock_msg = MagicMock()
    mock_client.download_media = AsyncMock(return_value=b"thumb_bytes")

    def mock_client_factory(session, api_id, api_hash):
        return mock_client

    service = TelegramService(
        account_repo=mock_account_repo,
        client_factory=mock_client_factory
    )
    service.client = mock_client

    thumb_b64 = await service.fetch_thumb(mock_msg)

    import base64
    expected = base64.b64encode(b"thumb_bytes").decode("utf-8")
    assert thumb_b64 == expected


@pytest.mark.asyncio
async def test_fetch_reactions_counts(mock_client, mock_account_repo):
    """fetch_reactions(message) → {emoji: count} dict."""
    account = Account(
        id=1,
        api_id_enc=encrypt("123456"),
        api_hash_enc=encrypt("abcdef123456"),
        session_enc=encrypt("some_session"),
        phone="+1234567890",
        username="testuser",
        user_id=987654,
        display_name="Test",
        status=AccountStatus.CONNECTED
    )
    mock_account_repo.get.return_value = account

    mock_msg = MagicMock()
    mock_msg.reactions = MagicMock()
    mock_msg.reactions.results = [
        MagicMock(reaction=MagicMock(emoticon="👍"), count=5),
        MagicMock(reaction=MagicMock(emoticon="❤️"), count=3),
    ]

    def mock_client_factory(session, api_id, api_hash):
        return mock_client

    service = TelegramService(
        account_repo=mock_account_repo,
        client_factory=mock_client_factory
    )
    service.client = mock_client

    reactions = await service.fetch_reactions(mock_msg)

    assert reactions == {"👍": 5, "❤️": 3}


@pytest.mark.asyncio
async def test_fetch_comment_count(mock_client, mock_account_repo):
    """fetch_comment_count(message) → int from message.replies.replies."""
    account = Account(
        id=1,
        api_id_enc=encrypt("123456"),
        api_hash_enc=encrypt("abcdef123456"),
        session_enc=encrypt("some_session"),
        phone="+1234567890",
        username="testuser",
        user_id=987654,
        display_name="Test",
        status=AccountStatus.CONNECTED
    )
    mock_account_repo.get.return_value = account

    mock_msg = MagicMock()
    mock_msg.replies = MagicMock()
    mock_msg.replies.replies = 7

    def mock_client_factory(session, api_id, api_hash):
        return mock_client

    service = TelegramService(
        account_repo=mock_account_repo,
        client_factory=mock_client_factory
    )
    service.client = mock_client

    count = await service.fetch_comment_count(mock_msg)

    assert count == 7


# ============================================================================
# Task 6: Download with semaphore and progress callback tests
# ============================================================================

@pytest.mark.asyncio
async def test_download_respects_semaphore(mock_client, mock_account_repo, tmp_path):
    """download() respects max_concurrent_downloads semaphore."""
    account = Account(
        id=1,
        api_id_enc=encrypt("123456"),
        api_hash_enc=encrypt("abcdef123456"),
        session_enc=encrypt("some_session"),
        phone="+1234567890",
        username="testuser",
        user_id=987654,
        display_name="Test",
        status=AccountStatus.CONNECTED
    )
    mock_account_repo.get.return_value = account

    # Mock message with document
    mock_msg = MagicMock()
    mock_msg.media = MagicMock()
    mock_msg.media.document = MagicMock()
    mock_msg.media.document.size = 1024000

    def mock_client_factory(session, api_id, api_hash):
        return mock_client

    service = TelegramService(
        account_repo=mock_account_repo,
        client_factory=mock_client_factory,
        max_concurrent_downloads=2
    )
    service.client = mock_client

    # Verify semaphore is created with max_concurrent_downloads=2
    assert service.download_semaphore._value == 2

    # Mock fast_telethon.download_file
    from unittest.mock import patch
    with patch("app.telegram.service.download_file", new_callable=AsyncMock) as mock_download:
        mock_download.return_value = b"downloaded_data"

        dest_path = str(tmp_path / "test.bin")

        # Call download (should not raise)
        result = await service.download(mock_msg, dest_path)

        assert result == dest_path
        mock_download.assert_called_once()


@pytest.mark.asyncio
async def test_download_forwards_progress_callback(mock_client, mock_account_repo, tmp_path):
    """download() calls on_progress(bytes_done, bytes_total)."""
    account = Account(
        id=1,
        api_id_enc=encrypt("123456"),
        api_hash_enc=encrypt("abcdef123456"),
        session_enc=encrypt("some_session"),
        phone="+1234567890",
        username="testuser",
        user_id=987654,
        display_name="Test",
        status=AccountStatus.CONNECTED
    )
    mock_account_repo.get.return_value = account

    mock_msg = MagicMock()
    mock_msg.media = MagicMock()
    mock_msg.media.document = MagicMock()
    mock_msg.media.document.size = 1024000

    def mock_client_factory(session, api_id, api_hash):
        return mock_client

    service = TelegramService(
        account_repo=mock_account_repo,
        client_factory=mock_client_factory
    )
    service.client = mock_client

    progress_calls = []

    def on_progress(bytes_done, bytes_total):
        progress_calls.append((bytes_done, bytes_total))

    dest_path = str(tmp_path / "test.bin")

    from unittest.mock import patch

    with patch("app.telegram.service.download_file", new_callable=AsyncMock) as mock_download:
        async def mock_download_impl(client, doc, f, progress_callback):
            if progress_callback:
                progress_callback(512000, 1024000)
                progress_callback(1024000, 1024000)
            f.write(b"x" * 1024000)
            return f

        mock_download.side_effect = mock_download_impl

        await service.download(mock_msg, dest_path, on_progress=on_progress)

        # Verify progress was called
        assert len(progress_calls) == 2
        assert progress_calls[0] == (512000, 1024000)
        assert progress_calls[1] == (1024000, 1024000)


# ============================================================================
# Task 7: Rate-limit handling (FloodWaitError catch, sleep, emit Event)
# ============================================================================

@pytest.mark.asyncio
async def test_list_channels_catches_flood_wait_sleeps_emits(mock_client, mock_account_repo):
    """list_channels catches FloodWaitError, sleeps, emits event via event_sink."""
    from telethon.errors import FloodWaitError
    from unittest.mock import patch

    account = Account(
        id=1,
        api_id_enc=encrypt("123456"),
        api_hash_enc=encrypt("abcdef123456"),
        session_enc=encrypt("some_session"),
        phone="+1234567890",
        username="testuser",
        user_id=987654,
        display_name="Test",
        status=AccountStatus.CONNECTED
    )
    mock_account_repo.get.return_value = account

    # Mock event_sink to track calls
    mock_event_sink = AsyncMock()

    # Mock client.get_dialogs to raise FloodWaitError with 5 seconds
    flood_error = FloodWaitError(request=None, capture=5)
    mock_client.get_dialogs = AsyncMock(side_effect=flood_error)

    def mock_client_factory(session, api_id, api_hash):
        return mock_client

    service = TelegramService(
        account_repo=mock_account_repo,
        client_factory=mock_client_factory,
        event_sink=mock_event_sink
    )
    service.client = mock_client

    # Patch asyncio.sleep to verify it's called with the right duration
    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        channels = await service.list_channels()

        # Should return empty list (graceful degradation)
        assert channels == []
        # Should have slept for 5 seconds
        mock_sleep.assert_called_once_with(5)
        # Should have emitted an event
        mock_event_sink.assert_called_once()
        args = mock_event_sink.call_args[0]
        assert args[0] == "warning"
        assert args[1] == "sync"
        assert "Rate limit" in args[2]
        assert "5" in args[2]


@pytest.mark.asyncio
async def test_iter_media_catches_flood_wait_sleeps_emits(mock_client, mock_account_repo):
    """iter_media catches FloodWaitError, sleeps, emits event via event_sink."""
    from telethon.errors import FloodWaitError
    from unittest.mock import patch

    account = Account(
        id=1,
        api_id_enc=encrypt("123456"),
        api_hash_enc=encrypt("abcdef123456"),
        session_enc=encrypt("some_session"),
        phone="+1234567890",
        username="testuser",
        user_id=987654,
        display_name="Test",
        status=AccountStatus.CONNECTED
    )
    mock_account_repo.get.return_value = account

    # Mock event_sink
    mock_event_sink = AsyncMock()

    # Mock client.iter_messages as async generator that raises on iteration
    flood_error = FloodWaitError(request=None, capture=3)

    async def mock_iter_messages(*args, **kwargs):
        if False:
            yield
        raise flood_error

    mock_client.iter_messages = mock_iter_messages

    def mock_client_factory(session, api_id, api_hash):
        return mock_client

    service = TelegramService(
        account_repo=mock_account_repo,
        client_factory=mock_client_factory,
        event_sink=mock_event_sink
    )
    service.client = mock_client

    from app.telegram.dtos import ChannelDTO, TopicDTO
    channel_dto = ChannelDTO(
        tg_id=123456,
        title="Test Channel",
        username="testchan",
        is_forum=False,
        photo_b64=None,
        raw={}
    )

    # Patch asyncio.sleep to verify it's called with the right duration
    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        media_list = []
        async for media in service.iter_media(channel_dto):
            media_list.append(media)

        # Should yield nothing (graceful degradation)
        assert media_list == []
        # Should have slept for 3 seconds
        mock_sleep.assert_called_once_with(3)
        # Should have emitted an event
        mock_event_sink.assert_called_once()
        args = mock_event_sink.call_args[0]
        assert args[0] == "warning"
        assert args[1] == "sync"
        assert "Rate limit" in args[2]
        assert "3" in args[2]


@pytest.mark.asyncio
async def test_list_channels_flood_wait_no_event_sink(mock_client, mock_account_repo):
    """list_channels handles FloodWaitError gracefully even without event_sink."""
    from telethon.errors import FloodWaitError
    from unittest.mock import patch

    account = Account(
        id=1,
        api_id_enc=encrypt("123456"),
        api_hash_enc=encrypt("abcdef123456"),
        session_enc=encrypt("some_session"),
        phone="+1234567890",
        username="testuser",
        user_id=987654,
        display_name="Test",
        status=AccountStatus.CONNECTED
    )
    mock_account_repo.get.return_value = account

    # No event_sink (default None)
    flood_error = FloodWaitError(request=None, capture=2)
    mock_client.get_dialogs = AsyncMock(side_effect=flood_error)

    def mock_client_factory(session, api_id, api_hash):
        return mock_client

    service = TelegramService(
        account_repo=mock_account_repo,
        client_factory=mock_client_factory
    )
    service.client = mock_client

    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        channels = await service.list_channels()

        # Should return empty list
        assert channels == []
        # Should have slept
        mock_sleep.assert_called_once_with(2)


@pytest.mark.asyncio
async def test_set_credentials_builds_client_and_enables_login(mock_client, mock_account_repo):
    """set_credentials stores api creds and builds a client so start_login works."""
    account = Account(
        id=1,
        api_id_enc=encrypt("123456"),
        api_hash_enc=encrypt("abcdef"),
        session_enc=None,
        status=AccountStatus.DISCONNECTED,
    )
    mock_account_repo.upsert_credentials = AsyncMock(return_value=account)
    mock_account_repo.get.return_value = account

    captured = {}

    def factory(session, api_id, api_hash):
        captured["api_id"] = api_id
        captured["api_hash"] = api_hash
        return mock_client

    service = TelegramService(account_repo=mock_account_repo, client_factory=factory)

    await service.set_credentials("123456", "abcdef")

    mock_account_repo.upsert_credentials.assert_awaited_once_with("123456", "abcdef")
    assert service.client is mock_client
    assert captured == {"api_id": 123456, "api_hash": "abcdef"}

    # start_login must now succeed (no "Client not initialized")
    mock_client.send_code_request = AsyncMock(return_value=MagicMock(phone_code_hash="h"))
    await service.start_login("+1234567890")
    mock_client.send_code_request.assert_awaited_once_with("+1234567890")
