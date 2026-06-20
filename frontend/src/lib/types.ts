/**
 * Frontend API types mirroring backend schemas.py
 * All field names must remain snake_case to match API exactly.
 */

// ============================================================================
// Enums
// ============================================================================

export enum AccountStatus {
  DISCONNECTED = "disconnected",
  WAITING_PHONE = "waiting_phone",
  WAITING_CODE = "awaiting_code",
  WAITING_PASSWORD = "awaiting_password",
  CONNECTED = "connected",
}

export enum MediaStatus {
  PENDING = "pending",
  DOWNLOADING = "downloading",
  DOWNLOADED = "downloaded",
  FAILED = "failed",
  PROCESSING = "processing",
  READY = "ready",
}

export enum SubMode {
  IMMEDIATE = "immediate",
  SCHEDULED = "scheduled",
}

export enum FilterMode {
  INCLUDE = "include",
  EXCLUDE = "exclude",
}

export enum JobStatus {
  PENDING = "pending",
  DOWNLOADING = "downloading",
  COMPLETED = "completed",
  FAILED = "failed",
}

export enum EventLevel {
  DEBUG = "debug",
  INFO = "info",
  WARNING = "warning",
  ERROR = "error",
}

// ============================================================================
// Auth
// ============================================================================

export interface LoginRequest {
  password: string;
}

export interface AuthMeRead {
  authenticated: boolean;
  password_set: boolean;
}

// ============================================================================
// Telegram
// ============================================================================

export interface TelegramStatusRead {
  status: string;
  configured?: boolean;
  username?: string | null;
  display_name?: string | null;
  phone?: string | null;
}

export interface TelegramPhoneRequest {
  phone: string;
}

export interface TelegramCodeRequest {
  code: string;
}

export interface TelegramPasswordRequest {
  password: string;
}

// ============================================================================
// Channel / Topic
// ============================================================================

export interface TopicRead {
  id: number;
  tg_topic_id: number;
  title: string;
}

export interface ChannelRead {
  id: number;
  tg_id: number;
  title: string;
  username?: string | null;
  is_forum: boolean;
  photo_b64?: string | null;
}

// ============================================================================
// Subscription
// ============================================================================

export interface SubscriptionCreateRequest {
  channel_id: number;
  topic_id?: number | null;
  enabled?: boolean;
  mode?: string;
  schedule_days?: string[] | null;
  filter_regex?: string | null;
  filter_mode?: string;
  min_size_mb?: number | null;
  max_size_mb?: number | null;
  storage_path: string;
  rename_template: string;
  season_detection?: boolean;
  retention_days?: number | null;
  retention_disk_pct?: number | null;
}

export interface SubscriptionUpdateRequest {
  enabled?: boolean | null;
  mode?: string | null;
  schedule_days?: string[] | null;
  filter_regex?: string | null;
  filter_mode?: string | null;
  min_size_mb?: number | null;
  max_size_mb?: number | null;
  storage_path?: string | null;
  rename_template?: string | null;
  season_detection?: boolean | null;
  retention_days?: number | null;
  retention_disk_pct?: number | null;
}

export interface SubscriptionRead {
  id: number;
  channel_id: number;
  topic_id?: number | null;
  enabled: boolean;
  mode: string;
  schedule_days?: string[] | null;
  filter_regex?: string | null;
  filter_mode: string;
  min_size_mb?: number | null;
  max_size_mb?: number | null;
  storage_path: string;
  rename_template: string;
  season_detection: boolean;
  retention_days?: number | null;
  retention_disk_pct?: number | null;
  created_at: string; // ISO datetime
  updated_at: string; // ISO datetime
}

// ============================================================================
// Media
// ============================================================================

export interface MediaItemRead {
  id: number;
  channel_id: number;
  topic_id?: number | null;
  subscription_id?: number | null;
  tg_msg_id: number;
  caption?: string | null;
  file_name?: string | null;
  mime?: string | null;
  size_bytes?: number | null;
  duration_sec?: number | null;
  date_posted: string; // ISO datetime
  thumb_b64?: string | null;
  status: string;
  local_path?: string | null;
  downloaded_at?: string | null; // ISO datetime
  reactions?: Record<string, unknown> | null;
  comments_count?: number | null;
  created_at: string; // ISO datetime
  updated_at: string; // ISO datetime
}

export interface MediaDownloadRequest {
  // Empty POST body; media_id in path
}

export interface MediaRequeueRequest {
  // Empty POST body; media_id in path
}

// ============================================================================
// Download Job
// ============================================================================

export interface DownloadJobRead {
  id: number;
  media_id: number;
  status: string;
  progress: number;
  speed_bps?: number | null;
  eta_sec?: number | null;
  bytes_done: number;
  bytes_total?: number | null;
  attempt: number;
  error?: string | null;
  started_at?: string | null; // ISO datetime
  finished_at?: string | null; // ISO datetime
}

// ============================================================================
// Settings
// ============================================================================

export interface SettingRead {
  key: string;
  value: string; // JSON stringified
}

export interface SettingPatchRequest {
  poll_interval_sec?: number | null;
  retention_days?: number | null;
  retention_disk_pct?: number | null;
  max_concurrent_downloads?: number | null;
  theme?: string | null;
}

// ============================================================================
// Events
// ============================================================================

export interface EventRead {
  id: number;
  level: string;
  kind: string;
  subscription_id?: number | null;
  media_id?: number | null;
  message: string;
  created_at: string; // ISO datetime
}

// ============================================================================
// Plugins
// ============================================================================

export interface PluginRead {
  id: number;
  name: string;
  version: string;
  enabled: boolean;
  config?: Record<string, unknown> | null;
  installed_at: string; // ISO datetime
}

export interface PluginPatchRequest {
  enabled?: boolean | null;
  config?: Record<string, unknown> | null;
}

// ============================================================================
// WebSocket
// ============================================================================

export interface WSMessage {
  kind: string;
  data: Record<string, unknown>;
}

export interface WSSnapshot {
  active_downloads: DownloadJobRead[];
  tg_status?: TelegramStatusRead | null;
}

// ============================================================================
// Utility Types
// ============================================================================

export interface ApiError {
  detail: string;
  status: number;
}
