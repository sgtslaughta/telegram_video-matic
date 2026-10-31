/**
 * Frontend API constants mapping to backend enums
 */
export const ACCOUNT_STATUS = {
    DISCONNECTED: "disconnected",
    WAITING_PHONE: "waiting_phone",
    WAITING_CODE: "waiting_code",
    WAITING_PASSWORD: "waiting_password",
    CONNECTED: "connected",
};
export const MEDIA_STATUS = {
    PENDING: "pending",
    DOWNLOADING: "downloading",
    DOWNLOADED: "downloaded",
    FAILED: "failed",
    PROCESSING: "processing",
    READY: "ready",
};
export const SUB_MODE = {
    IMMEDIATE: "immediate",
    SCHEDULED: "scheduled",
};
export const FILTER_MODE = {
    INCLUDE: "include",
    EXCLUDE: "exclude",
};
export const JOB_STATUS = {
    PENDING: "pending",
    DOWNLOADING: "downloading",
    COMPLETED: "completed",
    FAILED: "failed",
};
export const EVENT_LEVEL = {
    DEBUG: "debug",
    INFO: "info",
    WARNING: "warning",
    ERROR: "error",
};
