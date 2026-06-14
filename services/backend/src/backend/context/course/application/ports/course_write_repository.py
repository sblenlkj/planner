from __future__ import annotations

from typing import Protocol
from uuid import UUID

from backend.context.course.domain.entities.course import Course
from backend.context.course.domain.entities.course_observation import (
    CourseObservation,
)
from backend.context.course.domain.entities.course_task import CourseTask
from backend.context.course.domain.entities.course_task_observation import (
    CourseTaskObservation,
)


class CourseWriteRepository(Protocol):
    async def add_course(self, course: Course) -> None:
        raise NotImplementedError

    async def get_course_by_id(self, course_id: UUID) -> Course | None:
        raise NotImplementedError

    async def update_course(self, course: Course) -> None:
        raise NotImplementedError

    async def add_course_task(self, task: CourseTask) -> None:
        raise NotImplementedError

    async def get_course_task_by_id(
        self,
        task_id: UUID,
    ) -> CourseTask | None:
        raise NotImplementedError

    async def update_course_task(self, task: CourseTask) -> None:
        raise NotImplementedError

    async def add_course_observation(
        self,
        observation: CourseObservation,
    ) -> None:
        raise NotImplementedError

    async def get_course_observation_by_id(
        self,
        observation_id: UUID,
    ) -> CourseObservation | None:
        raise NotImplementedError

    async def update_course_observation(
        self,
        observation: CourseObservation,
    ) -> None:
        raise NotImplementedError

    async def add_course_task_observation(
        self,
        observation: CourseTaskObservation,
    ) -> None:
        raise NotImplementedError

    async def get_course_task_observation_by_id(
        self,
        observation_id: UUID,
    ) -> CourseTaskObservation | None:
        raise NotImplementedError

    async def update_course_task_observation(
        self,
        observation: CourseTaskObservation,
    ) -> None:
        raise NotImplementedError