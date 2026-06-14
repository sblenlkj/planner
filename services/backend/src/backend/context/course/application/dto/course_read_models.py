from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from backend.context.course.domain.value_objects.course_status import CourseStatus
from backend.context.course.domain.value_objects.course_task_status import (
    CourseTaskStatus,
)


@dataclass(frozen=True, kw_only=True)
class CourseListItem:
    id: UUID
    user_id: UUID
    title: str
    description: str | None
    status: CourseStatus


@dataclass(frozen=True, kw_only=True)
class CourseObservationReadItem:
    id: UUID
    title: str
    description: str | None


@dataclass(frozen=True, kw_only=True)
class CourseTaskReadItem:
    id: UUID
    course_id: UUID
    title: str
    description: str | None
    priority: int
    status: CourseTaskStatus


@dataclass(frozen=True, kw_only=True)
class CourseDetails:
    id: UUID
    user_id: UUID
    title: str
    description: str | None
    status: CourseStatus
    observations: list[CourseObservationReadItem] | None = None
    tasks: list[CourseTaskReadItem] | None = None


@dataclass(frozen=True, kw_only=True)
class CourseTaskObservationReadItem:
    id: UUID
    title: str
    description: str | None


@dataclass(frozen=True, kw_only=True)
class CourseTaskDetails:
    id: UUID
    course_id: UUID
    title: str
    description: str | None
    priority: int
    status: CourseTaskStatus
    observations: list[CourseTaskObservationReadItem] | None = None