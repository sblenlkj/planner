from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from ..value_objects import CommitmentStatus


@dataclass(kw_only=True, slots=True)
class Reminder:
    user_id: UUID
    remind_at: datetime
    title: str
    description: str | None = None
    status: CommitmentStatus = CommitmentStatus.ACTIVE
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        self._validate_utc_datetime(self.remind_at, field_name="remind_at")

        if not isinstance(self.status, CommitmentStatus):
            raise ValueError("status must be CommitmentStatus")

        self._validate_title(self.title)
        self.title = self.title.strip()

        if self.description is not None:
            self.description = self.description.strip()

    def cancel(self) -> None:
        self.status = CommitmentStatus.CANCELLED

    def reactivate(self) -> None:
        self.status = CommitmentStatus.ACTIVE

    def reschedule(self, remind_at: datetime) -> None:
        self._validate_utc_datetime(remind_at, field_name="remind_at")
        self.remind_at = remind_at

    def rename(self, title: str) -> None:
        self._validate_title(title)
        self.title = title.strip()

    def change_description(self, description: str | None) -> None:
        self.description = description.strip() if description is not None else None

    @staticmethod
    def _validate_title(title: str) -> None:
        if not title or not title.strip():
            raise ValueError("title is required")

    @staticmethod
    def _validate_utc_datetime(value: datetime, *, field_name: str) -> None:
        if not isinstance(value, datetime):
            raise ValueError(f"{field_name} must be datetime")

        if value.tzinfo is None:
            return

        if value.utcoffset() != UTC.utcoffset(value):
            raise ValueError(f"{field_name} must be UTC datetime or naive UTC datetime")