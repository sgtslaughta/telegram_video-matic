"""TDD tests for app/api/schemas.py"""
import re
import pytest
from datetime import datetime, timezone
from app.api.schemas import (
    TelegramStatusRead,
    ChannelRead,
    TopicRead,
    SubscriptionRead,
    SubscriptionCreateRequest,
    MediaItemRead,
    DownloadJobRead,
)
from app.db.models import Account, Channel, Topic, Subscription, MediaItem, DownloadJob, AccountStatus, MediaStatus, JobStatus


class TestTelegramStatusReadSecrets:
    """Verify TelegramStatusRead never exposes api_hash, session_enc, api_id_enc."""

    def test_telegram_status_serializes_from_account_orm_without_secrets(self):
        """TelegramStatusRead from Account ORM excludes all secret fields."""
        account = Account(
            id=1,
            api_id_enc="encrypted_api_id",
            api_hash_enc="encrypted_api_hash",
            session_enc="encrypted_session",
            phone="+1234567890",
            username="testuser",
            display_name="Test User",
            status=AccountStatus.CONNECTED,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        status = TelegramStatusRead.model_validate(account)
        data = status.model_dump()

        # Assert secrets are not in serialized output
        assert "api_hash_enc" not in data
        assert "session_enc" not in data
        assert "api_id_enc" not in data
        assert "api_hash" not in data
        assert "session" not in data
        assert "api_id" not in data

        # Assert permitted fields are present
        assert data["status"] == "connected"
        assert data["username"] == "testuser"
        assert data["display_name"] == "Test User"
        assert "phone" in data

    def test_telegram_status_phone_masking(self):
        """TelegramStatusRead masks phone: +1...2345."""
        account = Account(
            id=1,
            api_id_enc="x",
            api_hash_enc="y",
            phone="+1234567890",
            username="u",
            display_name="d",
            status=AccountStatus.CONNECTED,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        status = TelegramStatusRead.model_validate(account)
        # Phone should be masked as +1******7890 (first char + first char after + + 6 asterisks + last 4)
        assert status.phone == "+1******7890"

    def test_telegram_status_phone_masking_short_phone(self):
        """TelegramStatusRead handles short phone gracefully."""
        account = Account(
            id=1,
            api_id_enc="x",
            api_hash_enc="y",
            phone="+123",
            username="u",
            display_name="d",
            status=AccountStatus.CONNECTED,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        status = TelegramStatusRead.model_validate(account)
        # Short phone: return as-is
        assert status.phone == "+123"

    def test_telegram_status_null_phone(self):
        """TelegramStatusRead handles null phone."""
        account = Account(
            id=1,
            api_id_enc="x",
            api_hash_enc="y",
            phone=None,
            username="u",
            display_name="d",
            status=AccountStatus.CONNECTED,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        status = TelegramStatusRead.model_validate(account)
        assert status.phone is None


class TestChannelRead:
    """Test ChannelRead ORM serialization."""

    def test_channel_read_from_orm(self):
        """ChannelRead serializes from Channel ORM."""
        channel = Channel(
            id=1,
            tg_id=12345,
            title="My Channel",
            username="mychannel",
            is_forum=False,
            photo_b64=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        ch = ChannelRead.model_validate(channel)
        assert ch.id == 1
        assert ch.tg_id == 12345
        assert ch.title == "My Channel"
        assert ch.username == "mychannel"
        assert ch.is_forum is False


class TestTopicRead:
    """Test TopicRead ORM serialization."""

    def test_topic_read_from_orm(self):
        """TopicRead serializes from Topic ORM."""
        topic = Topic(
            id=1,
            channel_id=1,
            tg_topic_id=999,
            title="Topic Title",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        t = TopicRead.model_validate(topic)
        assert t.id == 1
        assert t.tg_topic_id == 999
        assert t.title == "Topic Title"


class TestSubscriptionRead:
    """Test SubscriptionRead ORM serialization."""

    def test_subscription_read_from_orm(self):
        """SubscriptionRead serializes from Subscription ORM."""
        sub = Subscription(
            id=1,
            channel_id=1,
            topic_id=None,
            enabled=True,
            mode="immediate",
            filter_regex=None,
            filter_mode="include",
            storage_path="/downloads",
            rename_template="%(title)s",
            season_detection=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        s = SubscriptionRead.model_validate(sub)
        assert s.id == 1
        assert s.channel_id == 1
        assert s.enabled is True
        assert s.storage_path == "/downloads"


class TestMediaItemRead:
    """Test MediaItemRead ORM serialization."""

    def test_media_item_read_from_orm(self):
        """MediaItemRead serializes from MediaItem ORM."""
        now = datetime.now(timezone.utc)
        media = MediaItem(
            id=1,
            channel_id=1,
            topic_id=None,
            subscription_id=None,
            tg_msg_id=42,
            caption="Test",
            file_name="test.mp4",
            mime="video/mp4",
            size_bytes=1024,
            duration_sec=60,
            date_posted=now,
            status=MediaStatus.PENDING,
            created_at=now,
            updated_at=now,
        )

        m = MediaItemRead.model_validate(media)
        assert m.id == 1
        assert m.tg_msg_id == 42
        assert m.file_name == "test.mp4"
        assert m.status == "pending"


class TestDownloadJobRead:
    """Test DownloadJobRead ORM serialization."""

    def test_download_job_read_from_orm(self):
        """DownloadJobRead serializes from DownloadJob ORM."""
        job = DownloadJob(
            id=1,
            media_id=1,
            status=JobStatus.RUNNING,
            progress=0.5,
            speed_bps=1000000,
            eta_sec=30,
            bytes_done=512,
            bytes_total=1024,
            attempt=1,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        j = DownloadJobRead.model_validate(job)
        assert j.id == 1
        assert j.progress == 0.5
        assert j.speed_bps == 1000000
        assert j.eta_sec == 30
        assert j.attempt == 1


class TestSubscriptionCreateRequestValidation:
    """Test regex validation in SubscriptionCreateRequest."""

    def test_valid_regex_accepted(self):
        """SubscriptionCreateRequest accepts valid regex."""
        req = SubscriptionCreateRequest(
            channel_id=1,
            enabled=True,
            storage_path="/downloads",
            rename_template="%(title)s",
            filter_regex=r".*\.mp4$",
        )
        assert req.filter_regex == r".*\.mp4$"

    def test_invalid_regex_rejected(self):
        """SubscriptionCreateRequest rejects invalid regex."""
        with pytest.raises(ValueError, match="Invalid regex"):
            SubscriptionCreateRequest(
                channel_id=1,
                enabled=True,
                storage_path="/downloads",
                rename_template="%(title)s",
                filter_regex="[invalid(regex",
            )

    def test_null_regex_accepted(self):
        """SubscriptionCreateRequest accepts null regex."""
        req = SubscriptionCreateRequest(
            channel_id=1,
            enabled=True,
            storage_path="/downloads",
            rename_template="%(title)s",
            filter_regex=None,
        )
        assert req.filter_regex is None
