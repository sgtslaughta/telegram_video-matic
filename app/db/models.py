from datetime import datetime, timezone
from enum import StrEnum
from typing import Optional
from sqlalchemy import (
    ForeignKey, String, Integer, Float, Boolean, DateTime, JSON, UniqueConstraint, PrimaryKeyConstraint
)
from sqlalchemy.orm import declarative_base, Mapped, mapped_column, relationship

Base = declarative_base()


class TimestampMixin:
    """Mixin that adds created_at and updated_at columns to models."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )


# ============================================================================
# Enums (StrEnum)
# ============================================================================

class AccountStatus(StrEnum):
    DISCONNECTED = "disconnected"
    AWAITING_CODE = "awaiting_code"
    AWAITING_PASSWORD = "awaiting_password"
    CONNECTED = "connected"


class SubMode(StrEnum):
    IMMEDIATE = "immediate"
    SCHEDULED = "scheduled"


class FilterMode(StrEnum):
    INCLUDE = "include"
    EXCLUDE = "exclude"


class MediaStatus(StrEnum):
    PENDING = "pending"
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    DOWNLOADED = "downloaded"
    FAILED = "failed"
    SKIPPED = "skipped"
    PAUSED = "paused"


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    DONE = "done"
    ERROR = "error"
    CANCELED = "canceled"


class EventLevel(StrEnum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


# ============================================================================
# Models
# ============================================================================

class Setting(Base, TimestampMixin):
    """Key-value app settings (can be changed at runtime)."""
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(255), primary_key=True)
    value: Mapped[str] = mapped_column(String(4096), nullable=False)  # JSON-encoded


class Account(Base, TimestampMixin):
    """Single-row Telegram account/session."""
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    api_id_enc: Mapped[str] = mapped_column(String(1024), nullable=False)
    api_hash_enc: Mapped[str] = mapped_column(String(1024), nullable=False)
    session_enc: Mapped[Optional[str]] = mapped_column(String(4096), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default=AccountStatus.DISCONNECTED, nullable=False)


class Channel(Base, TimestampMixin):
    """Telegram channel."""
    __tablename__ = "channels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tg_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_forum: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    photo_b64: Mapped[Optional[str]] = mapped_column(String(8192), nullable=True)
    raw: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    topics = relationship("Topic", back_populates="channel")
    subscriptions = relationship("Subscription", back_populates="channel")
    media_items = relationship("MediaItem", back_populates="channel")


class Topic(Base, TimestampMixin):
    """Forum topic within a channel."""
    __tablename__ = "topics"
    __table_args__ = (
        UniqueConstraint("channel_id", "tg_topic_id", name="uq_topics_channel_topic"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id"), nullable=False)
    tg_topic_id: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    raw: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    channel = relationship("Channel", back_populates="topics")
    subscriptions = relationship("Subscription", back_populates="topic")
    media_items = relationship("MediaItem", back_populates="topic")


class Subscription(Base, TimestampMixin):
    """Radarr/Sonarr-like monitoring unit (per channel or channel+topic)."""
    __tablename__ = "subscriptions"
    __table_args__ = (
        UniqueConstraint("channel_id", "topic_id", name="uq_subscriptions_channel_topic"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id"), nullable=False)
    topic_id: Mapped[Optional[int]] = mapped_column(ForeignKey("topics.id"), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    mode: Mapped[str] = mapped_column(String(32), default=SubMode.IMMEDIATE, nullable=False)
    # Capture cadence: realtime | 1m | 5m | 15m | 30m | hourly | daily | scheduled.
    # realtime = event-driven (no polling); scheduled uses schedule_days.
    check_frequency: Mapped[Optional[str]] = mapped_column(String(16), nullable=True, default="5m")
    last_checked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    schedule_days: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    filter_regex: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    filter_mode: Mapped[str] = mapped_column(String(32), default=FilterMode.INCLUDE, nullable=False)
    min_size_mb: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_size_mb: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # Per-subscription disk quota in GB; null = unlimited. When exceeded,
    # maintenance deletes oldest downloaded files for this sub (rolling window).
    max_total_gb: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # Timeframe window: only capture media posted within [date_from, date_to].
    # date_from set + date_to null = ongoing (catch up + keep going); both null = all.
    date_from: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    date_to: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    rename_template: Mapped[str] = mapped_column(String(1024), nullable=False)
    season_detection: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    jellyfin_metadata: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    retention_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    retention_disk_pct: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    channel = relationship("Channel", back_populates="subscriptions")
    topic = relationship("Topic", back_populates="subscriptions")
    media_items = relationship("MediaItem", back_populates="subscription")
    events = relationship("Event", back_populates="subscription")


class MediaItem(Base, TimestampMixin):
    """One Telegram media message tracked for download."""
    __tablename__ = "media_items"
    __table_args__ = (
        UniqueConstraint("channel_id", "tg_msg_id", name="uq_media_items_channel_msg"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id"), nullable=False)
    topic_id: Mapped[Optional[int]] = mapped_column(ForeignKey("topics.id"), nullable=True)
    subscription_id: Mapped[Optional[int]] = mapped_column(ForeignKey("subscriptions.id"), nullable=True)
    tg_msg_id: Mapped[int] = mapped_column(Integer, nullable=False)
    caption: Mapped[Optional[str]] = mapped_column(String(4096), nullable=True)
    file_name: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    mime: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    duration_sec: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    date_posted: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    thumb_b64: Mapped[Optional[str]] = mapped_column(String(8192), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default=MediaStatus.PENDING, nullable=False)
    local_path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    # Quick content fingerprint (size+head+tail) for dedup / renamed-file relink.
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    downloaded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    reactions: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    comments_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    raw: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    channel = relationship("Channel", back_populates="media_items")
    topic = relationship("Topic", back_populates="media_items")
    subscription = relationship("Subscription", back_populates="media_items")
    download_job = relationship("DownloadJob", back_populates="media", uselist=False)
    media_tags = relationship("MediaTag", back_populates="media")
    events = relationship("Event", back_populates="media")


class DownloadJob(Base, TimestampMixin):
    """Active queue + retry history."""
    __tablename__ = "download_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    media_id: Mapped[int] = mapped_column(ForeignKey("media_items.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default=JobStatus.QUEUED, nullable=False)
    progress: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    speed_bps: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    eta_sec: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    bytes_done: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    bytes_total: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    attempt: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    error: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    media = relationship("MediaItem", back_populates="download_job")


class Tag(Base, TimestampMixin):
    """Tag for categorizing media."""
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    media_tags = relationship("MediaTag", back_populates="tag")


class MediaTag(Base, TimestampMixin):
    """Association between MediaItem and Tag."""
    __tablename__ = "media_tags"
    __table_args__ = (
        PrimaryKeyConstraint("media_id", "tag_id", name="pk_media_tags"),
    )

    media_id: Mapped[int] = mapped_column(ForeignKey("media_items.id"), nullable=False)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id"), nullable=False)

    media = relationship("MediaItem", back_populates="media_tags")
    tag = relationship("Tag", back_populates="media_tags")


class Plugin(Base, TimestampMixin):
    """Plugin framework stub."""
    __tablename__ = "plugins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    installed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )


class Event(Base, TimestampMixin):
    """Activity feed + audit log."""
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    level: Mapped[str] = mapped_column(String(32), nullable=False)
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    subscription_id: Mapped[Optional[int]] = mapped_column(ForeignKey("subscriptions.id"), nullable=True)
    media_id: Mapped[Optional[int]] = mapped_column(ForeignKey("media_items.id"), nullable=True)
    message: Mapped[str] = mapped_column(String(1024), nullable=False)

    subscription = relationship("Subscription", back_populates="events")
    media = relationship("MediaItem", back_populates="events")
