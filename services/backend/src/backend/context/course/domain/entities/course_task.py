from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID, uuid4

from direttore import Validatable

from backend.context.course.domain.value_objects import (
    CourseTaskPriority,
    CourseTaskStatus,
    transition_course_task_status,
)


@dataclass(eq=False, kw_only=True)
class CourseTask(Validatable):
    id: UUID
    course_id: UUID
    title: str
    description: str | None = None
    priority: CourseTaskPriority
    status: CourseTaskStatus

    @classmethod
    def create(
        cls,
        *,
        course_id: UUID,
        title: str,
        description: str | None = None,
        priority: CourseTaskPriority | None = None,
        id: UUID | None = None,
    ) -> "CourseTask":
        return cls(
            id=id or uuid4(),
            course_id=course_id,
            title=cls._normalize_required_text(title, "Course task title"),
            description=cls._normalize_optional_text(description),
            priority=priority or CourseTaskPriority.normal(),
            status=CourseTaskStatus.PENDING,
        )

    def validate_invariants(self) -> Self:
        self._validate_required_text(self.title, "Course task title")
        return self

    def rename(self, title: str) -> None:
        self.title = self._normalize_required_text(title, "Course task title")

    def change_description(self, description: str | None) -> None:
        self.description = self._normalize_optional_text(description)

    def change_priority(self, priority: CourseTaskPriority) -> None:
        self.priority = priority

    def start(self) -> None:
        self.status = transition_course_task_status(
            current=self.status,
            target=CourseTaskStatus.IN_PROGRESS,
        )

    def skip(self) -> None:
        self.status = transition_course_task_status(
            current=self.status,
            target=CourseTaskStatus.SKIPPED,
        )

    def complete(self) -> None:
        self.status = transition_course_task_status(
            current=self.status,
            target=CourseTaskStatus.COMPLETED,
        )

    def reopen(self) -> None:
        self.status = transition_course_task_status(
            current=self.status,
            target=CourseTaskStatus.IN_PROGRESS,
        )

    @classmethod
    def _normalize_required_text(cls, value: str, field_name: str) -> str:
        value = value.strip()
        cls._validate_required_text(value, field_name)
        return value

    @staticmethod
    def _normalize_optional_text(value: str | None) -> str | None:
        if value is None:
            return None

        normalized = value.strip()
        return normalized or None

    @staticmethod
    def _validate_required_text(value: str, field_name: str) -> None:
        if not value:
            raise ValueError(f"{field_name} is required.")
