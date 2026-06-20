/**
 * Frontend API constants mapping to backend enums
 */

export const ACCOUNT_STATUS = {
  DISCONNECTED: "disconnected",
  WAITING_PHONE: "waiting_phone",
  WAITING_CODE: "waiting_code",
  WAITING_PASSWORD: "waiting_password",
  CONNECTED: "connected",
} as const;

export const MEDIA_STATUS = {
  PENDING: "pending",
  DOWNLOADING: "downloading",
  DOWNLOADED: "downloaded",
  FAILED: "failed",
  PROCESSING: "processing",
  READY: "ready",
} as const;

export const SUB_MODE = {
  IMMEDIATE: "immediate",
  SCHEDULED: "scheduled",
} as const;

export const FILTER_MODE = {
  INCLUDE: "include",
  EXCLUDE: "exclude",
} as const;

export const JOB_STATUS = {
  PENDING: "pending",
  DOWNLOADING: "downloading",
  COMPLETED: "completed",
  FAILED: "failed",
} as const;

export const EVENT_LEVEL = {
  DEBUG: "debug",
  INFO: "info",
  WARNING: "warning",
  ERROR: "error",
} as const;
