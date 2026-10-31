/**
 * Frontend API types mirroring backend schemas.py
 * All field names must remain snake_case to match API exactly.
 */
// ============================================================================
// Enums
// ============================================================================
export var AccountStatus;
(function (AccountStatus) {
    AccountStatus["DISCONNECTED"] = "disconnected";
    AccountStatus["WAITING_PHONE"] = "waiting_phone";
    AccountStatus["WAITING_CODE"] = "awaiting_code";
    AccountStatus["WAITING_PASSWORD"] = "awaiting_password";
    AccountStatus["CONNECTED"] = "connected";
})(AccountStatus || (AccountStatus = {}));
export var MediaStatus;
(function (MediaStatus) {
    MediaStatus["PENDING"] = "pending";
    MediaStatus["DOWNLOADING"] = "downloading";
    MediaStatus["DOWNLOADED"] = "downloaded";
    MediaStatus["FAILED"] = "failed";
    MediaStatus["PROCESSING"] = "processing";
    MediaStatus["READY"] = "ready";
})(MediaStatus || (MediaStatus = {}));
export var SubMode;
(function (SubMode) {
    SubMode["IMMEDIATE"] = "immediate";
    SubMode["SCHEDULED"] = "scheduled";
})(SubMode || (SubMode = {}));
export var FilterMode;
(function (FilterMode) {
    FilterMode["INCLUDE"] = "include";
    FilterMode["EXCLUDE"] = "exclude";
})(FilterMode || (FilterMode = {}));
export var JobStatus;
(function (JobStatus) {
    JobStatus["PENDING"] = "pending";
    JobStatus["DOWNLOADING"] = "downloading";
    JobStatus["COMPLETED"] = "completed";
    JobStatus["FAILED"] = "failed";
})(JobStatus || (JobStatus = {}));
export var EventLevel;
(function (EventLevel) {
    EventLevel["DEBUG"] = "debug";
    EventLevel["INFO"] = "info";
    EventLevel["WARNING"] = "warning";
    EventLevel["ERROR"] = "error";
})(EventLevel || (EventLevel = {}));
