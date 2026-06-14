from __future__ import annotations

from typing import Protocol
from uuid import UUID

from backend.context.course.application.dto.course_read_models import (
    CourseDetails,
    CourseListItem,
    CourseTaskDetails,
)
from backend.context.course.domain.value_objects.course_status import CourseStatus
from backend.context.course.domain.value_objects.course_task_status import (
    CourseTaskStatus,
)


class CourseReadRepository(Protocol):
    async def list_courses(
        self,
        *,
        user_id: UUID,
        status: CourseStatus | None = None,
    ) -> list[CourseListItem]:
        raise NotImplementedError

    async def get_course(
        self,
        *,
        course_id: UUID,
        with_observations: bool = False,
        with_tasks: bool = True,
        task_status: CourseTaskStatus | None = None,
    ) -> CourseDetails | None:
        raise NotImplementedError

    async def get_course_task(
        self,
        *,
        task_id: UUID,
        with_observations: bool = False,
    ) -> CourseTaskDetails | None:
        raise NotImplementedError