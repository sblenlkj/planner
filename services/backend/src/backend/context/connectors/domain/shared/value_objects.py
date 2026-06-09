from enum import StrEnum


class ConnectorProvider(StrEnum):
    GMAIL = "gmail"
    YOUTUBE = "youtube"


class ConnectorConnectionStatus(StrEnum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    ERROR = "error"


class ConnectorJobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ConnectorJobType(StrEnum):
    POLL = "poll"
    SYNC = "sync"
    PROCESS_EVENT = "process_event"


class ConnectorEventStatus(StrEnum):
    RECEIVED = "received"
    DISPATCHED = "dispatched"
    IGNORED = "ignored"
    FAILED = "failed"


class ConnectorEventType(StrEnum):
    GMAIL_MESSAGE_RECEIVED = "gmail_message_received"
    YOUTUBE_VIDEO_DETECTED = "youtube_video_detected"
