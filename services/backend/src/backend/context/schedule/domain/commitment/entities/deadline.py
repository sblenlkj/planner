from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from ..value_objects import CommitmentStatus


@dataclass(kw_only=True, slots=True)
class Deadline:
    user_id: UUID
    due_at: datetime
    title: str
    description: str | None = None
    course_id: UUID | None = None
    course_task_id: UUID | None = None
    status: CommitmentStatus = CommitmentStatus.ACTIVE
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        self._validate_utc_datetime(self.due_at, field_name="due_at")

        if not isinstance(self.status, CommitmentStatus):
            raise ValueError("status must be CommitmentStatus")

        if self.course_task_id is not None and self.course_id is None:
            raise ValueError("course_id is required when course_task_id is set")

        self._validate_title(self.title)
        self.title = self.title.strip()

        if self.description is not None:
            self.description = self.description.strip()

    def cancel(self) -> None:
        self.status = CommitmentStatus.CANCELLED

    def reactivate(self) -> None:
        self.status = CommitmentStatus.ACTIVE

    def reschedule(self, due_at: datetime) -> None:
        self._validate_utc_datetime(due_at, field_name="due_at")
        self.due_at = due_at

    def link_course_task(self, course_id: UUID, course_task_id: UUID) -> None:
        self.course_id = course_id
        self.course_task_id = course_task_id

    def unlink_course_task(self) -> None:
        self.course_id = None
        self.course_task_id = None

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