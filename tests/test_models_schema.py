import pytest
from datetime import datetime
from app.db.models import (
    TimestampMixin, Setting, Account, Channel, Topic, Subscription, MediaItem,
    DownloadJob, Tag, MediaTag, Plugin, Event,
    AccountStatus, SubMode, FilterMode, MediaStatus, JobStatus, EventLevel,
)


def test_timestamp_mixin_has_created_at_updated_at():
    """TimestampMixin provides created_at and updated_at fields."""
    class Dummy(TimestampMixin):
        pass

    obj = Dummy()
    assert hasattr(obj, 'created_at')
    assert hasattr(obj, 'updated_at')


def test_setting_model():
    """Setting model has key (pk), value (JSON), created_at, updated_at."""
    assert hasattr(Setting, 'key')
    assert hasattr(Setting, 'value')
    assert hasattr(Setting, 'created_at')


def test_account_model():
    """Account model has all required encrypted fields."""
    assert hasattr(Account, 'id')
    assert hasattr(Account, 'api_id_enc')
    assert hasattr(Account, 'api_hash_enc')
    assert hasattr(Account, 'session_enc')
    assert hasattr(Account, 'phone')
    assert hasattr(Account, 'username')
    assert hasattr(Account, 'user_id')
    assert hasattr(Account, 'display_name')
    assert hasattr(Account, 'status')
    assert hasattr(Account, 'created_at')


def test_channel_model():
    """Channel model has tg_id (unique), title, username, is_forum, photo_b64, raw."""
    assert hasattr(Channel, 'id')
    assert hasattr(Channel, 'tg_id')
    assert hasattr(Channel, 'title')
    assert hasattr(Channel, 'username')
    assert hasattr(Channel, 'is_forum')
    assert hasattr(Channel, 'photo_b64')
    assert hasattr(Channel, 'raw')


def test_topic_model():
    """Topic model has channel_id (fk), tg_topic_id, title, raw."""
    assert hasattr(Topic, 'id')
    assert hasattr(Topic, 'channel_id')
    assert hasattr(Topic, 'tg_topic_id')
    assert hasattr(Topic, 'title')
    assert hasattr(Topic, 'raw')


def test_subscription_model():
    """Subscription has channel_id, topic_id, mode, schedule_days, filter fields, storage_path, rename_template."""
    assert hasattr(Subscription, 'id')
    assert hasattr(Subscription, 'channel_id')
    assert hasattr(Subscription, 'topic_id')
    assert hasattr(Subscription, 'enabled')
    assert hasattr(Subscription, 'mode')
    assert hasattr(Subscription, 'schedule_days')
    assert hasattr(Subscription, 'filter_regex')
    assert hasattr(Subscription, 'filter_mode')
    assert hasattr(Subscription, 'min_size_mb')
    assert hasattr(Subscription, 'max_size_mb')
    assert hasattr(Subscription, 'storage_path')
    assert hasattr(Subscription, 'rename_template')
    assert hasattr(Subscription, 'season_detection')
    assert hasattr(Subscription, 'retention_days')
    assert hasattr(Subscription, 'retention_disk_pct')


def test_media_item_model():
    """MediaItem has channel_id, topic_id, subscription_id, tg_msg_id, status, etc."""
    assert hasattr(MediaItem, 'id')
    assert hasattr(MediaItem, 'channel_id')
    assert hasattr(MediaItem, 'topic_id')
    assert hasattr(MediaItem, 'subscription_id')
    assert hasattr(MediaItem, 'tg_msg_id')
    assert hasattr(MediaItem, 'caption')
    assert hasattr(MediaItem, 'file_name')
    assert hasattr(MediaItem, 'mime')
    assert hasattr(MediaItem, 'size_bytes')
    assert hasattr(MediaItem, 'duration_sec')
    assert hasattr(MediaItem, 'date_posted')
    assert hasattr(MediaItem, 'thumb_b64')
    assert hasattr(MediaItem, 'status')
    assert hasattr(MediaItem, 'local_path')
    assert hasattr(MediaItem, 'downloaded_at')
    assert hasattr(MediaItem, 'reactions')
    assert hasattr(MediaItem, 'comments_count')
    assert hasattr(MediaItem, 'raw')


def test_download_job_model():
    """DownloadJob has media_id (fk), status, progress, speed_bps, eta_sec, bytes_done, bytes_total, attempt, error, timestamps."""
    assert hasattr(DownloadJob, 'id')
    assert hasattr(DownloadJob, 'media_id')
    assert hasattr(DownloadJob, 'status')
    assert hasattr(DownloadJob, 'progress')
    assert hasattr(DownloadJob, 'speed_bps')
    assert hasattr(DownloadJob, 'eta_sec')
    assert hasattr(DownloadJob, 'bytes_done')
    assert hasattr(DownloadJob, 'bytes_total')
    assert hasattr(DownloadJob, 'attempt')
    assert hasattr(DownloadJob, 'error')
    assert hasattr(DownloadJob, 'started_at')
    assert hasattr(DownloadJob, 'finished_at')


def test_tag_model():
    """Tag has id (pk), name (unique)."""
    assert hasattr(Tag, 'id')
    assert hasattr(Tag, 'name')


def test_media_tag_model():
    """MediaTag has media_id (fk), tag_id (fk), composite pk."""
    assert hasattr(MediaTag, 'media_id')
    assert hasattr(MediaTag, 'tag_id')


def test_plugin_model():
    """Plugin has name (unique), version, enabled, config, installed_at."""
    assert hasattr(Plugin, 'id')
    assert hasattr(Plugin, 'name')
    assert hasattr(Plugin, 'version')
    assert hasattr(Plugin, 'enabled')
    assert hasattr(Plugin, 'config')
    assert hasattr(Plugin, 'installed_at')


def test_event_model():
    """Event has level, kind, subscription_id, media_id, message."""
    assert hasattr(Event, 'id')
    assert hasattr(Event, 'level')
    assert hasattr(Event, 'kind')
    assert hasattr(Event, 'subscription_id')
    assert hasattr(Event, 'media_id')
    assert hasattr(Event, 'message')


def test_enums_exist():
    """All required StrEnums are defined."""
    assert AccountStatus.DISCONNECTED
    assert AccountStatus.AWAITING_CODE
    assert AccountStatus.AWAITING_PASSWORD
    assert AccountStatus.CONNECTED

    assert SubMode.IMMEDIATE
    assert SubMode.SCHEDULED

    assert FilterMode.INCLUDE
    assert FilterMode.EXCLUDE

    assert MediaStatus.PENDING
    assert MediaStatus.QUEUED
    assert MediaStatus.DOWNLOADING
    assert MediaStatus.DOWNLOADED
    assert MediaStatus.FAILED
    assert MediaStatus.SKIPPED

    assert JobStatus.QUEUED
    assert JobStatus.RUNNING
    assert JobStatus.DONE
    assert JobStatus.ERROR
    assert JobStatus.CANCELED

    assert EventLevel.INFO
    assert EventLevel.SUCCESS
    assert EventLevel.WARNING
    assert EventLevel.ERROR
