from enum import StrEnum


class AnalyticsRecordStatus(StrEnum):
    ACTIVE = "active"
    REJECTED = "rejected"
    EXPIRED = "expired"
    SUPERSEDED = "superseded"