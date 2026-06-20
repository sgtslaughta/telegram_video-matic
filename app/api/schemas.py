"""Pydantic v2 schemas for API request/response models."""
from pydantic import BaseModel, ConfigDict, field_validator, Field
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
    topic_id: Optional[int] = None
    enabled: bool = True
    mode: str = "immediate"
    schedule_days: Optional[list[str]] = None
    filter_regex: Optional[str] = None
    filter_mode: str = "include"
    min_size_mb: Optional[int] = None
    max_size_mb: Optional[int] = None
    storage_path: str
    rename_template: str
    season_detection: bool = True
    retention_days: Optional[int] = None
    retention_disk_pct: Optional[int] = None
    # filter_regex is validated in the subscriptions router (-> HTTP 400),
    # not here, so a bad pattern returns 400 rather than Pydantic's 422.


class SubscriptionUpdateRequest(BaseModel):
    enabled: Optional[bool] = None
    mode: Optional[str] = None
    schedule_days: Optional[list[str]] = None
    filter_regex: Optional[str] = None
    filter_mode: Optional[str] = None
    min_size_mb: Optional[int] = None
    max_size_mb: Optional[int] = None
    storage_path: Optional[str] = None
    rename_template: Optional[str] = None
    season_detection: Optional[bool] = None
    retention_days: Optional[int] = None
    retention_disk_pct: Optional[int] = None
    # filter_regex validated in the router (-> HTTP 400), see SubscriptionCreateRequest.


class SubscriptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    channel_id: int
    topic_id: Optional[int] = None
    enabled: bool
    mode: str
    schedule_days: Optional[list[str]] = None
    filter_regex: Optional[str] = None
    filter_mode: str
    min_size_mb: Optional[int] = None
    max_size_mb: Optional[int] = None
    storage_path: str
    rename_template: str
    season_detection: bool
    retention_days: Optional[int] = None
    retention_disk_pct: Optional[int] = None
    created_at: datetime
    updated_at: datetime


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
    tg_status: TelegramStatusRead
