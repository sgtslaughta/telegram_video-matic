"""Pydantic v2 schemas for API request/response models."""
from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional
from datetime import datetime


# ============================================================================
# Auth
# ============================================================================

class LoginRequest(BaseModel):
    password: str


class AuthMeRead(BaseModel):
    authenticated: bool
    password_set: bool


# ============================================================================
# Telegram status (secret-masked read-only)
# ============================================================================

class TelegramStatusRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    status: str
    configured: bool = False
    username: Optional[str] = None
    display_name: Optional[str] = None
    phone: Optional[str] = None

    @field_validator("phone", mode="before")
    @classmethod
    def mask_phone(cls, v):
        if v and len(v) > 5:
            return f"+{v[1]}" + "*" * (len(v) - 5) + v[-4:]
        return v


# ============================================================================
# Telegram login flow
# ============================================================================

class TelegramCredentialsRequest(BaseModel):
    api_id: str
    api_hash: str

    @field_validator("api_id")
    @classmethod
    def api_id_numeric(cls, v):
        if not str(v).strip().isdigit():
            raise ValueError("api_id must be numeric")
        return str(v).strip()

    @field_validator("api_hash")
    @classmethod
    def api_hash_present(cls, v):
        if not str(v).strip():
            raise ValueError("api_hash is required")
        return str(v).strip()


class TelegramPhoneRequest(BaseModel):
    phone: str


class TelegramCodeRequest(BaseModel):
    code: str


class TelegramPasswordRequest(BaseModel):
    password: str


# ============================================================================
# Channel / Topic
# ============================================================================

class TopicRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    tg_topic_id: int
    title: str


class ChannelRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    tg_id: int
    title: str
    username: Optional[str] = None
    is_forum: bool
    photo_b64: Optional[str] = None


# ============================================================================
# Subscription CRUD
# ============================================================================

class SubscriptionCreateRequest(BaseModel):
    channel_id: int
    name: Optional[str] = None
    topic_id: Optional[int] = None
    enabled: bool = True
    mode: str = "immediate"
    check_frequency: Optional[str] = "5m"
    schedule_days: Optional[list[str]] = None
    filter_regex: Optional[str] = None
    filter_mode: str = "include"
    min_size_mb: Optional[int] = None
    max_size_mb: Optional[int] = None
    max_total_gb: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    storage_path: str
    rename_template: str
    season_detection: bool = True
    jellyfin_metadata: bool = False
    retention_days: Optional[int] = None
    retention_disk_pct: Optional[int] = None
    # filter_regex is validated in the subscriptions router (-> HTTP 400),
    # not here, so a bad pattern returns 400 rather than Pydantic's 422.


class SubscriptionUpdateRequest(BaseModel):
    name: Optional[str] = None
    enabled: Optional[bool] = None
    mode: Optional[str] = None
    check_frequency: Optional[str] = None
    schedule_days: Optional[list[str]] = None
    filter_regex: Optional[str] = None
    filter_mode: Optional[str] = None
    min_size_mb: Optional[int] = None
    max_size_mb: Optional[int] = None
    max_total_gb: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    storage_path: Optional[str] = None
    rename_template: Optional[str] = None
    season_detection: Optional[bool] = None
    jellyfin_metadata: Optional[bool] = None
    retention_days: Optional[int] = None
    retention_disk_pct: Optional[int] = None
    # filter_regex validated in the router (-> HTTP 400), see SubscriptionCreateRequest.


class SubscriptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: Optional[str] = None
    channel_id: int
    channel_title: Optional[str] = None
    topic_id: Optional[int] = None
    topic_title: Optional[str] = None
    enabled: bool
    mode: str
    check_frequency: Optional[str] = None
    schedule_days: Optional[list[str]] = None
    filter_regex: Optional[str] = None
    filter_mode: str
    min_size_mb: Optional[int] = None
    max_size_mb: Optional[int] = None
    max_total_gb: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    storage_path: str
    rename_template: str
    season_detection: bool
    jellyfin_metadata: bool = False
    retention_days: Optional[int] = None
    retention_disk_pct: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    @field_validator("jellyfin_metadata", mode="before")
    @classmethod
    def _default_bool(cls, v):
        return bool(v) if v is not None else False


# ============================================================================
# Media
# ============================================================================

class MediaItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    channel_id: int
    topic_id: Optional[int] = None
    subscription_id: Optional[int] = None
    tg_msg_id: int
    caption: Optional[str] = None
    file_name: Optional[str] = None
    mime: Optional[str] = None
    size_bytes: Optional[int] = None
    duration_sec: Optional[int] = None
    date_posted: datetime
    thumb_b64: Optional[str] = None
    status: str
    local_path: Optional[str] = None
    downloaded_at: Optional[datetime] = None
    reactions: Optional[dict] = None
    comments_count: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    @field_validator("duration_sec", mode="before")
    @classmethod
    def _floor_duration(cls, v):
        # Telethon durations can be float; the column/schema is int.
        return int(v) if v is not None else v


class MediaDownloadRequest(BaseModel):
    pass  # POST body empty; media_id in path


class MediaRequeueRequest(BaseModel):
    pass  # POST body empty; media_id in path


# ============================================================================
# Download Job
# ============================================================================

class DownloadJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    media_id: int
    file_name: Optional[str] = None  # enriched from the media item for display
    status: str
    progress: float
    speed_bps: Optional[int] = None
    eta_sec: Optional[int] = None
    bytes_done: int
    bytes_total: Optional[int] = None
    attempt: int
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None


# ============================================================================
# Settings
# ============================================================================

class SettingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    key: str
    value: str  # JSON stringified


class SettingPatchRequest(BaseModel):
    poll_interval_sec: Optional[int] = None
    retention_days: Optional[int] = None
    retention_disk_pct: Optional[int] = None
    max_concurrent_downloads: Optional[int] = None
    theme: Optional[str] = None


# ============================================================================
# Events
# ============================================================================

class EventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    level: str
    kind: str
    subscription_id: Optional[int] = None
    media_id: Optional[int] = None
    message: str
    created_at: datetime


# ============================================================================
# Plugins
# ============================================================================

class PluginRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    version: str
    enabled: bool
    config: Optional[dict] = None
    installed_at: datetime


class PluginPatchRequest(BaseModel):
    enabled: Optional[bool] = None
    config: Optional[dict] = None


# ============================================================================
# WebSocket
# ============================================================================

class WSMessage(BaseModel):
    kind: str  # download_progress, media_status, event, tg_status
    data: dict


class WSSnapshot(BaseModel):
    active_downloads: list[DownloadJobRead]
    tg_status: Optional[TelegramStatusRead] = None
